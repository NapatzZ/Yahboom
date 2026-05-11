import rclpy
import rclpy.time
import math
import os
import yaml

from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from nav2_msgs.action import NavigateToPose
from tf2_ros import Buffer, TransformListener
from ament_index_python.packages import get_package_share_directory

# Import custom services
from yahboom_interfaces.srv import SaveLocation, MoveDistance, RotateDegree, NavToLocation


class CommandServerNode(Node):
    def __init__(self):
        super().__init__('command_server')

        # Allow service callbacks to be re-entrant (needed for MultiThreadedExecutor)
        self.cb_group = ReentrantCallbackGroup()

        # ── Paths ──────────────────────────────────────────────────────────────
        try:
            self.share_dir = get_package_share_directory('yahboom_nav2')
            self.workspace_dir = os.path.abspath(
                os.path.join(self.share_dir, '..', '..', '..', '..'))
            self.save_path = os.path.join(
                self.workspace_dir, 'src', 'yahboom_nav2', 'maps', 'locations.yaml')
        except Exception:
            self.save_path = 'locations.yaml'

        # ── TF listener (for save_location) ────────────────────────────────────
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # ── Publishers ─────────────────────────────────────────────────────────
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # ── Odometry subscriber (for precision movement) ───────────────────────
        # Stores the latest odometry pose so callbacks can poll it
        self._odom_x: float = 0.0
        self._odom_y: float = 0.0
        self._odom_yaw: float = 0.0
        self.create_subscription(
            Odometry, '/odom', self._odom_callback, 10,
            callback_group=self.cb_group)

        # ── Action client (Nav2) ────────────────────────────────────────────────
        self.nav_to_pose_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose',
            callback_group=self.cb_group)

        # ── Services ───────────────────────────────────────────────────────────
        namespace = 'yahboom_esp32/nav'

        self.srv_save_location = self.create_service(
            SaveLocation,
            f'{namespace}/save_location',
            self.save_location_callback,
            callback_group=self.cb_group)

        self.srv_move_dist = self.create_service(
            MoveDistance,
            f'{namespace}/move_distance',
            self.move_distance_callback,
            callback_group=self.cb_group)

        self.srv_rotate_deg = self.create_service(
            RotateDegree,
            f'{namespace}/rotate_degree',
            self.rotate_degree_callback,
            callback_group=self.cb_group)

        self.srv_nav_loc = self.create_service(
            NavToLocation,
            f'{namespace}/nav_to_location',
            self.nav_to_location_callback,
            callback_group=self.cb_group)

        self.get_logger().info('Command Server Node is ready.')
        self.get_logger().info(f'Locations will be saved to: {self.save_path}')

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _odom_callback(self, msg: Odometry):
        """Cache latest odometry position and yaw."""
        self._odom_x = msg.pose.pose.position.x
        self._odom_y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self._odom_yaw = math.atan2(siny_cosp, cosy_cosp)

    @staticmethod
    def _angle_diff(a: float, b: float) -> float:
        """Smallest signed difference between two angles (radians)."""
        d = a - b
        while d > math.pi:
            d -= 2.0 * math.pi
        while d < -math.pi:
            d += 2.0 * math.pi
        return d

    # ── Service callbacks ──────────────────────────────────────────────────────

    def save_location_callback(self, request, response):
        location_name = request.location_name
        if not location_name:
            response.success = False
            response.message = 'Location name cannot be empty.'
            return response

        try:
            trans = self.tf_buffer.lookup_transform(
                'map', 'base_footprint', rclpy.time.Time())

            x = trans.transform.translation.x
            y = trans.transform.translation.y
            q = trans.transform.rotation
            siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
            yaw = math.atan2(siny_cosp, cosy_cosp)

            location_data = {
                location_name: {
                    'x': float(x),
                    'y': float(y),
                    'yaw': float(yaw),
                }
            }

            # Read existing locations if file exists
            locations: dict = {}
            if os.path.exists(self.save_path):
                with open(self.save_path, 'r') as f:
                    try:
                        loaded = yaml.safe_load(f)
                        if isinstance(loaded, dict):
                            locations = loaded
                    except yaml.YAMLError:
                        pass

            locations.update(location_data)
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            with open(self.save_path, 'w') as f:
                yaml.dump(locations, f, default_flow_style=False)

            response.success = True
            response.message = (
                f"Saved '{location_name}' → X:{x:.3f} Y:{y:.3f} Yaw:{math.degrees(yaw):.1f}°")
            self.get_logger().info(response.message)

        except Exception as e:
            response.success = False
            response.message = f'Failed to get transform or save: {e}'
            self.get_logger().error(response.message)

        return response

    def move_distance_callback(self, request, response):
        """
        Precision linear movement using odometry feedback.

        Instead of time.sleep(), we spin an inner loop that publishes
        cmd_vel and checks the distance travelled against the odom position
        that was captured at the start of the call.  This keeps accuracy
        regardless of battery voltage / floor surface.
        """
        distance = float(request.distance)
        if distance == 0.0:
            response.success = True
            response.message = 'Distance is 0 – no movement required.'
            return response

        MAX_SPEED = 0.20        # m/s
        SLOW_ZONE = 0.05        # start slowing down when within 5 cm of target
        MIN_SPEED = 0.06        # m/s – minimum to keep wheels turning
        RATE_HZ   = 20.0        # control loop frequency
        TIMEOUT   = abs(distance) / MIN_SPEED + 5.0   # generous timeout

        direction = 1.0 if distance > 0 else -1.0
        start_x, start_y = self._odom_x, self._odom_y
        travelled = 0.0

        twist = Twist()
        rate = self.create_rate(RATE_HZ)
        deadline = self.get_clock().now().nanoseconds * 1e-9 + TIMEOUT

        self.get_logger().info(
            f'Moving {distance:.3f} m (odom-based, max {MAX_SPEED} m/s)')

        while rclpy.ok():
            travelled = math.sqrt(
                (self._odom_x - start_x) ** 2 +
                (self._odom_y - start_y) ** 2)

            remaining = abs(distance) - travelled
            if remaining <= 0.0:
                break

            # Proportional slow-down in the final SLOW_ZONE
            if remaining < SLOW_ZONE:
                speed = MIN_SPEED + (MAX_SPEED - MIN_SPEED) * (remaining / SLOW_ZONE)
            else:
                speed = MAX_SPEED

            twist.linear.x = direction * speed
            self.cmd_vel_pub.publish(twist)

            if self.get_clock().now().nanoseconds * 1e-9 > deadline:
                self.get_logger().warn('move_distance timed out before reaching target.')
                break

            rate.sleep()

        # Stop
        self.cmd_vel_pub.publish(Twist())

        response.success = True
        response.message = (
            f'Moved {travelled:.3f} m (target {distance:.3f} m).')
        self.get_logger().info(response.message)
        return response

    def rotate_degree_callback(self, request, response):
        """
        Precision rotation using odometry feedback.

        Tracks accumulated yaw from the cached odom to avoid time-based error.
        """
        degrees = float(request.degrees)
        if degrees == 0.0:
            response.success = True
            response.message = 'Degrees is 0 – no rotation required.'
            return response

        target_rad = math.radians(degrees)
        MAX_SPEED  = 0.50       # rad/s
        SLOW_ZONE  = math.radians(10.0)   # slow down in last 10 °
        MIN_SPEED  = 0.15       # rad/s
        RATE_HZ    = 20.0
        TIMEOUT    = abs(target_rad) / MIN_SPEED + 5.0

        direction = 1.0 if target_rad > 0 else -1.0
        start_yaw = self._odom_yaw
        accumulated = 0.0
        prev_yaw = start_yaw

        twist = Twist()
        rate = self.create_rate(RATE_HZ)
        deadline = self.get_clock().now().nanoseconds * 1e-9 + TIMEOUT

        self.get_logger().info(
            f'Rotating {degrees:.1f}° (odom-based, max {MAX_SPEED} rad/s)')

        while rclpy.ok():
            delta = self._angle_diff(self._odom_yaw, prev_yaw)
            accumulated += delta
            prev_yaw = self._odom_yaw

            remaining = abs(target_rad) - abs(accumulated)
            if remaining <= 0.0:
                break

            if remaining < SLOW_ZONE:
                speed = MIN_SPEED + (MAX_SPEED - MIN_SPEED) * (remaining / SLOW_ZONE)
            else:
                speed = MAX_SPEED

            twist.angular.z = direction * speed
            self.cmd_vel_pub.publish(twist)

            if self.get_clock().now().nanoseconds * 1e-9 > deadline:
                self.get_logger().warn('rotate_degree timed out before reaching target.')
                break

            rate.sleep()

        # Stop
        self.cmd_vel_pub.publish(Twist())

        response.success = True
        response.message = (
            f'Rotated {math.degrees(accumulated):.1f}° '
            f'(target {degrees:.1f}°).')
        self.get_logger().info(response.message)
        return response

    def nav_to_location_callback(self, request, response):
        """Send a Nav2 NavigateToPose goal to a previously saved location."""
        location_name = request.location_name
        if not location_name:
            response.success = False
            response.message = 'Location name cannot be empty.'
            return response

        # Load saved locations
        if not os.path.exists(self.save_path):
            response.success = False
            response.message = f"Locations file not found: '{self.save_path}'"
            return response

        try:
            with open(self.save_path, 'r') as f:
                locations = yaml.safe_load(f)
        except Exception as e:
            response.success = False
            response.message = f'Failed to read locations file: {e}'
            return response

        if not isinstance(locations, dict) or location_name not in locations:
            response.success = False
            response.message = f"Location '{location_name}' not found in saved locations."
            return response

        loc = locations[location_name]
        x   = float(loc['x'])
        y   = float(loc['y'])
        yaw = float(loc['yaw'])

        if not self.nav_to_pose_client.wait_for_server(timeout_sec=5.0):
            response.success = False
            response.message = 'Nav2 action server is not available (timeout 5 s).'
            return response

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp    = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        # Convert yaw → quaternion (rotation about Z)
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)

        # Fire-and-forget: send goal and return immediately so the service
        # doesn't block other callbacks while Nav2 is executing.
        self.nav_to_pose_client.send_goal_async(goal_msg)

        response.success = True
        response.message = (
            f"Navigation to '{location_name}' started "
            f"(X:{x:.2f} Y:{y:.2f} Yaw:{math.degrees(yaw):.1f}°).")
        self.get_logger().info(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = CommandServerNode()

    # MultiThreadedExecutor is required so that the odom subscriber can
    # update _odom_x / _odom_y while a service callback is spinning its
    # inner control loop.
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

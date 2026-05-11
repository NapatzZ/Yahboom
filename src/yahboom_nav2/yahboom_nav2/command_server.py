import rclpy
from rclpy.node import Node
import yaml
import os
import math
import time
from geometry_msgs.msg import Twist
from tf2_ros import Buffer, TransformListener
from ament_index_python.packages import get_package_share_directory

# Import custom services
from yahboom_interfaces.srv import SaveLocation, MoveDistance, RotateDegree

class CommandServerNode(Node):
    def __init__(self):
        super().__init__('command_server')
        
        # Determine paths
        try:
            self.share_dir = get_package_share_directory('yahboom_nav2')
            self.workspace_dir = os.path.abspath(os.path.join(self.share_dir, '..', '..', '..', '..'))
            self.save_path = os.path.join(self.workspace_dir, 'src', 'yahboom_nav2', 'maps', 'locations.yaml')
        except Exception:
            self.save_path = 'locations.yaml'
            
        # Initialize TF listener for location saving
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Initialize publisher for movement
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Initialize Action Client for Navigation
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # Define namespace for services
        namespace = 'yahboom_esp32/nav'
        
        # Create Services
        self.srv_save_location = self.create_service(
            SaveLocation, 
            f'{namespace}/save_location', 
            self.save_location_callback
        )
        self.srv_move_dist = self.create_service(
            MoveDistance, 
            f'{namespace}/move_distance', 
            self.move_distance_callback
        )
        self.srv_rotate_deg = self.create_service(
            RotateDegree, 
            f'{namespace}/rotate_degree', 
            self.rotate_degree_callback
        )
        self.srv_nav_loc = self.create_service(
            NavToLocation, 
            f'{namespace}/nav_to_location', 
            self.nav_to_location_callback
        )
        
        self.get_logger().info('Command Server Node is ready.')
        self.get_logger().info(f'Locations will be saved to: {self.save_path}')

    def save_location_callback(self, request, response):
        location_name = request.location_name
        if not location_name:
            response.success = False
            response.message = "Location name cannot be empty."
            return response
            
        try:
            # Wait for TF map -> base_footprint
            trans = self.tf_buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())
            
            x = trans.transform.translation.x
            y = trans.transform.translation.y
            
            # Simple quaternion to yaw (assuming flat 2D plane)
            q = trans.transform.rotation
            siny_cosp = 2 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
            yaw = math.atan2(siny_cosp, cosy_cosp)
            
            location_data = {
                location_name: {
                    'x': float(x),
                    'y': float(y),
                    'yaw': float(yaw)
                }
            }
            
            # Read existing locations if file exists
            locations = {}
            if os.path.exists(self.save_path):
                with open(self.save_path, 'r') as f:
                    try:
                        locations = yaml.safe_load(f)
                        if not isinstance(locations, dict):
                            locations = {}
                    except yaml.YAMLError:
                        pass
                        
            # Update and save
            locations.update(location_data)
            
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            with open(self.save_path, 'w') as f:
                yaml.dump(locations, f, default_flow_style=False)
                
            response.success = True
            response.message = f"Successfully saved location '{location_name}' at X: {x:.2f}, Y: {y:.2f}, Yaw: {yaw:.2f}"
            self.get_logger().info(response.message)
            
        except Exception as e:
            response.success = False
            response.message = f"Failed to get transform or save: {str(e)}"
            self.get_logger().error(response.message)
            
        return response

    def move_distance_callback(self, request, response):
        distance = request.distance
        if distance == 0:
            response.success = True
            response.message = "Distance is 0, no movement required."
            return response
            
        speed = 0.2  # m/s
        if distance < 0:
            speed = -speed
            
        duration = abs(distance / speed)
        
        twist = Twist()
        twist.linear.x = speed
        
        self.get_logger().info(f"Moving {distance} meters (speed: {speed} m/s, duration: {duration:.2f}s)")
        
        # Start moving
        self.cmd_vel_pub.publish(twist)
        
        # Wait
        time.sleep(duration)
        
        # Stop
        twist.linear.x = 0.0
        self.cmd_vel_pub.publish(twist)
        
        response.success = True
        response.message = f"Successfully moved {distance} meters."
        return response

    def rotate_degree_callback(self, request, response):
        degrees = request.degrees
        if degrees == 0:
            response.success = True
            response.message = "Degrees is 0, no rotation required."
            return response
            
        radians = math.radians(degrees)
        angular_speed = 0.5  # rad/s
        
        if radians < 0:
            angular_speed = -angular_speed
            
        duration = abs(radians / angular_speed)
        
        twist = Twist()
        twist.angular.z = angular_speed
        
        self.get_logger().info(f"Rotating {degrees} degrees (speed: {angular_speed} rad/s, duration: {duration:.2f}s)")
        
        # Start rotating
        self.cmd_vel_pub.publish(twist)
        
        # Wait
        time.sleep(duration)
        
        # Stop
        twist.angular.z = 0.0
        self.cmd_vel_pub.publish(twist)
        
        response.success = True
        response.message = f"Successfully rotated {degrees} degrees."
        return response

def main(args=None):
    rclpy.init(args=args)
    node = CommandServerNode()
    
    try:
        # Use MultiThreadedExecutor if services might be called simultaneously or need to run while waiting
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
      
        loc = locations[location_name]
        x, y, yaw = float(loc['x']), float(loc['y']), float(loc['yaw'])
        
        if not self.nav_to_pose_client.wait_for_server(timeout_sec=2.0):
            response.success = False
            response.message = "Nav2 action server is not running."
            return response
            
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)
        
        self.nav_to_pose_client.send_goal_async(goal_msg)
        
        response.success = True
        response.message = f"Navigation to '{location_name}' started."
        self.get_logger().info(response.message)
        return response

def main(args=None):
    rclpy.init(args=args)
    node = CommandServerNode()
    
    try:
        # Use MultiThreadedExecutor if services might be called simultaneously or need to run while waiting
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

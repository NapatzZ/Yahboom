import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from tf_transformations import quaternion_from_euler

class YAHBOOM_NAV2(Node):
    def __init__(self, name):
        super().__init__(name)
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

    def send_goal(self, x, y, yaw):
        self.get_logger().info('Waiting for action server...')
        self._action_client.wait_for_server()

        # 2. Create the goal message
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

        # Position
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y

        quaternion = quaternion_from_euler(0, 0, yaw)
        
        goal_msg.pose.pose.orientation.x = quaternion[0] 
        goal_msg.pose.pose.orientation.y = quaternion[1] 
        goal_msg.pose.pose.orientation.z = quaternion[2] 
        goal_msg.pose.pose.orientation.w = quaternion[3]

        self.get_logger().info(f'Sending goal to: x={x}, y={y}, yaw={yaw}...')

        # 3. Send the goal
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg, 
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected!')
            return

        self.get_logger().info('Goal accepted')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        status = future.result().status
        self.get_logger().info(f'Navigation finished with status: {status}')

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f'Distance remaining: {feedback.distance_remaining:.2f} m')

def main(args=None):
    rclpy.init(args=args)
    yahboom_nav2 = YAHBOOM_NAV2(name = 'yahboom_nav2')
    
    yahboom_nav2.send_goal(x = 1.0, y = 0.0, yaw = 1.0)
    
    rclpy.spin(yahboom_nav2)

if __name__ == '__main__':
    main()
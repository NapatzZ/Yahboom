import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

class ImuFilterNode(Node):
    def __init__(self):
        super().__init__('imu_filter_node')
        
        # Subscriber to original IMU topic
        self.subscription = self.create_subscription(
            Imu,
            '/imu/data',
            self.imu_callback,
            10
        )
        
        # Publisher for the filtered IMU topic
        self.publisher = self.create_publisher(Imu, '/imu/data_filtered', 10)
        
        self.get_logger().info('IMU Filter Node has been started. Filtering linear_acceleration.z == 0.0')

    def imu_callback(self, msg):
        # Check if linear_acceleration.z is exactly 0.0 (or extremely close due to floating point)
        if abs(msg.linear_acceleration.z) < 1e-5:
            # Drop the message by simply returning
            self.get_logger().debug('Dropped IMU message: linear_acceleration.z is ~0.0')
            return
            
        # If the data is good, publish it to the new topic
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ImuFilterNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

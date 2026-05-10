import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rf2o_laser_odometry',
            executable='rf2o_laser_odometry_node',
            name='rf2o_laser_odometry',
            output='screen',
            parameters=[{
                'laser_scan_topic': '/scan',
                'odom_topic': '/laser_odom',
                'publish_tf': False, # EKF will handle TF
                'base_frame_id': 'base_footprint',
                'odom_frame_id': 'odom',
                'freq': 10.0,
                'qos_reliability': 1 # 1 = RELIABLE, to match YB_Car_Node
            }],
        ),
    ])

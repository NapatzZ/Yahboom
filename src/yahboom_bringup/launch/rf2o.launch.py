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
                'publish_tf': False,         # EKF handles odom → base_footprint TF
                'base_frame_id': 'base_footprint',
                'odom_frame_id': 'odom',
                # BUG-06 FIX: raised from 10.0 → 20.0 Hz.
                # EKF runs at 30 Hz; a larger ratio means more predict-only cycles
                # with no measurement update, which increases pose drift.
                # 20 Hz gives a 1.5:1 ratio which is a reasonable balance.
                # Note: rf2o cannot exceed the LiDAR's own scan rate.
                'freq': 20.0,
                'qos_reliability': 1,        # 1 = RELIABLE, matches YB_Car_Node
                'init_pose_from_topic': ''   # skip waiting for ground truth pose on real robot
            }],
        ),
    ])

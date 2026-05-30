import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    yahboom_nav2_dir = get_package_share_directory('yahboom_nav2')
    description_dir = get_package_share_directory('yahboomcar_description')

    return LaunchDescription([
        # Robot URDF + TF tree (base_link, wheels, laser_frame, etc.)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(description_dir, 'launch', 'description_launch.py')
            )
        ),

        # Fake wheel odometry: odom → base_footprint (robot sitting at origin)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='fake_odom_tf',
            arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_footprint'],
        ),

        # Fake AMCL output: map → odom (keeps planners alive without /scan)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='fake_map_tf',
            arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
        ),

        # Nav2 stack + RViz (navigate.launch.py with use_rviz:=True default)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(yahboom_nav2_dir, 'launch', 'navigate.launch.py')
            )
        ),
    ])

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    yahboom_nav2_dir = get_package_share_directory('yahboom_nav2')

    use_composition = LaunchConfiguration('use_composition', default='False')

    # Nav2 stack: AMCL localization + planners + controllers
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(yahboom_nav2_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': os.path.join(yahboom_nav2_dir, 'maps', 'map.yaml'),
            'use_composition': use_composition,
        }.items(),
    )

    # Command server for high-level navigation requests
    command_server_node = Node(
        package='yahboom_nav2',
        executable='command_server',
        name='command_server',
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_composition', default_value='False'),
        navigation_launch,      # 1. Nav2 stack      (AMCL + planners)
        command_server_node,    # 2. high-level command interface
        # Visualization: use Foxglove Studio — ws://localhost:8765
    ])
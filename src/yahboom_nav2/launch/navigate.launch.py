import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    yahboom_nav2_dir = get_package_share_directory('yahboom_nav2')

    use_composition = LaunchConfiguration('use_composition', default='False')
    use_rviz = LaunchConfiguration('use_rviz', default='True')

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(yahboom_nav2_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': os.path.join(yahboom_nav2_dir, 'maps', 'map.yaml'),
            'use_composition': use_composition,
        }.items(),
    )

    command_server_node = Node(
        package='yahboom_nav2',
        executable='command_server',
        name='command_server',
        output='screen'
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(yahboom_nav2_dir, 'config', 'nav2.rviz')],
        output='screen',
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_composition', default_value='False'),
        DeclareLaunchArgument('use_rviz', default_value='True',
                              description='Launch RViz with nav2 config'),
        navigation_launch,
        command_server_node,
        rviz_node,
    ])

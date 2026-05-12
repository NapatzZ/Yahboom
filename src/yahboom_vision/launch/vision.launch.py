from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='yahboom_vision',
            executable='image_proc',
            name='image_proc',
            output='screen',
        ),
        Node(
            package='yahboom_vision',
            executable='human_detection',
            name='human_detection_node',
            output='screen',
        ),
    ])

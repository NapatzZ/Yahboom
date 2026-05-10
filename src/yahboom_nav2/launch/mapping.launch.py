import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    yahboom_nav2_dir = get_package_share_directory('yahboom_nav2')
    nav2_dir = get_package_share_directory('nav2_bringup')

    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(yahboom_nav2_dir, 'launch', 'navigation_launch.py')
        ),
    )

    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_dir, 'launch', 'rviz_launch.py')
        )
    )

    online_async_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(yahboom_nav2_dir, 'launch', 'online_async_launch.py')
        )
    )

    return LaunchDescription([
        navigation_launch,
        rviz_launch,
        online_async_launch
    ])
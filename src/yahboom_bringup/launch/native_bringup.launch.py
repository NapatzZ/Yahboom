import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Directories
    yahboom_bringup_dir = get_package_share_directory('yahboom_bringup')
    description_dir = get_package_share_directory('yahboomcar_description')
    
    # Configurations
    ekf_config_path = os.path.join(yahboom_bringup_dir, 'config', 'ekf.yaml')

    # Launch Arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    # Robot Description (Robot State Publisher)
    description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(description_dir, 'launch', 'description_launch.py')
        )
    )

    # EKF (Robot Localization) for Odom + IMU Fusion
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config_path, {'use_sim_time': use_sim_time}]
    )

    # Laser Odometry (rf2o)
    rf2o_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(yahboom_bringup_dir, 'launch', 'rf2o.launch.py')
        )
    )

    # IMU Filter Node
    imu_filter_node = Node(
        package='yahboom_bringup',
        executable='imu_filter_node',
        name='imu_filter_node',
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        description_launch,
        imu_filter_node,
        ekf_node,
        rf2o_launch
    ])

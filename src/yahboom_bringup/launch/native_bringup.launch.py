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

    # IMU Filter Node — pre-processes raw IMU before EKF
    # Subscribes: /imu/data_raw  ->  Publishes: /imu/data_filtered
    imu_filter_node = Node(
        package='yahboom_bringup',
        executable='imu_filter_node',
        name='imu_filter_node',
        output='screen'
    )

    # Laser Odometry (rf2o) — estimates velocity from consecutive LiDAR scans
    # Subscribes: /scan  ->  Publishes: /laser_odom
    rf2o_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(yahboom_bringup_dir, 'launch', 'rf2o.launch.py')
        )
    )

    # EKF (Robot Localization) — fuses /odom_raw + /laser_odom + /imu/data_filtered
    # Publishes: /odom  and  odom -> base_footprint TF
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config_path, {'use_sim_time': use_sim_time}]
    )



    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        description_launch,     # 1. robot URDF / TF tree
        rf2o_launch,            # 2. laser odometry (/laser_odom)
        imu_filter_node,        # 3. IMU pre-processing
        ekf_node,               # 4. sensor fusion  — publishes /odom
    ])

# Yahboom ROS 2 Project

ROS 2 project for Yahboom robots.

## Installation (Build)

```bash
# Clone the repository with submodules
git clone --recursive https://github.com/NapatzZ/Yahboom.git

# Install dependencies (Optional but recommended)
rosdep update && rosdep install --from-paths src --ignore-src -y

# Compile project
colcon build --symlink-install
source install/setup.bash

```

## How to Run (Execution)

### 1. Micro-ROS Agent
The robot communicates with the computer via Micro-ROS.

**Option A: Docker (Recommended)**

*   **WIFI-UDP:**
    ```bash
    docker run -it --rm -v /dev:/dev -v /dev/shm:/dev/shm --privileged --net=host microros/micro-ros-agent:humble udp4 --port 8090 -v4
    ```
*   **USB Serial:**
    ```bash
    docker run -it --rm -v /dev:/dev -v /dev/shm:/dev/shm --privileged --net=host microros/micro-ros-agent:humble serial --dev /dev/ttyUSB0 -b 921600 -v4
    ```

**Option B: Native Built-in Agent**

*   **WIFI-UDP:**
    ```bash
    ros2 run micro_ros_agent micro_ros_agent udp4 --port 8090
    ```
*   **USB Serial:**
    ```bash
    ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -b 921600
    ```
### 2. Bringup 
Run this command to start sensors and robot description:
```bash
ros2 launch yahboom_bringup native_bringup.launch.py
```

### 3. Mapping (SLAM)
Run navigation using a saved map:
```bash
ros2 launch yahboom_nav2 navigate.launch.py
```

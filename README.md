# Yahboom ROS 2 Project

ROS 2 project for Yahboom robots.

## Installation (Build)

```bash
# Clone the repository with submodules
git clone --recursive https://github.com/NapatzZ/Yahboom.git
# Or if already cloned:
git submodule update --init --recursive

# Install dependencies (Optional but recommended)
rosdep update && rosdep install --from-paths src --ignore-src -y

# Compile project
colcon build --symlink-install
source install/setup.bash

# Build Micro-ROS Agent (If not using Docker)
ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh
```

## How to Run (Execution)

### 1. Bringup (Basic Operations)
Run this command to start sensors and robot description:
```bash
ros2 launch yahboom_bringup native_bringup.launch.py
```

### 2. Micro-ROS Agent
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

### 3. Mapping (SLAM)
Run navigation using a saved map:
```bash
ros2 launch yahboom_nav2 navigate.launch.py
```

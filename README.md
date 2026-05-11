# Yahboom ROS 2 Project 
![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![ESP32](https://img.shields.io/badge/ESP32-green)

ROS 2 project for Yahboom ESP32 robots, including Micro-ROS, SLAM, and Navigation.
<div align="center">
<img src = "asset/MicroROS_Car_Yahboom.png" width="200" height="200">  
</div>

## Requirements

### Hardware
*   **Yahboom Robot**: Yahboom ESP32.
*   **LiDAR**: for SLAM and Navigation.
*   **Computer**: Ubuntu 22.04 recommended.
*   **Docker**: for run micro-ros connection

### Software
*   **OS**: Ubuntu 22.04 (Jammy Jellyfish)
*   **ROS 2**: Humble Hawksbill
*   **Docker**: For running Micro-ROS agent (optional if using native).
*   **Python Libraries**:
    ```bash
    pip install -r requirements.txt
    ```
*   **ROS 2 Packages**:
    Install essential packages:
    ```bash
    sudo apt update
    sudo apt install ros-humble-robot-localization \
                     ros-humble-slam-toolbox \
                     ros-humble-navigation2 \
                     ros-humble-nav2-bringup \
                     ros-humble-rmw-cyclonedds-cpp
    ```

## 1. Installation & Setup

### Clone and Build
```bash
# Clone with submodules
git clone --recursive https://github.com/NapatzZ/Yahboom.git

# Install dependencies
cd Yahboom
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# Build
colcon build 
source install/setup.bash
```

### Environment Setup (Bashrc)
To set up your terminal with the correct ROS_DOMAIN_ID (20), IP display, and workspace sourcing:
```bash
chmod +x src/script/update_bashrc.sh
./src/script/update_bashrc.sh
source ~/.bashrc
```

### Build Micro-ROS Agent (Native)
```bash
ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh
source install/setup.bash
```

---

## 2. Robot Configuration (WiFi & IP)

The robot must be configured to connect to your local network and point to your computer's IP address (Micro-ROS Agent).

This process is highly automated. The configuration script will **automatically detect** your currently active WiFi connection (SSID & Password) via `nmcli` and your computer's local IP address.

1. Connect the robot via USB.
2. Run the configuration script:
   ```bash
   python3 src/script/robot_config.py
   ```
3. Reboot the robot.

**Fallback Configuration (If Auto-Detect Fails)**
If you are not running Ubuntu, or if `nmcli` fails to retrieve the password, the script will use fallback credentials. To edit the fallback settings:
1. Open `src/script/robot_config.py`.
2. Locate the `if __name__ == '__main__':` block at the bottom of the file.
3. Modify the fallback line with your manual credentials:
   ```python
   print("Warning: Could not auto-detect WiFi. Using fallback values.")
   robot.set_wifi_config("YOUR_SSID", "YOUR_PASSWORD")
   ```
4. Rerun the script and reboot the robot.

---


## 3. Execution Workflow

### Step 1: Micro-ROS Agent
Connect the robot and start the communication bridge.

**Option A: Docker (Recommended)**
```bash
# WIFI-UDP
docker run -it --rm -v /dev:/dev -v /dev/shm:/dev/shm --privileged --net=host microros/micro-ros-agent:humble udp4 --port 8090 -v4

# USB Serial
docker run -it --rm -v /dev:/dev -v /dev/shm:/dev/shm --privileged --net=host microros/micro-ros-agent:humble serial --dev /dev/ttyUSB0 -b 921600 -v4
```

**Option B: Native**
```bash
ros2 run micro_ros_agent micro_ros_agent udp4 --port 8090
```

### Step 2: Bringup
Start sensors and robot state:
```bash
ros2 launch yahboom_bringup native_bringup.launch.py
```

### Step 3: SLAM (Mapping)
To create a new map:
```bash
# Start Mapping
ros2 launch yahboom_nav2 mapping.launch.py

# Control the robot to explore (using teleop in another terminal)
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### Step 4: Save Map
Once the map is complete, save it to the fixed path (`src/yahboom_nav2/maps/`):
```bash
ros2 run yahboom_nav2 map_saver
```

### Step 5: Navigation
Run navigation using the saved map:
```bash
ros2 launch yahboom_nav2 navigate.launch.py
```

---



# Yahboom ROS 2 Project 
![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)

ROS 2 project for Yahboom robots, including Micro-ROS, SLAM, and Navigation.

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
colcon build --symlink-install
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

## 2. Execution Workflow

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

## 3. Robot Configuration (WiFi & IP)

To fetch new WiFi settings or update the Agent IP on the robot hardware:

1. Connect the robot via USB.
2. Open `src/script/robot_config.py`.
3. Modify the `if __name__ == '__main__':` block with your new settings:
   ```python
   robot.set_wifi_config("YOUR_SSID", "YOUR_PASSWORD")
   robot.set_udp_config([192, 168, 1, 100], 8090) # Your Computer IP
   ```
4. Run the configuration script:
   ```bash
   python3 src/script/robot_config.py
   ```
5. Reboot the robot.

---


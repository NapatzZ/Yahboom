# Yahboom ROS 2 Project

ROS 2 project for Yahboom robots.

## Installation (Build)

```bash
# Compile project
colcon build --symlink-install

# Source workspace
source install/setup.bash
```

## How to Run (Execution)

### 1. Bringup (Basic Operations)
Run this command to start sensors and robot description:
```bash
ros2 launch yahboom_bringup native_bringup.launch.py
```

### 2. Mapping (SLAM)
Start the mapping process:
```bash
ros2 launch yahboom_nav2 mapping.launch.py
```

### 3. Save Map
Save the generated map to the default path:
```bash
ros2 run yahboom_nav2 map_saver
```

### 4. Micro-ROS Agent
The robot communicates with the computer via Micro-ROS. You need to start the agent:

**For WIFI-UDP (Standard):**
```bash
# Using script
./src/script/start_agent_computer.sh

# Or using Docker directly
docker run -it --rm --net=host microros/micro-ros-agent:humble udp4 --port 8090
```

**For Serial (USB):**
```bash
docker run -it --rm --privileged -v /dev:/dev microros/micro-ros-agent:humble serial --dev /dev/ttyUSB0 -b 921600
```

## Robot Configuration (Flash/Setup)

To configure the robot's Wi-Fi, IP, or PID parameters, use the `robot_config.py` script:

1. Connect the robot to your computer via USB.
2. Edit the configuration in `src/script/robot_config.py` (inside the `if __name__ == '__main__':` block).
3. Run the script:
```bash
python3 src/script/robot_config.py
```

### 5. Navigation
Run navigation using a saved map:
```bash
ros2 launch yahboom_nav2 navigate.launch.py
```

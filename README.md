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

## 1. Installation & Setup

### Option 1: Docker Environment (Recommended)
We provide a fully containerized environment that includes all dependencies, ROS 2, and the pre-built workspace.

**1. Build the Docker Image:**
```bash
docker build -t yahboom_ros2_workspace .
```

**2. Run the Container (with GUI & USB support):**
```bash
xhost +
docker run -it --rm \
  --name yahboom_nav_container \
  --net=host \
  --privileged \
  -v /dev:/dev \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  yahboom_ros2_workspace bash
```
*Note: The container uses the custom `bashrc_template` and automatically sources the workspace.*

### Option 2: Native Setup (Clone and Build)

### Environment Setup 
**Python Libraries**:

```bash
pip install -r requirements.txt
```
**ROS 2 Packages**:
    
Install essential packages:
    
```bash
sudo apt update
sudo apt install ros-humble-robot-localization \
     ros-humble-slam-toolbox \
     ros-humble-navigation2 \
     ros-humble-nav2-bringup \
     ros-humble-rmw-cyclonedds-cpp
```

**Clone Project**:

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

### Bashrc setup
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

## 4. Navigation Interfaces

When running the navigation stack (`navigate.launch.py`), a custom command server is automatically started. You can interact with the robot using the following ROS 2 services under the `yahboom_esp32/nav/` namespace.

### 4.1 Save Current Location
Saves the robot's current position (X, Y, Yaw) from the `map` to `base_footprint` TF into `src/yahboom_nav2/maps/locations.yaml`.
```bash
ros2 service call /yahboom_esp32/nav/save_location yahboom_interfaces/srv/SaveLocation "{location_name: 'point_a'}"
```

### 4.2 Move Distance (Manual)
Commands the robot to move straight by a specific distance (in meters) directly via `/cmd_vel`. Positive for forward, negative for backward.
```bash
ros2 service call /yahboom_esp32/nav/move_distance yahboom_interfaces/srv/MoveDistance "{distance: 1.0}"
```

### 4.3 Rotate Degree (Manual)
Commands the robot to rotate in place by a specific degree directly via `/cmd_vel`. Positive for Counter-Clockwise (left), negative for Clockwise (right).
```bash
ros2 service call /yahboom_esp32/nav/rotate_degree yahboom_interfaces/srv/RotateDegree "{degrees: 90.0}"
```

### 4.4 Navigate to Saved Location
Commands the robot to autonomously navigate to a previously saved location using the Nav2 stack. The location name must exist in `locations.yaml`.
```bash
ros2 service call /yahboom_esp32/nav/nav_to_location yahboom_interfaces/srv/NavToLocation "{location_name: 'point_a'}"
```

---

## 5. Vision & Human Detection

The `yahboom_vision` package provides camera image processing and MediaPipe-based human detection.

### Architecture Overview

```
ESP32-CAM (WiFi)
      │
      │  Micro-ROS UDP (port 9999)          TCP (port 8888)
      │  → publishes /espRos/esp32camera    ← set_camera.py (flip/mirror config)
      │
      ▼
 [start_camera_computer.sh]  ← Micro-ROS Agent (must run first)
      │
      ▼
 image_proc node
      │  /yahboom/vision/camera/image_raw  (Image)
      │  /yahboom/vision/camera/debug      (Image, annotated)
      ▼
 human_detection node  ◄──── Service call from any node / terminal
      │
      └── /yahboom_esp32/vision/human_detection  →  bool detected
```

> [!IMPORTANT]
> The camera ESP32 uses **port 9999** (Micro-ROS Agent).
> The robot body ESP32 uses **port 8090** (separate agent).
> Both must be running for full functionality.

---

### Step 0 (First-time only): Configure Camera Orientation

If the image appears flipped or mirrored, run this once to correct it:

```bash
python3 src/script/set_camera.py
# Enter the Docker container's IPv4 address when prompted
```

This connects to the ESP32-CAM via TCP (port 8888) and applies vflip/mirror settings. **Only needed once** during initial setup or if the image orientation is wrong.

To change the orientation, edit `set_camera.py`:
```python
set_Camera(True, True)   # Flip vertically + mirror horizontally
# set_Camera(False, False) # No flip, no mirror
```

---

### Step 1: Start the Camera Micro-ROS Agent

The camera ESP32 communicates via its **own Micro-ROS Agent on port 9999**.
This must be running before any image data appears.

```bash
bash src/script/start_camera_computer.sh
```

This runs:
```bash
docker run -it --rm -v /dev:/dev -v /dev/shm:/dev/shm --privileged --net=host \
  microros/micro-ros-agent:humble udp4 --port 9999 -v4
```

---

### Step 2: Start Camera Stream + Human Detection

**Option A (Recommended) – single launch file:**
```bash
ros2 launch yahboom_vision vision.launch.py
```

**Option B – run separately:**
```bash
# Terminal 1
ros2 run yahboom_vision image_proc
# Terminal 2
ros2 run yahboom_vision human_detection
```

**Topics published:**

| Topic | Type | Description |
|-------|------|-------------|
| `/yahboom/vision/camera/image_raw` | `sensor_msgs/Image` | Raw BGR frame (used by human_detection) |
| `/yahboom/vision/camera/debug` | `sensor_msgs/Image` | Annotated debug frame |

To preview the stream:
```bash
ros2 run rqt_image_view rqt_image_view /yahboom/vision/camera/debug
```

---

### Step 3: Trigger Human Detection

Call the service with a timeout (in seconds). Returns as soon as a human is confirmed, or when the timeout expires.

```bash
ros2 service call /yahboom_esp32/vision/human_detection \
  yahboom_interfaces/srv/HumanDetection "{timeout: 5.0}"
```

**Response example:**
```yaml
detected: true    # Human found within timeout
```
```yaml
detected: false   # No human detected before timeout
```

---

### Detection Thresholds

MediaPipe Pose detects 33 body landmarks. A frame is classified as **"human detected"** when:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `VISIBILITY_THRESHOLD` | `0.5` | Minimum confidence per landmark (0.0–1.0) |
| `LANDMARK_THRESHOLD` | `15` | Minimum number of visible landmarks (out of 33) |

> [!TIP]
> Tune these constants at the top of `human_detection.py` to adjust sensitivity.
> - **Reduce** `LANDMARK_THRESHOLD` → more sensitive (detects partial bodies)
> - **Increase** `LANDMARK_THRESHOLD` → more strict (requires full body visibility)

---

### Calling from Another Node (Python)

```python
from yahboom_interfaces.srv import HumanDetection

client = self.create_client(HumanDetection, '/yahboom_esp32/vision/human_detection')
client.wait_for_service()

req = HumanDetection.Request()
req.timeout = 5.0

future = client.call_async(req)
rclpy.spin_until_future_complete(self, future)

if future.result().detected:
    self.get_logger().info('Human detected!')
else:
    self.get_logger().info('No human found.')
```

---

### Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| No image on `/espRos/esp32camera` | Camera agent not running | Run `start_camera_computer.sh` first |
| `No frame received yet` warning | `image_proc` not running | Run `ros2 run yahboom_vision image_proc` |
| Image upside-down / mirrored | Orientation not configured | Run `set_camera.py` once |
| `detected` always `false` | Poor lighting / camera angle | Check debug topic with `rqt_image_view`, lower `LANDMARK_THRESHOLD` |
| `mediapipe` import error | Library not installed | `pip install mediapipe` |
| Service not found | Node not started | Run `ros2 run yahboom_vision human_detection` |





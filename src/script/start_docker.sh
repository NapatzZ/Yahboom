#!/bin/bash

# Allow local root to access X server for GUI support
xhost +local:root

# Run the container with GUI, USB, and privileged access
docker run -it --rm \
  --name yahboom_nav_container \
  --net=host \
  --privileged \
  -v /dev:/dev \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  -e ROS_DOMAIN_ID=20 \
  yahboom_ros2_workspace bash

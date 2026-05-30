#!/bin/bash

docker run -it --rm \
  --name yahboom_nav_container \
  -p 8090:8090/udp \
  -p 6080:6080 \
  -e ROS_DOMAIN_ID=20 \
  -v "$(pwd)/src:/ros2_ws/src" \
  yahboom_ros2_workspace bash

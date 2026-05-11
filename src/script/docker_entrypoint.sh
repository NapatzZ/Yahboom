#!/bin/bash
set -e

# Source ROS 2 base
source /opt/ros/humble/setup.bash

# Source workspace
if [ -f /ros2_ws/install/setup.bash ]; then
  source /ros2_ws/install/setup.bash
fi

# Execute the command passed to docker run
exec "$@"

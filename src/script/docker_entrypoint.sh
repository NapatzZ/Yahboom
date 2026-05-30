#!/bin/bash
set -e

source /opt/ros/humble/setup.bash

if [ -f /ros2_ws/install/setup.bash ]; then
  source /ros2_ws/install/setup.bash
fi

# Virtual display for RViz via noVNC (http://localhost:6080/vnc.html)
Xvfb :1 -screen 0 1280x1024x24 -ac &
sleep 1
x11vnc -display :1 -nopw -forever -quiet -rfbport 5900 &
websockify --web=/usr/share/novnc/ --wrap-mode=ignore 6080 localhost:5900 &

export DISPLAY=:1
export LIBGL_ALWAYS_SOFTWARE=1

exec "$@"

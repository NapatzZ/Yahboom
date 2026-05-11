FROM osrf/ros:humble-desktop

# Set non-interactive to avoid timezone prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /ros2_ws

# Copy requirements.txt
COPY requirements.txt /ros2_ws/

# Install system and ROS 2 dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    ros-humble-robot-localization \
    ros-humble-slam-toolbox \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-cv-bridge \
    ros-humble-rqt-image-view \
    nano \
    byobu \
    iputils-ping \
    net-tools \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies (includes mediapipe, pyyaml, opencv-python, etc.)
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY ./src /ros2_ws/src

# Resolve and install any remaining ROS dependencies
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && \
    apt-get update && \
    rosdep install --from-paths src --ignore-src -r -y && \
    rm -rf /var/lib/apt/lists/*"

# Build the workspace
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build"

# Setup bashrc to use the custom template and automatically source ROS and workspace
COPY ./src/script/bashrc_template /root/.bashrc
RUN sed -i 's|$HOME/Yahboom|/ros2_ws|g' /root/.bashrc && \
    sed -i 's|ip addr show wlp4s0 |hostname -I |g' /root/.bashrc

# NOTE: Two Micro-ROS agents are required (run outside the container):
#   Robot body:  docker run ... microros/micro-ros-agent:humble udp4 --port 8090
#   Camera ESP32: docker run ... microros/micro-ros-agent:humble udp4 --port 9999

# Set the default entrypoint
COPY ./src/script/docker_entrypoint.sh /
RUN chmod +x /docker_entrypoint.sh
ENTRYPOINT ["/docker_entrypoint.sh"]
CMD ["bash"]

# Copy micro-ros-agent from the official image
FROM --platform=linux/amd64 microros/micro-ros-agent:humble AS micro_ros_agent

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
    ros-humble-joint-state-publisher \
    ros-humble-joint-state-publisher-gui \
    ros-humble-xacro \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    libgl1-mesa-dri \
    nano \
    byobu \
    iputils-ping \
    net-tools \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# Copy micro-ros-agent workspace from the official image
COPY --from=micro_ros_agent /uros_ws/install /uros_ws/install

# Install python dependencies
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

# Set the default entrypoint
COPY ./src/script/docker_entrypoint.sh /
RUN chmod +x /docker_entrypoint.sh
ENTRYPOINT ["/docker_entrypoint.sh"]
CMD ["bash"]

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
    nano \
    iputils-ping \
    net-tools \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

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

# Setup bashrc to automatically source ROS and workspace
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> ~/.bashrc && \
    echo "export ROS_DOMAIN_ID=20" >> ~/.bashrc

# Set the default entrypoint
COPY ./src/script/docker_entrypoint.sh /
RUN chmod +x /docker_entrypoint.sh
ENTRYPOINT ["/docker_entrypoint.sh"]
CMD ["bash"]

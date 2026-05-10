#!/bin/bash

docker run --rm -it --name yahboom_ros2_docker --privileged -e ROS_DOMAIN_ID=20 --network=host -e DISPLAY nptttn/yahboom_docker:latest bash

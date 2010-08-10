#!/usr/bin/env bash
set -o errexit
source /tmp/ros-release/setup.sh
rosrun rosdeb build_release checkout $ROSDISTRO -r -w /opt/ros/cturtle
rosrun rosdeb build_release rosdep -w /opt/ros/cturtle -y
rosrun rosdeb build_release build -w /opt/ros/cturtle
rosrun rosdeb build_release package $ROSDISTRO -w /opt/ros/cturtle
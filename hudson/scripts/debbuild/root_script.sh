#!/usr/bin/env bash

# Argument are DISTRO, ARCH, ROSDISTRO
DISTRO=$1
ARCH=$2
ROSDISTRO=$3

echo "I have distro, arch, rosdistro:"
echo $DISTRO
echo $ARCH
echo $ROSDISTRO

set -o errexit
source /tmp/ros-release/setup.sh
rosrun rosdeb build_release checkout $ROSDISTRO -r -w /opt/ros/cturtle
rosrun rosdeb build_release rosdep -w /opt/ros/cturtle -y
rosrun rosdeb build_release build -w /opt/ros/cturtle
rosrun rosdeb build_release package $ROSDISTRO -w /opt/ros/cturtle
. /opt/ros/${ROS_DISTRO_NAME}/setup.sh
export ROS_HOME=/tmp/.ros
#TODO:FIXME:REMOVE
sudo apt-get install pkg-config
export ROS_PACKAGE_PATH=${ROS_DESTDIR}/opt/ros/${ROS_DISTRO_NAME}/stacks:${ROS_PACKAGE_PATH}

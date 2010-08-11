export ROS_ROOT=/opt/ros/unstable/ros
export PATH=${ROS_ROOT}/bin:${PATH}
export PYTHONPATH=${PYTHONPATH}:${ROS_ROOT}/core/roslib/src
export ROS_PACKAGE_PATH=/opt/ros/unstable/stacks
if [ ! "$ROS_MASTER_URI" ] ; then export ROS_MASTER_URI=http://localhost:11311 ; fi

. ${ROS_ROOT}/tools/rosbash/rosbash
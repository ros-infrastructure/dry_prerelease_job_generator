#!/bin/sh

# We expect the following environment variables to be set:
#export WORKSPACE=`pwd`
#export DISTRO=karmic
#export ARCH=amd64
#export ROSDISTRO=cturtle
#export ROSSTACK=ros
#export ROSVERSION=1.2.0

set -o errexit

export DISTRO_TGZ=${DISTRO}-base.tgz
export DEBNAME=ros-${ROSDISTRO}-`echo $ROSSTACK | sed -e 's/_/-/'`
export DEBVERSION=${ROSVERSION}-0~${DISTRO}
export ROSFILE=${ROSSTACK}-${ROSVERSION}
export DEBFILE=${DEBNAME}_${DEBVERSION}

# Remove all debs that depend on this package
ssh rosbuild@pub5.willowgarage.com "cat /var/packages/ros-shadow/ubuntu/dists/${DISTRO}/main/binary-${ARCH}/Packages | sed -nre \"s/^Package: (.*)/\1/;t hold;/^Depends: .*${DEBNAME}.*/{g;p};b;:hold h\" | xargs -I{} reprepro -b /var/packages/ros-shadow/ubuntu -V removefilter ${DISTRO} 'Package (=={})'"
# Remove this deb itself
ssh rosbuild@pub5.willowgarage.com "reprepro -b /var/packages/ros-shadow/ubuntu -V removefilter ${DISTRO} \"Package (==${DEBNAME})\""
# Copy it to pub5.willowgarage.com
scp result/${DEBFILE}_${ARCH}.deb result/${DEBFILE}_${ARCH}.changes result/${DEBFILE}.dsc result/${DEBFILE}.tar.gz rosbuild@pub5.willowgarage.com:/var/packages/ros-shadow/ubuntu/queue/${DISTRO}/
# Load it into the repo
ssh rosbuild@pub5.willowgarage.com reprepro -b /var/packages/ros-shadow/ubuntu -V processincoming ${DISTRO}
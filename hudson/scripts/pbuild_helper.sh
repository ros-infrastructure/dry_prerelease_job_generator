#!/bin/sh

set -o errexit

export WORKSPACE=`pwd`
export DISTRO=karmic
export ARCH=amd64
export ROSDISTRO=cturtle
export ROSSTACK=ros
export ROSVERSION=1.2.0
export DEBNAME=ros-${ROSDISTRO}-`echo $ROSSTACK | sed -e 's/_/-/'`
export DEBVERSION=1.2.0-0~${DISTRO}
export ROSFILE=${ROSSTACK}-${ROSVERSION}
export DEBFILE=${DEBNAME}_${DEBVERSION}

sudo apt-get install pbuilder
[ -e ${DISTRO}-base.tgz ] || 
{
    sudo pbuilder --create --distribution ${DISTRO} --othermirror "deb http://code.ros.org/packages/ros/ubuntu ${DISTRO} main" --basetgz ${DISTRO}-base.tgz --components "main restricted universe multiverse" --extrapackages "wget lsb-release debhelper"
}
wget https://code.ros.org/svn/release/download/stacks/${ROSSTACK}/${ROSFILE}/${DEBFILE}.dsc -O ${DEBFILE}.dsc
wget https://code.ros.org/svn/release/download/stacks/${ROSSTACK}/${ROSFILE}/${DEBFILE}.tar.gz -O ${DEBFILE}.tar.gz
mkdir -p hookdir
echo "wget https://code.ros.org/svn/release/download/stacks/${ROSSTACK}/${ROSFILE}/${ROSFILE}.tar.bz2 -O /tmp/buildd/${ROSFILE}.tar.bz2" > hookdir/A00fetch
chmod +x hookdir/A00fetch
mkdir -p result
sudo pbuilder --build --basetgz ${DISTRO}-base.tgz --hookdir hookdir  --buildresult result ${DEBFILE}.dsc

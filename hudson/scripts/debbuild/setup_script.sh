#!/usr/bin/env bash
set -o errexit
sudo apt-get install -y --force-yes build-essential python-yaml cmake subversion wget lsb-release fakeroot sudo debhelper cdbs ca-certificates debconf-utils wget

wget --no-check-certificate http://ros.org/rosinstall -O /tmp/rosinstall
chmod 755 /tmp/rosinstall
/tmp/rosinstall --rosdep-yes /tmp/ros-release http://www.ros.org/rosinstalls/ros-release.rosinstall
echo export JAVA_HOME=/usr/lib/jvm/java-6-sun >> /tmp/ros-release/setup.sh

sudo /tmp/ros/hudson/scripts/debbuild/root_script.sh

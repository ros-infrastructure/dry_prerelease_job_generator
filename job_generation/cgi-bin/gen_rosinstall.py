#!/usr/bin/env python

import sys
import cgi
import urllib
import os
import subprocess
import tempfile

import cgitb
cgitb.enable()


def main():
    print "Content-Type: text/html"     # HTML is following
    print                               # blank line, end of headers

    form = cgi.FieldStorage()
    keys = ['rosdistro', 'variant', 'overlay']
    for k in keys:
        if not k in form.keys():
            print 'Missing parameters: %s'%k
            return

    command = 'ssh -i /keys/id_dsa willow@pub8 export ROS_PACKAGE_PATH="/home/willow/ros_release:/opt/ros/cturtle/stacks" && export ROS_ROOT="/opt/ros/cturtle/ros" && export PATH="/opt/ros/cturtle/ros/bin:$PATH" && export PYTHONPATH="/opt/ros/cturtle/ros/core/roslib/src" && rosrun job_generation generate_rosinstall.py --rosdistro %s --variant %s --overlay %s --database /home/willow/rosinstall.db'%(form['rosdistro'].value, form['variant'].value, form['overlay'].value)
    res, err = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    print '%s %s'%(str(res), str(err))    


if __name__ == '__main__':
    main()

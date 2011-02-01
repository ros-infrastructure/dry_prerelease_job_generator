#!/usr/bin/env python

import sys
import cgi
import urllib
import os
import subprocess
import tempfile
import re

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
            return -1
    if form['rosdistro'].value not in ['boxturtle', 'cturtle', 'diamondback', 'unstable', 'electric', 'fuerte']:
         # needs to send httperror instead
         print 'invalid rosdistro parameter'
         return -1
    if form['overlay'].value not in ['yes', 'no']:
         # needs to send httperror instead
         print 'invalid overlay parameter'
         return -1
    p = re.compile('\A[A-Za-z]+[\w\-]*\Z')
    if not bool(p.match(form['variant'].value)):
         # needs to send httperror instead
         print 'invalid variant parameter'
         return -1

    command = 'export ROS_HOME=/tmp && export ROS_PACKAGE_PATH="/home/willow/ros_release:/opt/ros/cturtle/stacks" && export ROS_ROOT="/opt/ros/cturtle/ros" && export PATH="/opt/ros/cturtle/ros/bin:$PATH" && export PYTHONPATH="/opt/ros/cturtle/ros/core/roslib/src" && rosrun job_generation generate_rosinstall.py --rosdistro %s --variant %s --overlay %s --database /home/willow/rosinstall.db'%(form['rosdistro'].value, form['variant'].value, form['overlay'].value)


    helper = subprocess.Popen(['bash', '-c', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res, err = helper.communicate()
    if helper.returncode != 0:
        print '%s'%str(err)
        return -1
    else:
        print '%s'%str(res)
        return 0
    

if __name__ == '__main__':
    res = main()
    sys.exit( res )


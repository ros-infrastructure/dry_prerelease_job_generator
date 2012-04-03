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
    legacy_distro = ['cturtle', 'diamondback', 'electric']

    prefix = "{'other': {'local-name': '/opt/ros/fuerte/share/ros'}}, \
              {'other': {'local-name': '/opt/ros/fuerte/share'}}, \
              {'other': {'local-name': '/opt/ros/fuerte/stacks'}}, \
              {'setup-file': {'local-name': '/opt/ros/fuerte/setup.sh'}}"

    print "Content-Type: text/html"     # HTML is following
    print                               # blank line, end of headers

    form = cgi.FieldStorage()
    keys = ['rosdistro', 'variant', 'overlay']
    for k in keys:
        if not k in form.keys():
            return 'Missing parameters: %s'%k
    if form['overlay'].value not in ['yes', 'no']:
         # needs to send httperror instead
         return 'invalid overlay parameter'
    p = re.compile('\A[A-Za-z]+[\w\-]*\Z')
    if not bool(p.match(form['variant'].value)):
         # needs to send httperror instead
         return 'invalid variant parameter'


    # old legacy toolset in /home/willow/ros_release
    if form['rosdistro'].value in legacy_distro:
        command = 'export ROS_HOME=/tmp && export ROS_PACKAGE_PATH="/home/willow/ros_release:/opt/ros/cturtle/stacks" && export ROS_ROOT="/opt/ros/cturtle/ros" && export PATH="/opt/ros/cturtle/ros/bin:$PATH" && export PYTHONPATH="/opt/ros/cturtle/ros/core/roslib/src" && rosrun job_generation generate_rosinstall.py --rosdistro %s --variant %s --overlay %s --database /home/log/rosinstall.db'%(form['rosdistro'].value, form['variant'].value, form['overlay'].value)

    # new pypi-based tools
    else:
        command = 'generate_rosinstall.py --rosdistro %s --variant %s --overlay %s --database /home/log/rosinstall.db'%(form['rosdistro'].value, form['variant'].value, form['overlay'].value)

    helper = subprocess.Popen(['bash', '-c', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res, err = helper.communicate()
    if helper.returncode != 0:
        return '%s'%str(err)
    else:
        if not form['rosdistro'].value in legacy_distro: 
            res = "[" + prefix + ", " + res[1:]
        print '%s'%str(res)
        return 0
    

if __name__ == '__main__':
    sys.exit(main())


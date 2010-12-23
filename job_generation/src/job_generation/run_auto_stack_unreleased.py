#!/usr/bin/python


import roslib; roslib.load_manifest("job_generation")
import rosdistro
from jobs_common import *
import sys
import os
import optparse 
import subprocess
import urllib

def main():
    # parse command line options
    (options, args) = get_options(['rosdistro'], [])
    if not options:
        return -1

    # set environment
    env = get_environment()
    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])
    env['ROS_PACKAGE_PATH'] = '%s:/opt/ros/%s/stacks'%(env['WORKSPACE'], options.rosdistro)
    env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'


    # Parse distro file
    rosdistro_obj = rosdistro.Distro(ROSDISTRO_MAP[options.rosdistro])
    print 'Operating on ROS distro %s'%rosdistro_obj.release_name

    # Install Debian packages of ALL stacks in distro
    print 'Installing all stacks of ros distro %s: %s'%(options.rosdistro, str(rosdistro_obj.stacks.keys()))
    for stack in rosdistro_obj.stacks:
        subprocess.Popen(('sudo apt-get install %s --yes'%(stack_to_deb(stack, options.rosdistro))).split(' ')).communicate()
    

    # Run hudson helper 
    print 'Running Hudson Helper'
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%env['WORKSPACE']).split(' '), env=env)
    helper.communicate()
    return helper.returncode


if __name__ == '__main__':
    sys.exit( main() )






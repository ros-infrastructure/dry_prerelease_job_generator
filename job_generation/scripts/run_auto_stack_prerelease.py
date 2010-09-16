#pr2_!/usr/bin/python

from roslib import distro, stack_manifest
from jobs_common import *
import sys
import re
import os
import urllib2
import optparse 
import subprocess


def main():
    # parse command line options
    parser = optparse.OptionParser()
    
    parser.add_option('--stack', dest = 'stacklist', action='append',
                      help='Stack name')
    parser.add_option('--rosdistro', dest = 'rosdistro', default=False, action='store',
                      help='Ros distro name')
    (options, args) = parser.parse_args()
    if not options.stacklist or not options.rosdistro:
        print 'You did not specify all options to run this script.'
        return


    # set environment
    env = {}
    env['PYTHONPATH'] = '/opt/ros/%s/ros/core/roslib/src'%options.rosdistro
    env['WORKSPACE'] = os.environ['WORKSPACE']
    env['HOME'] = os.environ['WORKSPACE']
    env['JOB_NAME'] = os.environ['JOB_NAME']
    env['BUILD_NUMBER'] = os.environ['BUILD_NUMBER']
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR']
    env['PWD'] = os.environ['WORKSPACE']
    env['ROS_PACKAGE_PATH'] = '%s:/opt/ros/%s/stacks'%(os.environ['INSTALL_DIR'], options.rosdistro)
    env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])


    # Parse distro file
    rosdistro_obj = distro.Distro(ROSDISTRO_MAP[options.rosdistro])
    print 'Operating on ROS distro %s'%rosdistro_obj.release_name


    # Install Debian packages of ALL stacks in distro
    print 'Installing stacks of ros distro: %s'%options.rosdistro
    subprocess.Popen('sudo apt-get update'.split(' ')).communicate()
    subprocess.Popen(('sudo apt-get install %s --yes'%(stacks_to_debs(rosdistro_obj.stacks.keys(), options.rosdistro))).split(' ')).communicate()
    

    # Install all stacks that depend on this stack
    print 'Installing all stacks that depend on these stacks from source'
    print options.stacklist
    rosinstall = ''
    for stack in options.stacklist:
        rosinstall += stack_to_rosinstall(stack, rosdistro_obj.stacks, 'dev_svn')
    for stack in options.stacklist:
        res, err = subprocess.Popen(('rosstack depends-on %s'%stack).split(' '), stdout=subprocess.PIPE, env=env).communicate()
        print res
        rosinstall += stacks_to_rosinstall(res.split('\n'), rosdistro_obj.stacks)
    print rosinstall
    rosinstall_file = 'depends_on_overlay.rosinstall'
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    subprocess.Popen(('rosinstall depends_on_overlay /opt/ros/%s %s'%(options.rosdistro, rosinstall_file)).split(' ')).communicate()


    # Install system dependencies
    print 'Installing system dependencies'
    for stack in options.stacklist:
        subprocess.Popen(('rosdep install %s -y'%stack).split(' '), env=env).communicate()
    

    # Start Hudson Helper
    print 'Running Hudson Helper'
    subprocess.Popen('python hudson_helper --dir-test depends_on_overlay build'.split(' '), env=env).communicate()


if __name__ == '__main__':
    main()






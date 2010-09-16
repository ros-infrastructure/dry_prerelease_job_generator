#!/usr/bin/python

from roslib import distro, stack_manifest
from run_auto_stack_common import *
import sys
import re
import os
import urllib2
import optparse 
import subprocess


def main():
    # parse command line options
    parser = optparse.OptionParser()
    
    parser.add_option('--stack', dest = 'stacklist', default=False, action='append',
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
    res, err = subprocess.Popen('sudo apt-get update'.split(' '),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env).communicate()
    res, err = subprocess.Popen(('sudo apt-get install %s --yes'%(stack_to_deb(rosdistro_obj.stacks.keys(), 
                                                                               options.rosdistro))).split(' '),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env).communicate()
    print res
    

    # Install all stacks that depend on this stack
    print env['ROS_PACKAGE_PATH']
    print 'Installing all stack that depend on these stacks from source'
    rosinstall = stack_to_rosinstall(options.stack, rosdistro_obj.stacks, 'dev_svn')
    for stack in options.stacklist:
        res, err = subprocess.Popen(('rosstack depends-on %s'%stack).split(' '),
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env).communicate()
        rosinstall += stacks_to_rosinstall(res.split('\n'), rosdistro_obj.stacks)
    print rosinstall
    rosinstall_file = 'depends_on_overlay.rosinstall'
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    res, err = subprocess.Popen(('rosinstall depends_on_overlay /opt/ros/%s %s'%(options.rosdistro, 
                                                                                 rosinstall_file)).split(' '),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env).communicate()
    print res
    print err

    # Install system dependencies
    print 'Installing system dependencies'
    res, err = subprocess.Popen(('rosdep install %s -y'%options.stack).split(' '),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env).communicate()
    print res
    

    # Start Hudson Helper
    print 'Running Hudson Helper'
    res, err = subprocess.Popen('python hudson_helper --dir-test depends_on_overlay build'.split(' '),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env).communicate()
    print res


if __name__ == '__main__':
    main()






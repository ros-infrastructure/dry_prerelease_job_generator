#!/usr/bin/python

STACK_DIR = 'stack_overlay'


import roslib; roslib.load_manifest("job_generation")
from roslib import stack_manifest
from roslib2 import distro
from jobs_common import *
import sys
import os
import optparse 
import subprocess


def main():
    # parse command line options
    parser = optparse.OptionParser()
    
    parser.add_option('--rosdistro', dest = 'rosdistro', default=False, action='store',
                      help='Ros distro name')
    (options, args) = parser.parse_args()
    if not options.stacklist or not options.rosdistro:
        print 'You did not specify all options to run this script.'
        return


    # set environment
    env = {}
    env['WORKSPACE'] = os.environ['WORKSPACE']
    env['HOME'] = os.environ['WORKSPACE']
    env['JOB_NAME'] = os.environ['JOB_NAME']
    env['BUILD_NUMBER'] = os.environ['BUILD_NUMBER']
    env['PWD'] = os.environ['WORKSPACE']
    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])
    if 'ros' in rosdistro_obj.stacks.keys():
        env['ROS_ROOT'] = env['INSTALL_DIR']+'/'+STACK_DIR+'/ros'
        print "We're building ROS, so setting the ROS_ROOT to %s"%(env['ROS_ROOT'])
    else:
        env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'
    env['ROS_PACKAGE_PATH'] = os.environ['INSTALL_DIR']+'/'+STACK_DIR


    # Parse distro file
    rosdistro_obj = distro.Distro(ROSDISTRO_MAP[options.rosdistro])
    print 'Operating on ROS distro %s'%rosdistro_obj.release_name


    # Install all stacks in distro file from source
    print 'Installing all stacks in distro file from source'
    rosinstall = ''
    for stack in rosdistro_obj.stacks:
        rosinstall += stack_to_rosinstall(rosdistro_obj.stacks[stack], 'distro')
    rosinstall_file = 'stack_overlay.rosinstall'
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    print rosinstall
    subprocess.Popen(('rosinstall %s %s'%(STACK_DIR, rosinstall_file)).split(' ')).communicate()


    # Install system dependencies
    print 'Installing system dependencies'
    for stack in rosdistro_obj.stacks:
        subprocess.Popen(('rosmake --rosdep-install --rosdep-yes %s'%stack).split(' '), env=env).communicate()

    
    # Run hudson helper 
    print 'Running Hudson Helper'
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR'] + '/stack'
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%STACK_DIR).split(' '), env=env)
    helper.communicate()
    return helper.returncode


if __name__ == '__main__':
    sys.exit( main() )






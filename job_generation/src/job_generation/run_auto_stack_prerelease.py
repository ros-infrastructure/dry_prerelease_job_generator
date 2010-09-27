#!/usr/bin/python

STACK_DIR = 'stack_overlay'
DEPENDS_ON_DIR = 'depends_on_overlay'


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
    env['PWD'] = os.environ['WORKSPACE']
    env['ROS_PACKAGE_PATH'] = '%s:%s:%s:/opt/ros/%s/stacks'%(os.environ['INSTALL_DIR']+'/'+'ros_release',
                                                             os.environ['INSTALL_DIR']+'/'+STACK_DIR,
                                                             os.environ['INSTALL_DIR']+'/'+DEPENDS_ON_DIR,
                                                             options.rosdistro)
    if 'ros' in options.stacklist:
        env['ROS_ROOT'] = os.environ['INSTALL_DIR']+'/'+STACK_DIR
    else:
        env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])


    # Parse distro file
    rosdistro_obj = distro.Distro(ROSDISTRO_MAP[options.rosdistro])
    print 'Operating on ROS distro %s'%rosdistro_obj.release_name


    # Install the stacks to test from source
    print 'Installing the stacks to test from source'
    rosinstall = ''
    for stack in options.stacklist:
        rosinstall += stack_to_rosinstall(rosdistro_obj.stacks[stack], 'devel')
    rosinstall_file = 'stack_overlay.rosinstall'
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    print "ROSINSTALL STACK begin"
    print rosinstall
    print "ROSINSTALL STACK end"
    subprocess.Popen(('rosinstall %s /opt/ros/%s %s'%(STACK_DIR, options.rosdistro, rosinstall_file)).split(' ')).communicate()


    # Install Debian packages of stack dependencies
    print 'Installing debian packages of stack dependencies'
    subprocess.Popen('sudo apt-get update'.split(' ')).communicate()
    for stack in options.stacklist:
        with open('%s/%s/stack.xml'%(STACK_DIR, stack)) as stack_file:
            depends = stack_manifest.parse(stack_file.read()).depends
        subprocess.Popen(('sudo apt-get install %s --yes'%(stacks_to_debs(depends, options.rosdistro))).split(' ')).communicate()


    # Install system dependencies
    print 'Installing system dependencies'
    for stack in options.stacklist:
        subprocess.Popen(('rosdep install %s -y'%stack).split(' '), env=env).communicate()

    
    # Run hudson helper for stacks only
    print 'Running Hudson Helper'
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR'] + '/stack'
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%STACK_DIR).split(' '), env=env)
    helper.communicate()
    if helper.returncode != 0:
        return helper.returncode


    # Install Debian packages of ALL stacks in distro
    print 'Installing all stacks of ros distro %s: %s'%(options.rosdistro, str(rosdistro_obj.stacks.keys()))
    for stack in rosdistro_obj.stacks:
        subprocess.Popen(('sudo apt-get install %s --yes'%(stack_to_deb(stack, options.rosdistro))).split(' ')).communicate()
    

    # Install all stacks that depend on this stack
    print 'Installing all stacks that depend on these stacks from source'
    print "ENV begin"
    print str(env)
    print "ENV end"
    rosinstall = ''
    for stack in options.stacklist:
        print 'Installing dependencies of stack %s'%stack
        res, err = subprocess.Popen(('rosstack depends-on %s'%stack).split(' '), stdout=subprocess.PIPE, env=env).communicate()
        print res
        rosinstall += stacks_to_rosinstall(res.split('\n'), rosdistro_obj.stacks, 'distro')
    rosinstall_file = 'depends_on_overlay.rosinstall'
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    print "ROSINSTALL ALL begin"
    print rosinstall
    print "ROSINSTALL ALL end"
    subprocess.Popen(('rosinstall %s /opt/ros/%s %s'%(DEPENDS_ON_DIR, options.rosdistro, rosinstall_file)).split(' ')).communicate()


    # Run hudson helper for all stacks
    print 'Running Hudson Helper'
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR'] + '/depends_on'
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%DEPENDS_ON_DIR).split(' '), env=env)
    helper.communicate()
    return helper.returncode


if __name__ == '__main__':
    sys.exit( main() )






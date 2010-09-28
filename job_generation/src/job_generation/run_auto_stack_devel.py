#!/usr/bin/python

from roslib import stack_manifest
from jobs_common import *
import sys
import os
import optparse 
import subprocess
    

def main():
    # parse command line options
    parser = optparse.OptionParser()
    
    parser.add_option('--stack', dest = 'stack', default=False, action='store',
                      help='Stack name')
    parser.add_option('--rosdistro', dest = 'rosdistro', default=False, action='store',
                      help='Ros distro name')
    (options, args) = parser.parse_args()
    if not options.stack or not options.rosdistro:
        print 'You did not specify all options to run this script.'
        return


    # set environment
    env = {}
    env['WORKSPACE'] = os.environ['WORKSPACE']
    env['INSTALL_DIR'] = os.environ['INSTALL_DIR']
    env['HOME'] = os.environ['INSTALL_DIR']
    env['JOB_NAME'] = os.environ['JOB_NAME']
    env['BUILD_NUMBER'] = os.environ['BUILD_NUMBER']
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR']
    env['PWD'] = os.environ['WORKSPACE']
    env['ROS_PACKAGE_PATH'] = '%s:/opt/ros/%s/stacks'%(os.environ['WORKSPACE'], options.rosdistro)
    if options.stack == 'ros':
        env['ROS_ROOT'] = env['WORKSPACE']+'/'+options.stack+'/ros'
    else:
        env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'
    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])
    stack_dir = env['WORKSPACE']+'/'+options.stack


    # Install Debian packages of stack dependencies
    print 'Installing debian packages of stack dependencies'
    subprocess.Popen('sudo apt-get update'.split(' ')).communicate()
    with open('%s/stack.xml'%stack_dir) as stack_file:
        depends = stack_manifest.parse(stack_file.read()).depends
    subprocess.Popen(('sudo apt-get install %s --yes'%(stacks_to_debs(depends, options.rosdistro))).split(' ')).communicate()


    # Install system dependencies
    print 'Installing system dependencies'
    subprocess.Popen(('rosdep install %s -y'%options.stack).split(' '), env=env).communicate()


    # Start Hudson Helper
    print 'Running Hudson Helper'
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%stack_dir).split(' '), env=env)
    helper.communicate()
    return helper.returncode


if __name__ == '__main__':
    sys.exit( main() )





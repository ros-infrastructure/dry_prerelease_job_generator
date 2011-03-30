#!/usr/bin/python

from roslib import stack_manifest
from jobs_common import *
import sys
import os
import optparse 
import subprocess
    

def main():
    print "Starting run_auto_stack_devel script"

    # parse command line options
    print "Parsing command line options"
    (options, args) = get_options(['stack', 'rosdistro'], ['repeat'])
    print "Checking options 1"
    if not options:
        return -1
    print "Checking options 2"
    if len(options.stack) > 1:
        print "You can only provide one stack at a time"
        return -1
    print "Checking options 3"
    options.stack = options.stack[0]

    # set environment
    print "Setting up environment"
    env = get_environment()
    env['ROS_PACKAGE_PATH'] = '%s:/opt/ros/%s/stacks'%(os.environ['WORKSPACE'], options.rosdistro)
    if options.stack == 'ros':
        env['ROS_ROOT'] = env['WORKSPACE']+'/ros'
        print "Changing ROS_ROOT and PYTHONPATH because we are building ROS"
    else:
        env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'

    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])
    stack_dir = env['WORKSPACE']+'/'+options.stack


    # Install Debian packages of stack dependencies
    print "Installing Debian packages of stack dependencies"
    call('sudo apt-get update', env)
    with open('%s/stack.xml'%stack_dir) as stack_file:
        depends = stack_manifest.parse(stack_file.read()).depends
    if len(depends) != 0:
        print 'Installing debian packages of stack dependencies: %s'%str(depends)        
        call('sudo apt-get install %s --yes'%(stacks_to_debs(depends, options.rosdistro)), env,
             'Installing dependencies of stack "%s": %s'%(options.stack, str(depends)))

    # Install system dependencies
    print 'Installing system dependencies'
    call('rosmake rosdep', env)
    call('rosdep install -y %s'%options.stack, env,
         'Installing system dependencies of stack %s'%options.stack)
    

    # Start Hudson Helper
    print 'Running Hudson Helper'
    res = 0
    for r in range(0, options.repeat+1):
        env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR']+'/run_'+str(r)
        res_one = subprocess.call(('./hudson_helper --dir-test %s build'%stack_dir).split(' '), env=env)
        if res_one != 0:
            res = res_one
    return res


if __name__ == '__main__':
    try:
        res = main()
        sys.exit( res )
    except Exception:
        sys.exit(-1)





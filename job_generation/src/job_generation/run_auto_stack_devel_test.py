#!/usr/bin/python

from roslib import stack_manifest
from jobs_common import *
import sys
import os
import optparse 
import subprocess
    

def main():
    # parse command line options
    (options, args) = get_options(['stack', 'rosdistro'], ['repeat'])
    if not options:
        return -1
    if len(options.stack) > 1:
        print "You can only provide one stack at a time"
        return -1
    options.stack = options.stack[0]

    # set environment
    env = get_environment()
    env['ROS_PACKAGE_PATH'] = '%s:/opt/ros/%s/stacks'%(os.environ['WORKSPACE'], options.rosdistro)
    if options.stack == 'ros':
        env['ROS_ROOT'] = os.path.join(env['WORKSPACE'], 'ros')
        print "Changing ROS_ROOT and PYTHONPATH because we are building ROS"
    else:
        env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PYTHONPATH'] = os.path.join(env['ROS_ROOT'], 'core', 'roslib', 'src')

    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])
    stack_dir = os.path.join(env['WORKSPACE'], options.stack)

    print 'Wimpie'
    call('wimpie command', env, 'Wim Message test')

    # Install Debian packages of stack dependencies
    subprocess.Popen('sudo apt-get update'.split(' ')).communicate()
    with open('%s/stack.xml'%stack_dir) as stack_file:
        depends = stack_manifest.parse(stack_file.read()).depends
    if len(depends) != 0:
        print 'Installing debian packages of stack dependencies: %s'%str(depends)        
        res = subprocess.call(('sudo apt-get install %s --yes'%(stacks_to_debs(depends, options.rosdistro))).split(' '))
        if res != 0:
            return res
    else:
        print 'Stack does not have any dependencies, not installing any other debian packages'

    # Install system dependencies
    print 'Installing system dependencies'
    subprocess.Popen(('rosmake -V --status-rate=0 --rosdep-install --rosdep-yes %s'%options.stack).split(' '), env=env).communicate()


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
    sys.exit(main())
    try:
        res = main()
        sys.exit( res )
    except Exception:
        sys.exit(-1)





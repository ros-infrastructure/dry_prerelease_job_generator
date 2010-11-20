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
    parser.add_option('--repeat', dest = 'repeat', default=0, action='store',
                      help='How many times to repeat the test')
    (options, args) = parser.parse_args()
    if not options.stack or not options.rosdistro:
        print 'You did not specify all options to run this script.'
        return
    options.repeat = int(options.repeat)
    if options.repeat < 0:
        options.repeat = 0
        print 'Setting repeat from %d to 0'%options.repeat 

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
        env['ROS_ROOT'] = env['WORKSPACE']+'/ros'
        print "Changing ROS_ROOT and PYTHONPATH because we are building ROS"
    else:
        env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'

    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])
    stack_dir = env['WORKSPACE']+'/'+options.stack


    # Install Debian packages of stack dependencies
    subprocess.Popen('sudo apt-get update'.split(' ')).communicate()
    with open('%s/stack.xml'%stack_dir) as stack_file:
        depends = stack_manifest.parse(stack_file.read()).depends
    print 'Installing debian packages of stack dependencies: %s'%str(depends)        
    subprocess.Popen(('sudo apt-get install %s --yes'%(stacks_to_debs(depends, options.rosdistro))).split(' ')).communicate()


    # Install system dependencies
    print 'Installing system dependencies'
    subprocess.Popen(('rosmake -V --status-rate=0 --rosdep-install --rosdep-yes %s'%options.stack).split(' '), env=env).communicate()


    # Start Hudson Helper
    print 'Running Hudson Helper'
    res = 0
    for r in range(0, options.repeat+1):
        env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR']+'/run_'+str(r)
        helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%stack_dir).split(' '), env=env)
        helper.communicate()
        if helper.returncode != 0:
            res = helper.returncode
    return res


if __name__ == '__main__':
    sys.exit( main() )





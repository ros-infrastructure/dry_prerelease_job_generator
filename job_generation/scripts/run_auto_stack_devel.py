#!/usr/bin/python

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
    env['PYTHONPATH'] = '/opt/ros/%s/ros/core/roslib/src'%options.rosdistro
    env['WORKSPACE'] = os.environ['WORKSPACE']
    env['INSTALL_DIR'] = os.environ['INSTALL_DIR']
    env['HOME'] = os.environ['INSTALL_DIR']
    env['JOB_NAME'] = os.environ['JOB_NAME']
    env['BUILD_NUMBER'] = os.environ['BUILD_NUMBER']
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR']
    env['PWD'] = os.environ['WORKSPACE']
    env['ROS_PACKAGE_PATH'] = '%s:/opt/ros/%s/stacks'%(os.environ['WORKSPACE'], options.rosdistro)
    env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])


    # Parse distro file
    rosdistro_obj = distro.Distro(ROSDISTRO_MAP[options.rosdistro])
    print 'Operating on ROS distro %s'%rosdistro_obj.release_name


    # Install Debian packages of stack dependencies
    stack_xml = rosdistro_obj.stacks[options.stack].dev_svn + '/stack.xml'
    stack_file = urllib2.urlopen(stack_xml)
    depends = stack_manifest.parse(stack_file.read()).depends
    stack_file.close()
    print 'Installing stack dependencies Debians: %s'%stacks_to_debs(depends, options.rosdistro)
    subprocess.Popen('sudo apt-get update'.split(' ')).communicate()
    subprocess.Popen(('sudo apt-get install %s %s --yes'%(stack_to_deb(options.stack, options.rosdistro), stacks_to_debs(depends, options.rosdistro))).split(' ')).communicate()
    

    # Install system dependencies
    print 'Installing system dependencies'
    subprocess.Popen(('rosdep install %s -y'%options.stack).split(' '), env=env).communicate()


    # Start Hudson Helper
    print 'Running Hudson Helper'
    test_dir = env['WORKSPACE']+'/'+options.stack
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%test_dir).split(' '), env=env)
    helper.communicate()
    print "HUDSON HELPER EXITS WITH RETURN CODE %d"%helper.returncode
    return helper.returncode


if __name__ == '__main__':
    sys.exit( main() )





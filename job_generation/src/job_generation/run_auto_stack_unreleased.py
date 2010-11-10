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
    parser = optparse.OptionParser()
    parser.add_option('--rosdistro', dest = 'rosdistro', default=False, action='store',
                      help='Ros distro name')
    (options, args) = parser.parse_args()

    # set environment
    env = {}
    env['WORKSPACE'] = os.environ['WORKSPACE']
    env['HOME'] = os.environ['WORKSPACE']
    env['JOB_NAME'] = os.environ['JOB_NAME']
    env['BUILD_NUMBER'] = os.environ['BUILD_NUMBER']
    env['PWD'] = os.environ['WORKSPACE']
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR']
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
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%stack_dir).split(' '), env=env)
    helper.communicate()
    return helper.returncode


if __name__ == '__main__':
    sys.exit( main() )






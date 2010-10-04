#!/usr/bin/python

UNRELEASED_DIR = 'stack_overlay'
ROSINSTALL_FILE = 'unreleased.rosinstall'


import roslib; roslib.load_manifest("job_generation")
from roslib import stack_manifest
from roslib2 import distro
from jobs_common import *
import sys
import os
import optparse 
import subprocess
import urllib

def main():
    # parse command line options
    parser = optparse.OptionParser()
    
    parser.add_option('--rosinstall', dest = 'rosinstall', action='store',
                      help='Stack name')
    parser.add_option('--rosdistro', dest = 'rosdistro', default=False, action='store',
                      help='Ros distro name')
    (options, args) = parser.parse_args()
    if not options.rosinstall or not options.rosdistro:
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
    env['ROS_PACKAGE_PATH'] = '%s:/opt/ros/%s/stacks'%(os.environ['INSTALL_DIR']+'/'+UNRELEASED_DIR,
                                                       options.rosdistro)
    env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'


    # Parse distro file
    rosdistro_obj = distro.Distro(ROSDISTRO_MAP[options.rosdistro])
    print 'Operating on ROS distro %s'%rosdistro_obj.release_name

    # Install Debian packages of ALL stacks in distro
    print 'Installing all stacks of ros distro %s: %s'%(options.rosdistro, str(rosdistro_obj.stacks.keys()))
    for stack in rosdistro_obj.stacks:
        subprocess.Popen(('sudo apt-get install %s --yes'%(stack_to_deb(stack, options.rosdistro))).split(' ')).communicate()
    

    # Install unreleased code to test
    with open(ROSINSTALL_FILE, 'w') as f:
        f.write(urllib.urlopen(options.rosinstall).read())
    command = 'rosinstall %s /opt/ros/%s %s'%(UNRELEASED_DIR, options.rosdistro, ROSINSTALL_FILE)
    print '!!!!!!!!!!!!!!!!!!!'
    print command
    print '!!!!!!!!!!!!!!!!!!!'
    subprocess.Popen(command.split(' ')).communicate()


    # Run hudson helper 
    print 'Running Hudson Helper'
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%UNRELEASED_DIR).split(' '), env=env)
    helper.communicate()
    return helper.returncode


if __name__ == '__main__':
    sys.exit( main() )






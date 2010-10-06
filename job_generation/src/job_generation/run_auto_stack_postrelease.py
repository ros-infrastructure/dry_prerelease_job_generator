#!/usr/bin/python

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
    
    parser.add_option('--stack', dest = 'stack', action='store',
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
    env['HOME'] = os.environ['WORKSPACE']
    env['JOB_NAME'] = os.environ['JOB_NAME']
    env['BUILD_NUMBER'] = os.environ['BUILD_NUMBER']
    env['PWD'] = os.environ['WORKSPACE']
    env['ROS_PACKAGE_PATH'] = '%s:%s:/opt/ros/%s/stacks'%(os.environ['WORKSPACE']+'/'+options.stack,
                                                          os.environ['INSTALL_DIR']+'/'+DEPENDS_ON_DIR,
                                                          options.rosdistro)
    if options.stack == 'ros':
        env['ROS_ROOT'] = os.environ['WORKSPACE']+'/'+options.stack
        print "We're building ROS, so setting the ROS_ROOT to %s"%(env['ROS_ROOT'])
    else:
        env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'
    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])


    # Parse distro file
    rosdistro_obj = distro.Distro(ROSDISTRO_MAP[options.rosdistro])
    print 'Operating on ROS distro %s'%rosdistro_obj.release_name


    # Install Debian packages of stack dependencies
    print 'Installing debian packages of stack dependencies'
    subprocess.Popen('sudo apt-get update'.split(' ')).communicate()
    with open('%s/%s/stack.xml'%(os.environ['WORKSPACE'], options.stack)) as stack_file:
        depends = stack_manifest.parse(stack_file.read()).depends
    subprocess.Popen(('sudo apt-get install %s --yes'%(stacks_to_debs(depends, options.rosdistro))).split(' ')).communicate()


    # Install system dependencies
    print 'Installing system dependencies'
    subprocess.Popen(('rosmake --rosdep-install --rosdep-yes %s'%options.stack).split(' '), env=env).communicate()

    
    # Run hudson helper for stacks only
    print 'Running Hudson Helper'
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR'] + '/' + options.stack
    helper = subprocess.Popen(('./hudson_helper --dir-test %s/%s build'%(env['WORKSPACE'], options.stack)).split(' '), env=env)
    helper.communicate()
    if helper.returncode != 0:
        return helper.returncode


    # Install Debian packages of ALL stacks in distro
    print 'Installing all stacks of ros distro %s: %s'%(options.rosdistro, str(rosdistro_obj.stacks.keys()))
    for stack in rosdistro_obj.stacks:
        subprocess.Popen(('sudo apt-get install %s --yes'%(stack_to_deb(stack, options.rosdistro))).split(' ')).communicate()
    

    # Install all stacks that depend on this stack
    print 'Installing all stacks that depend on these stacks from source'
    res, err = subprocess.Popen(('rosstack depends-on %s'%options.stack).split(' '), stdout=subprocess.PIPE, env=env).communicate()
    print 'These stacks depend on the stacks we are testing: "%s"'%str(res)
    depends_on = res.split('\n')
    depends_on.remove('')
    if len(depends_on) == 0:
        print 'No stack depends on %s, finishing test.'%options.stack
        return 0
    rosinstall = [stack_to_rosinstall(s, rosdistro_obj.stacks, 'distro') for s in depends_on].join('\n')
    print 'Running rosinstall on "%s"'%rosinstall
    rosinstall_file = '%s.rosinstall'%DEPENDS_ON_DIR
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    subprocess.Popen(('rosinstall %s /opt/ros/%s %s'%(DEPENDS_ON_DIR, options.rosdistro, rosinstall_file)).split(' ')).communicate()


    # Run hudson helper for all stacks
    print 'Running Hudson Helper'
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR'] + '/' + DEPENDS_ON_DIR
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%DEPENDS_ON_DIR).split(' '), env=env)
    helper.communicate()
    return helper.returncode


if __name__ == '__main__':
    sys.exit( main() )






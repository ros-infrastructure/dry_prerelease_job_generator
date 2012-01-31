#!/usr/bin/python

DEPENDS_ON_DIR = 'depends_on_overlay'

import rospkg
import rospkg.distro

from job_generation.jobs_common import *
import sys
import os
import optparse 
import subprocess


def main():
    # parse command line options
    (options, args) = get_options(['rosdistro', 'stack'], [])
    if not options:
        return -1
    if len(options.stack) > 1:
        print "You can only provide one stack at a time"
        return -1
    options.stack = options.stack[0]
    distro_name = options.rosdistro

    # set environment
    env = get_environment()
    env['ROS_PACKAGE_PATH'] = os.pathsep.join([env['WORKSPACE']+'/'+options.stack,
                                               env['INSTALL_DIR']+'/'+DEPENDS_ON_DIR,
                                               env['ROS_PACKAGE_PATH']])

    # Parse distro file
    distro_obj = rospkg.distro.load_distro(rospkg.distro.distro_uri(distro_name))
    print 'Operating on ROS distro %s'%distro_obj.release_name

    # Install Debian packages of stack dependencies
    print 'Installing debian packages of stack dependencies'
    call('sudo apt-get update', env)
    stack_dir = os.path.join(os.environ['WORKSPACE'], options.stack)
    rosstack = rospkg.RosStack(ros_paths=[stack_dir])
    depends = rosstack.get_depends(options.stack, implicit=False)
    if len(depends) != 0:
        call('sudo apt-get install %s --yes'%(stacks_to_debs(depends, distro_name)), env,
             'Installing dependencies of stack "%s": %s'%(options.stack, str(depends)))

    # Install system dependencies
    print 'Installing system dependencies'
    call('rosdep install -y %s'%options.stack, env,
         'Installing system dependencies of stack %s'%options.stack)

    
    # Run hudson helper for stacks only
    print 'Running Hudson Helper'
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR'] + '/' + options.stack
    helper = subprocess.Popen(('./hudson_helper --dir-test %s/%s build'%(env['WORKSPACE'], options.stack)).split(' '), env=env)
    helper.communicate()
    if helper.returncode != 0:
        return helper.returncode


    # Install Debian packages of ALL stacks in distro
    print 'Installing all released stacks of ros distro %s: %s'%(distro_name, str(distro_obj.released_stacks.keys()))
    for stack in distro_obj.released_stacks:
        call('sudo apt-get install %s --yes'%(stack_to_deb(stack, distro_name)), env, ignore_fail=True)

    # Install all stacks that depend on this stack
    print 'Installing all stacks that depend on these stacks from source'
    res = call('rosstack depends-on %s'%options.stack, env, 'Getting list of stacks that depends on %s'%options.stack)
    print 'These stacks depend on the stacks we are testing: "%s"'%str(res)
    if res == '':
        print 'No stack depends on %s, finishing test.'%options.stack
        return 0
    rosinstall = stacks_to_rosinstall(res.split('\n'), distro_obj.released_stacks, 'release-tar')
    print 'Running rosinstall on "%s"'%rosinstall
    rosinstall_file = '%s.rosinstall'%DEPENDS_ON_DIR
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    call('rosinstall --rosdep-yes %s /opt/ros/%s %s/%s %s'%(DEPENDS_ON_DIR, distro_name, os.environ['WORKSPACE'], options.stack, rosinstall_file), env,
         'Install of stacks that depend on %s from source'%options.stack)

    # Remove stacks that depend on this stack from Debians
    print 'Removing all stack from Debian that depend on this stack'
    call('sudo apt-get remove %s --yes'%stack_to_deb(options.stack, distro_name), env)


    # Run hudson helper for all stacks
    print 'Running Hudson Helper'
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR'] + '/' + DEPENDS_ON_DIR
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%DEPENDS_ON_DIR).split(' '), env=env)
    helper.communicate()
    return helper.returncode


if __name__ == '__main__':
    try:
        res = main()
        sys.exit( res )
    except Exception:
        sys.exit(-1)







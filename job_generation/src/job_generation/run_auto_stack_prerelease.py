#!/usr/bin/python

STACK_DIR = 'stack_overlay'
DEPENDS_ON_DIR = 'depends_on_overlay'


import roslib; roslib.load_manifest("job_generation")
from roslib import stack_manifest
import rosdistro
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

    # set environment
    env = get_environment()
    env['ROS_PACKAGE_PATH'] = '%s:%s:/opt/ros/%s/stacks'%(os.path.join(os.environ['INSTALL_DIR'], STACK_DIR),
                                                          os.path.join(os.environ['INSTALL_DIR'], DEPENDS_ON_DIR),
                                                          options.rosdistro)
    if 'ros' in options.stack:
        env['ROS_ROOT'] = os.environ['INSTALL_DIR']+'/'+STACK_DIR+'/ros'
        print "We're building ROS, so setting the ROS_ROOT to %s"%(env['ROS_ROOT'])
    else:
        env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'
    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])


    # Parse distro file
    rosdistro_obj = rosdistro.Distro(ROSDISTRO_MAP[options.rosdistro])
    print 'Operating on ROS distro %s'%rosdistro_obj.release_name


    # Install the stacks to test from source
    print 'Installing the stacks to test from source'
    rosinstall = ''
    for stack in options.stack:
        rosinstall += stack_to_rosinstall(rosdistro_obj.stacks[stack], 'devel')
    rosinstall_file = '%s.rosinstall'%STACK_DIR
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    call('rosinstall %s /opt/ros/%s %s'%(STACK_DIR, options.rosdistro, rosinstall_file), env,
         'Failed to install the stacks to test from source.')


    # Install Debian packages of stack dependencies
    print 'Installing debian packages of stack dependencies from stacks %s'%str(options.stack)
    call('sudo apt-get update', env)
    for stack in options.stack:
        with open('%s/%s/stack.xml'%(STACK_DIR, stack)) as stack_file:
            depends = [str(d) for d in stack_manifest.parse(stack_file.read()).depends]  # convert to list
        for s in options.stack:  # remove stacks we are testing from dependency list, as debians might not yet exist
            if s in depends:
                depends.remove(s)
        if len(depends) != 0:
            print 'Installing debian packages of "%s" dependencies: %s'%(stack, str(depends))
            call('sudo apt-get install %s --yes'%(stacks_to_debs(depends, options.rosdistro)), env)
        else:
            print 'Stack %s does not have any dependencies, not installing any other debian packages'%stack


    # Install system dependencies
    print 'Installing system dependencies'
    for stack in options.stack:
        call('rosmake -V --status-rate=0 --rosdep-install --rosdep-yes %s'%stack, env,
             'Failed to install system dependencies of stack %s'%stack)

    
    # Run hudson helper for stacks only
    print 'Running Hudson Helper'
    res = 0
    for r in range(0, int(options.repeat)+1):
        env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR'] + '/' + STACK_DIR + '_run_' + str(r)
        helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%STACK_DIR).split(' '), env=env)
        helper.communicate()
        if helper.returncode != 0:
            res = helper.returncode
    if res != 0:
        return res


    # Install Debian packages of ALL stacks in distro
    print 'Installing all stacks of ros distro %s: %s'%(options.rosdistro, str(rosdistro_obj.released_stacks.keys()))
    for stack in rosdistro_obj.released_stacks:
        call('sudo apt-get install %s --yes'%(stack_to_deb(stack, options.rosdistro)), env, ignore_fail=True)
    

    # Install all stacks that depend on this stack
    print 'Installing all stacks that depend on these stacks from source'
    depends_on = {}
    for stack in options.stack:
        res, err = subprocess.Popen(('rosstack depends-on %s'%stack).split(' '), stdout=subprocess.PIPE, env=env).communicate()
        if res != '':
            for r in res.split('\n'):
                if r != '':
                    depends_on[r] = ''
    print 'Removing the stacks we are testing from the depends_on list'
    depends_on_keys = list(set(depends_on.keys()) - set(options.stack))
    if len(depends_on_keys) == 0:
        print 'No stacks depends on %s, finishing test.'%options.stack        
        return 0
    print 'These stacks depend on the stacks we are testing: "%s"'%str(depends_on_keys)
    rosinstall = stacks_to_rosinstall(depends_on_keys, rosdistro_obj.released_stacks, 'distro')
    rosinstall_file = '%s.rosinstall'%DEPENDS_ON_DIR
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    call('rosinstall %s /opt/ros/%s %s'%(DEPENDS_ON_DIR, options.rosdistro, rosinstall_file), env,
         'Failed to do a source install of the stacks that depend on the stacks that are getting tested.')

    # Remove stacks that depend on this stack from Debians
    print 'Removing all stacks from Debian that depend on these stacks'
    for stack in options.stack:    
        call('sudo apt-get remove %s --yes'%stack_to_deb(stack, options.rosdistro), env)

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







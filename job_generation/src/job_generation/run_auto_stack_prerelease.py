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
    parser = optparse.OptionParser()
    
    parser.add_option('--stack', dest = 'stacklist', action='append',
                      help='Stack name')
    parser.add_option('--rosdistro', dest = 'rosdistro', default=False, action='store',
                      help='Ros distro name')
    parser.add_option('--repeat', dest = 'repeat', default=0, action='store',
                      help='How many times to repeat the tests of the stack itself')
    (options, args) = parser.parse_args()
    if not options.stacklist or not options.rosdistro:
        print 'You did not specify all options to run this script.'
        return


    # set environment
    env = {}
    env['WORKSPACE'] = os.environ['WORKSPACE']
    env['HOME'] = os.environ['WORKSPACE']
    env['JOB_NAME'] = os.environ['JOB_NAME']
    env['BUILD_NUMBER'] = os.environ['BUILD_NUMBER']
    env['PWD'] = os.environ['WORKSPACE']
    env['ROS_PACKAGE_PATH'] = '%s:%s:/opt/ros/%s/stacks'%(os.environ['INSTALL_DIR']+'/'+STACK_DIR,
                                                          os.environ['INSTALL_DIR']+'/'+DEPENDS_ON_DIR,
                                                          options.rosdistro)
    if 'ros' in options.stacklist:
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
    for stack in options.stacklist:
        rosinstall += stack_to_rosinstall(rosdistro_obj.stacks[stack], 'devel')
    rosinstall_file = '%s.rosinstall'%STACK_DIR
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    subprocess.Popen(('rosinstall %s /opt/ros/%s %s'%(STACK_DIR, options.rosdistro, rosinstall_file)).split(' ')).communicate()


    # Install Debian packages of stack dependencies
    print 'Installing debian packages of stack dependencies from stacks %s'%str(options.stacklist)
    subprocess.Popen('sudo apt-get update'.split(' ')).communicate()
    for stack in options.stacklist:
        with open('%s/%s/stack.xml'%(STACK_DIR, stack)) as stack_file:
            depends = [str(d) for d in stack_manifest.parse(stack_file.read()).depends]  # convert to list
        for s in options.stacklist:  # remove stacks we are testing from dependency list, as debians might not yet exist
            if s in depends:
                depends.remove(s)
        if len(depends) != 0:
            print 'Installing debian packages of "%s" dependencies: %s'%(stack, str(depends))
            res = subprocess.call(('sudo apt-get install %s --yes'%(stacks_to_debs(depends, options.rosdistro))).split(' '))
            if res != 0:
                return res
        else:
            print 'Stack %s does not have any dependencies, not installing any other debian packages'%stack


    # Install system dependencies
    print 'Installing system dependencies'
    for stack in options.stacklist:
        subprocess.Popen(('rosmake -V --status-rate=0 --rosdep-install --rosdep-yes %s'%stack).split(' '), env=env).communicate()

    
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
        subprocess.Popen(('sudo apt-get install %s --yes'%(stack_to_deb(stack, options.rosdistro))).split(' ')).communicate()
    

    # Install all stacks that depend on this stack
    print 'Installing all stacks that depend on these stacks from source'
    depends_on = {}
    for stack in options.stacklist:
        res, err = subprocess.Popen(('rosstack depends-on %s'%stack).split(' '), stdout=subprocess.PIPE, env=env).communicate()
        if res != '':
            for r in res.split('\n'):
                if r != '':
                    depends_on[r] = ''
    print 'Removing the stacks we are testing from the depends_on list'
    depends_on_keys = list(set(depends_on.keys()) - set(options.stacklist))
    if len(depends_on_keys) == 0:
        print 'No stacks depends on %s, finishing test.'%options.stacklist        
        return 0
    print 'These stacks depend on the stacks we are testing: "%s"'%str(depends_on_keys)
    rosinstall = stacks_to_rosinstall(depends_on_keys, rosdistro_obj.released_stacks, 'distro')
    rosinstall_file = '%s.rosinstall'%DEPENDS_ON_DIR
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    helper = subprocess.Popen(('rosinstall %s /opt/ros/%s %s'%(DEPENDS_ON_DIR, options.rosdistro, rosinstall_file)).split(' '))
    helper.communicate()
    if helper.returncode != 0:
        print 'Failed to do a source install of the depends-on stacks.'
        return helper.returncode
    

    # Remove stacks that depend on this stack from Debians
    print 'Removing all stacks from Debian that depend on these stacks'
    for stack in options.stacklist:    
        subprocess.Popen(('sudo apt-get remove %s --yes'%stack_to_deb(stack, options.rosdistro)).split(' ')).communicate()

    # Run hudson helper for all stacks
    print 'Running Hudson Helper'
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR'] + '/' + DEPENDS_ON_DIR
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%DEPENDS_ON_DIR).split(' '), env=env)
    helper.communicate()
    return helper.returncode


if __name__ == '__main__':
    sys.exit( main() )






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
    (options, args) = get_options(['rosdistro'], [])
    if not options:
        return -1

    # set environment
    env = get_environment()
    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])
    env['ROS_PACKAGE_PATH'] = '%s:/opt/ros/%s/stacks'%(env['WORKSPACE'], options.rosdistro)
    env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'


    # Parse distro file
    rosdistro_obj = rosdistro.Distro(ROSDISTRO_MAP[options.rosdistro])
    print 'Operating on ROS distro %s'%rosdistro_obj.release_name

    # Install Debian packages of ALL stacks in distro
    call('sudo apt-get update', env)
    print 'Installing all stacks of ros distro %s: %s'%(options.rosdistro, str(rosdistro_obj.stacks.keys()))
    for stack in rosdistro_obj.stacks:
        call('sudo apt-get install %s --yes'%(stack_to_deb(stack, options.rosdistro)), env, ignore_fail=True)
    
    # install system dependencies of all packages
    res, err = subprocess.Popen('rospack list'.split(' '), env=env, stdout=subprocess.PIPE).communicate()
    packages = [p.split(' ')[0] for p in res.split('\n') if p != '']
    for pkg in packages:
        if not pkg in rosdistro_obj.stacks:
            res, err = subprocess.Popen(('rospack find %s'%pkg).split(' '), env=env, stdout=subprocess.PIPE).communicate()
            if not os.path.isfile(res[0,len(res)-1]+'/ROS_BUILD_BLACKLIST'):
                call('rosdep install -y %s'%pkg, env, 'Installing system dependencies of package %s'%pkg)


    # Run hudson helper 
    print 'Running Hudson Helper'
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%env['WORKSPACE']).split(' '), env=env)
    helper.communicate()
    return helper.returncode


if __name__ == '__main__':
    try:
        res = main()
        sys.exit( res )
    except Exception:
        sys.exit(-1)





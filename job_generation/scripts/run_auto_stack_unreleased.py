#!/usr/bin/python

import rospkg
import rospkg.distro

from job_generation.jobs_common import *
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
    env['ROS_PACKAGE_PATH'] = os.pathsep.join(env['WORKSPACE'], env['ROS_PACKAGE_PATH'])

    # Parse distro file
    distro_name = options.rosdistro
    distro_obj = rospkg.distro.load_distro(rospkg.distro.distro_uri(distro_name))
    print 'Operating on ROS distro %s'%distro_obj.release_name

    # Install Debian packages of ALL stacks in distro
    call('sudo apt-get update', env)
    print 'Installing all stacks of ros distro %s: %s'%(distro_name, str(distro_obj.stacks.keys()))
    for stack in distro_obj.stacks:
        call('sudo apt-get install %s --yes'%(stack_to_deb(stack, distro_name)), env, ignore_fail=True)
    
    # install system dependencies of all packages
    rospack = rospkg.RosPack(ros_paths=rospkg.environment.get_ros_paths(env=env))
    packages = rospack.list()
    for pkg in packages:
        if not pkg in distro_obj.stacks:
            pkg_dir = rospack.get_path(pkg)
            if not os.path.isfile(os.path.join(pkg_dir, 'ROS_BUILD_BLACKLIST'):
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





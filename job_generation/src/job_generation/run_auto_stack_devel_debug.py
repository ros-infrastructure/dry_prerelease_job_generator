#!/usr/bin/python

from roslib import stack_manifest
from jobs_common import *
from apt_parser import parse_apt
import sys
import os
import optparse 
import subprocess
import traceback


def main():
    # global try
    try:
        print "Starting run_auto_stack_devel script"

        # parse command line options
        print "Parsing command line options"
        (options, args) = get_options(['stack', 'rosdistro'], ['repeat', 'source-only'])
        if not options:
            return -1
        if len(options.stack) > 1:
            print "You can only provide one stack at a time"
            return -1
        options.stack = options.stack[0]
        print "parsed options: %s"%str(options)

        # set environment
        print "Setting up environment"
        env = get_environment()
        if options.source_only or options.stack == 'ros':
            ros_path = env['WORKSPACE']
        else:
            ros_path = '/opt/ros/%s'%options.rosdistro
        print "Working in %s"%ros_path
        env['ROS_PACKAGE_PATH'] = '%s:%s'%(env['WORKSPACE'], ros_path)
        env['ROS_ROOT'] = '%s/ros'%ros_path
        env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'
        env['PATH'] = '%s/ros/bin:%s'%(ros_path, os.getenv('PATH'))
        stack_dir = env['WORKSPACE']+'/'+options.stack
        print("Environment set to %s"%str(env))

        # Parse distro file
        rosdistro_obj = rosdistro.Distro(get_rosdistro_file(options.rosdistro))
        print 'Operating on ROS distro %s'%rosdistro_obj.release_name

        # get all stack dependencies of the stack we're testing
        depends = []
        stack_xml = '%s/stack.xml'%stack_dir
        call('ls %s'%stack_xml, env, 'Checking if stack %s contains "stack.xml" file'%options.stack)
        with open(stack_xml) as stack_file:
            depends_one = [str(d) for d in stack_manifest.parse(stack_file.read()).depends]  # convert to list
            print 'Dependencies of stack %s: %s'%(options.stack, str(depends_one))
            for d in depends_one:
                if not d == options.stack and not d in depends:
                    print 'Adding dependencies of stack %s'%d
                    get_depends_all(rosdistro_obj, d, depends)
                    print 'Resulting total dependencies: %s'%str(depends)

        if len(depends) > 0:
            if not options.source_only:
                # check if Debian packages of stack exist
                (arch, ubuntudistro) = get_sys_info()
                print "Parsing apt repository configuration file to get stack dependencies, for %s machine running %s"%(arch, ubuntudistro)
                apt_deps = parse_apt(ubuntudistro, arch, options.rosdistro)
                for d in depends:
                    if not apt_deps.has_debian_package(d):
                        print "Stack %s does not have Debian package yet. Stopping this test." %d
                        generate_email("Stack %s does not have Debian package yet. Stopping this test."%d, env)
                        return 0

                # Install Debian packages of stack dependencies
                print 'Installing debian packages of stack dependencies from stacks %s'%str(options.stack)
                call('sudo apt-get update', env)
                print 'Installing debian packages of "%s" dependencies: %s'%(options.stack, str(depends))
                call('sudo apt-get install %s --yes'%(stacks_to_debs(depends, options.rosdistro)), env)
            else:
                # Install stack dependencies from source
                print 'Installing stack dependencies from source'
                rosinstall = stacks_to_rosinstall(depends, rosdistro_obj.released_stacks, 'release-tar')
                print 'Using rosinstall yaml: %s'%rosinstall
                rosinstall_file = '%s.rosinstall'%options.stack
                with open(rosinstall_file, 'w') as f:
                    f.write(rosinstall)
                call('rosinstall --delete-changed-uris --rosdep-yes %s %s'%(env['WORKSPACE'], rosinstall_file), env,
                     'Install the stack dependencies from source.')
        else:
            print 'Stack %s does not have any dependencies, not installing anything now'%str(options.stack)

        # Install system dependencies of stack itself
        print 'Installing system dependencies of stack %s'%options.stack
        call('rosmake rosdep', env)
        call('rosdep install -y %s'%options.stack, env,
             'Install system dependencies of stack %s'%options.stack)

        # Start Hudson Helper
        print 'Running Hudson Helper in folder %s'%stack_dir
        res = 0
        test_results = env['ROS_TEST_RESULTS_DIR']
        for r in range(0, options.repeat+1):
            env['ROS_TEST_RESULTS_DIR'] = test_results + '/run_'+str(r)
            #res_one = subprocess.call(('./hudson_helper --dir-test %s build'%stack_dir).split(' '), env=env)
            res_one = subprocess.call(('./hudson_helper --pkg-test %s build'%options.stack).split(' '), env=env)
            if res_one != 0:
                res = res_one
        return res

    # global except
    except Exception, ex:
        print "Global exception caught. Generating email with exception text %s"%str(ex)
        generate_email("%s. Check the console output for test failure details."%str(ex), env)
        traceback.print_exc(file=sys.stdout)
        raise ex


if __name__ == '__main__':
    try:
        res = main()
        sys.exit( res )
    except Exception, ex:
        sys.exit(-1)





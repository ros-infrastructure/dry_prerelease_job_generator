#!/usr/bin/python

from job_generation.jobs_common import *
import sys
import os
import optparse 
import subprocess
import traceback

import rospkg
import rospkg.distro

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
        distro_name = options.rosdistro
        print "parsed options: %s"%str(options)

        # set environment
        print "Setting up environment"
        env = get_environment()
        stack_dir = env['WORKSPACE']+'/'+options.stack
        env['ROS_PACKAGE_PATH'] = os.pathsep.join([env['ROS_PACKAGE_PATH'], stack_dir])
        print("Environment set to %s"%str(env))

        # Parse distro file
        distro_obj = rospkg.distro.load_distro(rospkg.distro.distro_uri(distro_name))
        print 'Operating on ROS distro %s'%distro_obj.release_name

        # get all stack dependencies of the stack we're testing
        depends = []
        rosstack = rospkg.RosStack(ros_paths=[stack_dir])
        depends_one = rosstack.get_depends(options.stack, implicit=False)
        print 'Dependencies of stack %s: %s'%(options.stack, str(depends_one))
        for d in depends_one:
            if not d == options.stack and not d in depends:
                print 'Adding dependencies of stack %s'%d
                get_depends_all(distro_obj, d, depends)
                print 'Resulting total dependencies: %s'%str(depends)

        if len(depends) > 0:
            if not options.source_only:
                # Install Debian packages of stack dependencies
                print 'Installing debian packages of stack dependencies from stacks %s'%str(options.stack)
                call('sudo apt-get update', env)
                print 'Installing debian packages of "%s" dependencies: %s'%(options.stack, str(depends))
                res = call('sudo apt-get install %s --yes'%(stacks_to_debs(depends, distro_name)), env, ignore_fail=True)
                if res != 0:
                    generate_email('Not all dependencies of stack %s have a Debian package. Skipping this devel build'%str(options.stack), env)
                    sys.exit(0)  # return success
            else:
                # Install stack dependencies from source
                print 'Installing stack dependencies from source'
                rosinstall = stacks_to_rosinstall(depends, distro_obj.released_stacks, 'release-tar')
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





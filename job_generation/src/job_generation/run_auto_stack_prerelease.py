#!/usr/bin/python

STACK_DIR = 'stack_overlay'
DEPENDS_DIR = 'depends_overlay'
DEPENDS_ON_DIR = 'depends_on_overlay'


import roslib; roslib.load_manifest("job_generation")
from roslib import stack_manifest
import rosdistro
from jobs_common import *
from apt_parser import parse_apt
import sys
import os
import optparse 
import subprocess
import traceback


def remove(list1, list2):
    for l in list2:
        if l in list1:
            list1.remove(l)


def main():
    # global try
    try:

        # parse command line options
        (options, args) = get_options(['stack', 'rosdistro'], ['repeat', 'source-only'])
        if not options:
            return -1

        # set environment
        print "Setting up environment"
        env = get_environment()
        env['ROS_PACKAGE_PATH'] = '%s:%s:%s:/opt/ros/%s/stacks'%(env['INSTALL_DIR']+'/'+STACK_DIR,
                                                                 env['INSTALL_DIR']+'/'+DEPENDS_DIR,
                                                                 env['INSTALL_DIR']+'/'+DEPENDS_ON_DIR,
                                                                 options.rosdistro)
        if 'ros' in options.stack:
            env['ROS_ROOT'] = env['INSTALL_DIR']+'/'+STACK_DIR+'/ros'
            print "We're building ROS, so setting the ROS_ROOT to %s"%(env['ROS_ROOT'])
        else:
            env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
        env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'
        env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])
        print "Environment set to %s"%str(env)

        # Parse distro file
        rosdistro_obj = rosdistro.Distro(get_rosdistro_file(options.rosdistro))
        print 'Operating on ROS distro %s'%rosdistro_obj.release_name


        # Install the stacks to test from source
        print 'Installing the stacks to test from source'
        rosinstall = ''
        for stack in options.stack:
            rosinstall += stack_to_rosinstall(rosdistro_obj.stacks[stack], 'devel')
        rosinstall_file = '%s.rosinstall'%STACK_DIR
        print 'Generating rosinstall file [%s]'%(rosinstall_file)
        print 'Contents:\n\n'+rosinstall+'\n\n'
        with open(rosinstall_file, 'w') as f:
            f.write(rosinstall)
            print 'rosinstall file [%s] generated'%(rosinstall_file)
        call('rosinstall --rosdep-yes %s /opt/ros/%s %s'%(STACK_DIR, options.rosdistro, rosinstall_file), env,
             'Install the stacks to test from source.')


        # get all stack dependencies of stacks we're testing
        print "Computing dependencies of stacks we're testing"
        depends_all = []
        for stack in options.stack:    
            stack_xml = '%s/%s/stack.xml'%(STACK_DIR, stack)
            call('ls %s'%stack_xml, env, 'Checking if stack %s contains "stack.xml" file'%stack)
            with open(stack_xml) as stack_file:
                depends_one = [str(d) for d in stack_manifest.parse(stack_file.read()).depends]  # convert to list
                print 'Dependencies of stack %s: %s'%(stack, str(depends_one))
                for d in depends_one:
                    if not d in options.stack and not d in depends_all:
                        print 'Adding dependencies of stack %s'%d
                        get_depends_all(rosdistro_obj, d, depends_all)
                        print 'Resulting total dependencies of all stacks that get tested: %s'%str(depends_all)

        if len(depends_all) > 0:
            if options.source_only:
                # Install dependencies from source
                print 'Installing stack dependencies from source'
                rosinstall = stacks_to_rosinstall(depends_all, rosdistro_obj.released_stacks, 'release-tar')
                rosinstall_file = '%s.rosinstall'%DEPENDS_DIR
                print 'Generating rosinstall file [%s]'%(rosinstall_file)
                print 'Contents:\n\n'+rosinstall+'\n\n'
                with open(rosinstall_file, 'w') as f:
                    f.write(rosinstall)
                    print 'rosinstall file [%s] generated'%(rosinstall_file)
                call('rosinstall --rosdep-yes %s /opt/ros/%s %s'%(DEPENDS_DIR, options.rosdistro, rosinstall_file), env,
                     'Install the stack dependencies from source.')
            else:
                # Install Debian packages of stack dependencies
                print 'Installing debian packages of "%s" dependencies: %s'%(stack, str(depends_all))
                call('sudo apt-get update', env)
                call('sudo apt-get install %s --yes'%(stacks_to_debs(depends_all, options.rosdistro)), env)
        else:
            print 'Stack(s) %s do(es) not have any dependencies, not installing anything now'%str(options.stack)


        # Install system dependencies of stacks re're testing
        print "Installing system dependencies of stacks we're testing"
        call('rosmake rosdep', env)
        for stack in options.stack:
            call('rosdep install -y %s'%stack, env,
                 'Install system dependencies of stack %s'%stack)


        # Run hudson helper for stacks only
        print "Running Hudson Helper for stacks we're testing"
        res = 0
        for r in range(0, int(options.repeat)+1):
            env['ROS_TEST_RESULTS_DIR'] = env['ROS_TEST_RESULTS_DIR'] + '/' + STACK_DIR + '_run_' + str(r)
            helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%STACK_DIR).split(' '), env=env)
            helper.communicate()
            if helper.returncode != 0:
                res = helper.returncode
        if res != 0:
            return res


        # parse debian repository configuration file to get stack dependencies
        (arch, ubuntudistro) = get_sys_info()
        print "Parsing apt repository configuration file to get stack dependencies, for %s machine running %s"%(arch, ubuntudistro)
        apt_deps = parse_apt(ubuntudistro, arch, options.rosdistro)
        if not apt_deps.has_debian_package(options.stack):
            print "Stack does not yet have a Debian package. No need to test dependenies"
            return 0

        # all stacks that depends on the tested stacks, excluding the tested stacks.
        depends_on_all = apt_deps.depends_on_all(options.stack)
        remove(depends_on_all, options.stack)

        # if tested stacks are all in a variant, then only test stacks that are also in a variant
        variant_stacks = []
        for name, v in rosdistro_obj.variants.iteritems():
            variant_stacks = variant_stacks + v.stack_names
        all_in_variant = True
        for s in options.stack:
            if not s in variant_stacks:
                all_in_variant = False
        if all_in_variant:
            print "Limiting test to stacks that are in a variant"
            for s in depends_on_all:
                if not s in variant_stacks:
                    depends_on_all.remove(s)

        # all stack dependencies of above stack list, except for the test stack dependencies
        depends_all_depends_on_all = apt_deps.depends_all(depends_on_all)
        remove(depends_all_depends_on_all, options.stack)
        remove(depends_all_depends_on_all, depends_all)


        # Install dependencies of depends_on_all stacks, excluding dependencies of test stacks.
        if len(depends_all_depends_on_all) > 0:
            print "Install dependencies of depends_on_all stacks, excluding dependencies of test stacks."
            if not options.source_only:
                # Install Debian packages of 'depends_all_depends_on_all' list
                print 'Installing Debian package of %s'%str(depends_all_depends_on_all)
                call('sudo apt-get install %s --yes'%(stacks_to_debs(depends_all_depends_on_all, options.rosdistro)), env)
            else:
                # Install source of 'depends_all_depends_on_all' list
                print 'Installing source of %s'%str(depends_all_depends_on_all)
                rosinstall = stacks_to_rosinstall(depends_all_depends_on_all, rosdistro_obj.released_stacks, 'release-tar')
                rosinstall_file = '%s_depends_all_depends_on_all.rosinstall'%DEPENDS_ON_DIR
                print 'Generating rosinstall file [%s]'%(rosinstall_file)
                print 'Contents:\n\n'+rosinstall+'\n\n'
                with open(rosinstall_file, 'w') as f:
                    f.write(rosinstall)
                    print 'rosinstall file [%s] generated'%(rosinstall_file)
                call('rosinstall --rosdep-yes %s /opt/ros/%s %s %s'%(DEPENDS_ON_DIR, options.rosdistro, STACK_DIR, rosinstall_file), env,
                     'Install dependencies of depends_on_all stacks, excluding dependencies of test stacks.')
        else:
            print "No dependencies of depends_on_all stacks"
            

        # Install all stacks that depend on this stack from source
        if len(depends_on_all) > 0:
            print 'Installing depends_on_all stacks from source: %s'%str(depends_on_all)
            rosinstall = stacks_to_rosinstall(depends_on_all, rosdistro_obj.released_stacks, 'release-tar')
            rosinstall_file = '%s.rosinstall'%DEPENDS_ON_DIR
            print 'Generating rosinstall file [%s]'%(rosinstall_file)
            print 'Contents:\n\n'+rosinstall+'\n\n'
            with open(rosinstall_file, 'w') as f:
                f.write(rosinstall)
                print 'rosinstall file [%s] generated'%(rosinstall_file)
            call('rosinstall --rosdep-yes %s /opt/ros/%s %s %s'%(DEPENDS_ON_DIR, options.rosdistro, STACK_DIR, rosinstall_file), env,
                 'Install the stacks that depend on the stacks that are getting tested from source.')

            # Run hudson helper for all stacks
            print 'Running Hudson Helper'
            env['ROS_TEST_RESULTS_DIR'] = env['ROS_TEST_RESULTS_DIR'] + '/' + DEPENDS_ON_DIR
            helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%DEPENDS_ON_DIR).split(' '), env=env)
            helper.communicate()
            return helper.returncode
        else:
            print "No stacks depends on this stack. Tests finished"


    # global except
    except Exception, ex:
        print "Global exception caught. Generating email"
        generate_email("%s. Check the console output for test failure details."%ex, env)
        traceback.print_exc(file=sys.stdout)
        raise ex


if __name__ == '__main__':
    try:
        res = main()
        sys.exit( res )
    except Exception, ex:
        sys.exit(-1)







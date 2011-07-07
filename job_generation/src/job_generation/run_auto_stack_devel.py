#!/usr/bin/python

from roslib import stack_manifest
from jobs_common import *
import sys
import os
import optparse 
import subprocess
import traceback

#####################
# Copy of roslib.stacks code in order to be backwards compatible

from roslib.rosenv import ROS_ROOT, ROS_PACKAGE_PATH
import roslib.packages
import roslib.stacks
STACK_FILE = roslib.stacks.STACK_FILE

def get_stack_dir(stack, env=None):
    """
    Get the directory of a ROS stack. This will initialize an internal
    cache and return cached results if possible.
    
    This routine is not thread-safe to os.environ changes.
    
    @param env: override environment variables
    @type  env: {str: str}
    @param stack: name of ROS stack to locate on disk
    @type  stack: str
    @return: directory of stack.
    @rtype: str
    @raise InvalidROSStackException: if stack cannot be located.
    """
    
    # it's possible to get incorrect results from this cache
    # implementation by manipulating the environment and calling this
    # from multiple threads.  as that is an unusual use case and would
    # require a slower implmentation, it's not supported. the
    # interpretation of this routine is get_stack_dir for the
    # environment this process was launched in.
    global _dir_cache_marker 

    if env is None:
        env = os.environ
    if stack in _dir_cache:
        ros_root = env[ROS_ROOT]
        ros_package_path = env.get(ROS_PACKAGE_PATH, '')

        # we don't attempt to be thread-safe to environment changes,
        # however we do need to be threadsafe to cache invalidation.
        try:
            if _dir_cache_marker == (ros_root, ros_package_path):
                d = _dir_cache[stack]
                if os.path.isfile(os.path.join(d, STACK_FILE)):
                    return d
                else:
                    # invalidate the cache
                    _dir_cache_marker = None
                    _dir_cache.clear()
        except KeyError:
            pass
    _update_stack_cache(env=env) #update cache
    val = _dir_cache.get(stack, None)
    if val is None:
        raise roslib.stacks.InvalidROSStackException("Cannot location installation of stack %s. ROS_ROOT[%s] ROS_PACKAGE_PATH[%s]"%(stack, env[ROS_ROOT], env.get(ROS_PACKAGE_PATH, '')))
    return val

# rosstack directory cache
_dir_cache = {}
# stores ROS_ROOT, ROS_PACKAGE_PATH of _dir_cache
_dir_cache_marker = None

def _update_stack_cache(force=False, env=None):
    """
    Update _dir_cache if environment has changed since last cache build.
    
    @param env: override environment variables
    @type  env: {str: str}
    @param force: force cache rebuild regardless of environment variables
    @type  force: bool
    """
    global _dir_cache_marker
    if env is None:
        env = os.environ
    ros_root = env[ROS_ROOT]
    ros_package_path = env.get(ROS_PACKAGE_PATH, '')
    
    if _dir_cache_marker == (ros_root, ros_package_path):
        return
    _dir_cache.clear()
    _dir_cache_marker = ros_root, ros_package_path

    pkg_dirs = roslib.packages.get_package_paths(env=env)
    # ros is assumed to be at ROS_ROOT
    if os.path.exists(os.path.join(ros_root, 'stack.xml')):
        _dir_cache['ros'] = ros_root
        pkg_dirs.remove(ros_root)

    # pass in accumulated stacks list to each call. This ensures
    # precedence (i.e. that stacks first on pkg_dirs path win). 
    stacks = []
    for pkg_root in pkg_dirs:
        # list_stacks_by_path will append list into stacks, so that
        # each call accumulates in it.
        list_stacks_by_path(pkg_root, stacks, cache=_dir_cache)
    
def list_stacks_by_path(path, stacks=None, cache=None):
    """
    List ROS stacks within the specified path.

    Optionally, a cache dictionary can be provided, which will be
    updated with the stack->path mappings. list_stacks_by_path() does
    NOT returned cached results -- it only updates the cache.
    
    @param path: path to list stacks in
    @type  path: str
    @param stacks: list of stacks to append to. If stack is
      already present in stacks, it will be ignored.
    @type  stacks: [str]
    @param cache: (optional) stack path cache to update. Maps stack name to directory path.
    @type  cache: {str: str}
    @return: complete list of stack names in ROS environment. Same as stacks parameter.
    @rtype: [str]
    """
    if stacks is None:
        stacks = []
    MANIFEST_FILE = roslib.packages.MANIFEST_FILE
    basename = os.path.basename
    for d, dirs, files in os.walk(path, topdown=True):
        if STACK_FILE in files:
            stack = basename(d)
            if stack not in stacks:
                stacks.append(stack)
                if cache is not None:
                    cache[stack] = d
            del dirs[:]
            continue #leaf
        elif MANIFEST_FILE in files:
            del dirs[:]
            continue #leaf     
        elif 'rospack_nosubdirs' in files:
            del dirs[:]
            continue  #leaf
        # remove hidden dirs (esp. .svn/.git)
        [dirs.remove(di) for di in dirs if di[0] == '.']
        for sub_d in dirs:
            # followlinks=True only available in Python 2.6, so we
            # have to implement manually
            sub_p = os.path.join(d, sub_d)
            if os.path.islink(sub_p):
                stacks.extend(list_stacks_by_path(sub_p, cache=cache))
    return stacks

#####################

def main():
    # global try
    try:
        print "Starting run_auto_stack_devel script"

        # parse command line options
        print "Parsing command line options"
        (options, args) = get_options(['stack', 'rosdistro'], ['repeat'])
        if not options:
            return -1
        if len(options.stack) > 1:
            print "You can only provide one stack at a time"
            return -1
        options.stack = options.stack[0]

        # set environment
        print "Setting up environment"
        env = get_environment()
        env['ROS_PACKAGE_PATH'] = '%s:/opt/ros/%s/stacks'%(os.environ['WORKSPACE'], options.rosdistro)
        if options.stack == 'ros':
            env['ROS_ROOT'] = env['WORKSPACE']+'/ros'
            print "Changing ROS_ROOT and PYTHONPATH because we are building ROS"
        else:
            env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
        env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'

        env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])
        stack_dir = get_stack_dir(options.stack, env=env)
        #stack_dir = env['WORKSPACE']+'/'+options.stack

        # Install Debian packages of stack dependencies
        print "Installing Debian packages of stack dependencies"
        call('sudo apt-get update', env)
        with open('%s/stack.xml'%stack_dir) as stack_file:
            depends = stack_manifest.parse(stack_file.read()).depends

        if len(depends) != 0:
            print 'Installing debian packages of stack dependencies: %s'%str(depends)        
            call('sudo apt-get install %s --yes'%(stacks_to_debs(depends, options.rosdistro)), env,
                 'Installing dependencies of stack "%s": %s'%(options.stack, str(depends)))

        # Install system dependencies
        print 'Installing system dependencies'
        call('rosmake rosdep', env)
        call('rosdep install -y %s'%options.stack, env,
             'Installing system dependencies of stack %s'%options.stack)


        # Start Hudson Helper
        print 'Running Hudson Helper'
        res = 0
        for r in range(0, options.repeat+1):
            env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR']+'/run_'+str(r)
            res_one = subprocess.call(('./hudson_helper --dir-test %s build'%stack_dir).split(' '), env=env)
            if res_one != 0:
                res = res_one
        return res

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





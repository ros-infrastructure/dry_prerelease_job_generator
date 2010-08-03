#!/usr/bin/env python

"""
This script copies release tags from one distro to another, e.g.
tags/latest to tag/cturtle
"""
import roslib; roslib.load_manifest('release')
NAME="copy_distro.py"

import sys
import os
import os.path
import traceback

import roslib.scriptutil

from roslib.vcs.svn import SVNClient
from roslib.distro import Distro, DistroException

print "WARNING: this script requires ROS 1.1+"

import release

def main():
    try:
        from optparse import OptionParser
        parser = OptionParser(usage="usage: %prog <from-release> <to-release>", prog=NAME)
        options, args = parser.parse_args()
        if len(args) != 2:
            parser.error("""You must specify: 
 * from release name
 * to release name""")
        from_release_name = args[0]
        to_release_name = args[1]

        from_distro = Distro("http://ros.org/distros/%s.rosdistro"%from_release_name)
        to_distro = Distro("http://ros.org/distros/%s.rosdistro"%to_release_name)

        cmds = []
        # for every stack in from, copy to the new distro
        for stack_name, stack in from_distro.stacks.iteritems():
            #if not stack_name in ['navigation', 'navigation_experimental', 'pr2_ethercat_drivers', 'pr2_robot', 'vision_opencv', 'web_interface']:
            #    continue
            print "checking", stack_name
            from_uri = stack.distro_svn
            to_uri = to_distro.stacks[stack_name].distro_svn
            if not release.svn_url_exists(to_uri):
                cmds.append(['svn', 'cp', '-m', 'copying from %s to %s'%(from_release_name, to_release_name), from_uri, to_uri])
            else:
                cmds.append(['svn', 'rm', '-m', "resyncing from latest", to_uri]) 
                cmds.append(['svn', 'cp', '-m', 'copying from %s to %s'%(from_release_name, to_release_name), from_uri, to_uri])                
        
        if not hasattr(roslib.scriptutil, 'ask_and_call'):
            print >> sys.stderr, "this script only works with ROS 1.1+"
            sys.exit(1)

        roslib.scriptutil.ask_and_call(cmds)

    except Exception, e:
        traceback.print_exc()
        print >> sys.stderr, "ERROR: %s"%str(e)
        sys.exit(1)

if __name__ == '__main__':
    main()

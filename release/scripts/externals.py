#!/usr/bin/env python

import roslib; roslib.load_manifest('release')
NAME="externals.py"

import sys
import os
import os.path
import traceback

import roslib.scriptutil

from roslib2.vcs.svn import SVNClient
from roslib2.distro import Distro, DistroException

print "WARNING: this script requires ROS 1.1+"

def main():
    try:
        from optparse import OptionParser
        parser = OptionParser(usage="usage: %prog <release>\n\tUse 'rosdoc' as the release name to general rosdoc external", prog=NAME)
        options, args = parser.parse_args()
        if len(args) != 1:
            parser.error("""You must specify: 
 * release name""")
        release_name = args[0]

        rosdoc_external = release_name == 'rosdoc'
        if rosdoc_external:
            # general based on the cturtle list of stacks
            release_name = 'cturtle'
            
        distro = Distro("http://ros.org/distros/%s.rosdistro"%release_name)

        # create text for externals
        externals = []
        tmpl = "%(stack_name)s %(uri)s\n"

        # create external for each variant
        for name, variant in distro.variants.iteritems():
            svn_external = ''
            for stack_name in variant.stack_names:
                if stack_name == 'ros':
                    continue
                stack = distro.stacks[stack_name]
                uri = stack.distro_svn
                svn_external += tmpl%locals()
            externals.append((name, svn_external))

        # create an all external for everything
        #  - also create the rosdoc external just in case we need it
        all = ''
        rosdoc_all = ''
        for stack_name, stack in distro.stacks.iteritems():
            if stack_name == 'ros':
                continue
            uri = stack.distro_svn
            all += tmpl%locals()
            
            uri = stack.dev_svn
            rosdoc_all += tmpl%locals()
            
        externals.append(('all', all))
        
        if not hasattr(roslib.scriptutil, 'ask_and_call'):
            print >> sys.stderr, "this script only works with ROS 1.1+"
            sys.exit(1)

        if rosdoc_external:
            external_uri = "https://code.ros.org/svn/wg-ros-pkg/externals/rosdoc"
            rosdoc_all += """ros-pkg-trunk https://code.ros.org/svn/ros-pkg/trunk
wg-ros-pkg-trunk https://code.ros.org/svn/wg-ros-pkg/trunk
"""
            externals = (('rosdoc', rosdoc_all),)
        else:
            external_uri = "https://code.ros.org/svn/wg-ros-pkg/externals/distro/%(release_name)s/%(name)s"
            
        svn = SVNClient('.')
        for name, svn_external in externals:
            cmds = []
            url = external_uri%locals()
            if not svn.exists(url):
                cmds.append(['svn','mkdir','-m', 'creating new external variant', '--parents', external_uri%locals()])
            cmds.append(['svnmucc','propset','svn:externals','-m', 'auto-updating external', svn_external, external_uri%locals()])
            roslib.scriptutil.ask_and_call(cmds)

    except Exception, e:
        traceback.print_exc()
        print >> sys.stderr, "ERROR: %s"%str(e)
        sys.exit(1)

if __name__ == '__main__':
    main()

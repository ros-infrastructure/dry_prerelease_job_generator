#!/usr/bin/env python

import roslib; roslib.load_manifest('release')
NAME="externals.py"

import sys
import os
import os.path
import traceback

import roslib.scriptutil

from vcstools.svn import SVNClient
from rosdistro import Distro, DistroException

print "WARNING: this script requires ROS 1.1+"

def guess_repo(uri):
    """
    For the rosdoc external, we want to bin each URL by the repository it belongs to
    """
    if 'code.ros.org/svn/ros/' in uri:
        repo = 'ros'
    elif 'code.ros.org/svn/ros-pkg/' in uri:
        repo = 'ros-pkg'                
    elif 'code.ros.org/svn/wg-ros-pkg/' in uri:
        repo = 'wg-ros-pkg'
    else:
        print >> sys.stderr, "warning: unknown repo %s"%(uri)
    return repo

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
            # general based on the unstable list of stacks
            release_name = 'unstable'
            
        #distro = Distro("http://ros.org/distros/%s.rosdistro"%release_name)
        # now loading from direct svn copy
        distro = Distro("https://code.ros.org/svn/release/trunk/distros/%s.rosdistro"%release_name)
        
        # create text for externals
        externals = []
        tmpl = "%(stack_name)s %(uri)s\n"

        # create external for each variant
        for name, variant in distro.variants.iteritems():
            svn_external = ''
            # don't configure variants for external variants just yet
            if name in ['cassowary']:
                continue
            for stack_name in variant.stack_names:
                if stack_name == 'ros':
                    continue
                stack = distro.stacks[stack_name]
                uri = stack.distro_svn
                # TODO: convert to VCS config
                
                # Filter by code.ros.org as we don't configure
                # externals for thirdparty stacks
                if not uri or not 'code.ros.org' in uri:
                    continue
                svn_external += tmpl%locals()
            externals.append((name, svn_external))

        # create an all external for everything
        #  - also create the rosdoc external just in case we need it
        all = ''
        rosdoc_all = {
            'ros': '',
            'ros-pkg': '',
            'wg-ros-pkg': '',            
            }
        for stack_name, stack in distro.stacks.iteritems():
            if stack_name == 'ros':
                continue
            uri = stack.distro_svn
            if not uri or not 'code.ros.org' in uri:
                continue
            
            all += tmpl%locals()
            
            uri = stack.dev_svn
            if not uri:
                continue

            # for rosdoc external only
            repo = guess_repo(uri)
            if repo:
                rosdoc_all[repo] += tmpl%locals()
            
        externals.append(('all', all))
        
        if not hasattr(roslib.scriptutil, 'ask_and_call'):
            print >> sys.stderr, "this script only works with ROS 1.1+"
            sys.exit(1)

        if rosdoc_external:
            rosdoc_all['wg-ros-pkg'] += """wg-ros-pkg-diamondback https://code.ros.org/svn/wg-ros-pkg/branches/trunk_diamondback
wg-ros-pkg-electric https://code.ros.org/svn/wg-ros-pkg/branches/trunk_electric
wg-ros-pkg-cturtle https://code.ros.org/svn/wg-ros-pkg/branches/trunk_cturtle
"""
            rosdoc_all['ros-pkg'] += """ros-pkg-trunk https://code.ros.org/svn/ros-pkg/trunk
ros-pkg-cturtle https://code.ros.org/svn/ros-pkg/branches/trunk_cturtle
"""
            rosdoc_all['ros'] += """ros_experimental https://code.ros.org/svn/ros/stacks/ros_experimental/trunk
"""
            
            externals = (('rosdoc', rosdoc_all),)

            for repo, external in rosdoc_all.iteritems():
                uri = "https://code.ros.org/svn/%s/externals/rosdoc_rosorg"%(repo)
                update_external(uri, external)
            
        else:
            external_uri = "https://code.ros.org/svn/wg-ros-pkg/externals/distro/%(release_name)s/%(name)s"
            for name, svn_external in externals:
                update_external(external_uri%locals(), svn_external)

    except Exception, e:
        traceback.print_exc()
        print >> sys.stderr, "ERROR: %s"%str(e)
        sys.exit(1)

def update_external(url, svn_external):
    cmds = []
    svn = SVNClient('.')
    if not svn.exists(url):
        cmds.append(['svn','mkdir','-m', 'creating new external variant', '--parents', url])
    cmds.append(['svnmucc','propset','svn:externals','-m', 'auto-updating external', svn_external, url])
    roslib.scriptutil.ask_and_call(cmds)
    
    

if __name__ == '__main__':
    main()

#!/usr/bin/env python

# source code refers to 'stacks', but this can work with apps as well
from __future__ import with_statement
PKG = 'release'
import roslib; roslib.load_manifest(PKG)
NAME="rosinstalls.py"

import sys
import os
import os.path
from subprocess import Popen, PIPE, call, check_call
import traceback

import roslib.scriptutil
import roslib.stacks
from roslib.distro import Distro, DistroException

print "WARNING: this script requires ROS *trunk*"

try:
    import yaml
except ImportError:
    print >> sys.stderr, "python-yaml not installed, cannot proceed"
    sys.exit(1)

def main():
    try:
        from optparse import OptionParser
        parser = OptionParser(usage="usage: %prog <release>", prog=NAME)
        options, args = parser.parse_args()
        if len(args) != 1:
            parser.error("""You must specify: 
 * release name""")
        release_name = args[0]
        if release_name.endswith('.rosdistro'):
            release_name = release_name[:-len('.rosdistro')]

        print "release name", release_name
        
        # load in an expand URIs for rosinstalls
        distro = Distro("http://ros.org/distros/%s.rosdistro"%release_name)
        checkouts = {}
        for stack_name, stack in distro.stacks.iteritems():
            checkouts[stack_name] = stack.distro_svn

        # create text for rosinstalls
        variant_rosinstalls = []
        tmpl = """- svn:
    uri: %(uri)s
    local-name: %(local_name)s
"""

        variant_stacks = {}
        variant_stacks_extended = {}
        # create the ros-only variant
        local_name = 'ros'
        uri = checkouts['ros']
        variant_rosinstalls.append(('rosinstall/%s_ros.rosinstall'%release_name,tmpl%locals()))

        pkg_dir = roslib.packages.get_pkg_dir(PKG)
        rosinstall_dir = os.path.join(pkg_dir, 'rosinstalls')

        for name, variant in distro.variants.iteritems():
            variant_props = variant.props

            # the variant class computes the extended list, we also need the unextended list
            variant_stacks[name] = variant_props['stacks']
            variant_stacks_extended[name] = variant.stack_names
                
            # create two rosinstalls per variant: 'extended' (non-overlay) and normal (overlay)
            text = ''

            local_name = 'ros'
            uri = checkouts['ros']
            text_extended = tmpl%locals()

            for stack_name in sorted(variant_stacks[name]):
                uri = checkouts[stack_name]
                if stack_name == 'ros':
                    continue
                else:
                    local_name = "stacks/%s"%stack_name
                text += tmpl%locals()
                
            for stack_name in sorted(variant_stacks_extended[name]):
                uri = checkouts[stack_name]
                if stack_name == 'ros':
                    continue
                else:
                    local_name = "stacks/%s"%stack_name
                text_extended += tmpl%locals()

            # create non-overlay rosinstall
            filename = os.path.join(rosinstall_dir, '%s_%s.rosinstall'%(release_name, name))
            variant_rosinstalls.append((filename, text_extended))

            # create variant overlay
            filename = os.path.join(rosinstall_dir, '%s_%s_overlay.rosinstall'%(release_name, name))
            variant_rosinstalls.append((filename, text))

        # output rosinstalls
        for filename, text in variant_rosinstalls:
            d = os.path.dirname(filename)
            if not os.path.exists(d):
                os.makedirs(d)
            with open(filename,'w') as f:
                f.write(text)
            copy_to_server(filename)

    except Exception, e:
        traceback.print_exc()
        print >> sys.stderr, "ERROR: %s"%str(e)
        sys.exit(1)


def copy_to_server(filename):
    try:
        dest = os.path.join('wgs32.willowgarage.com:/var/www/www.ros.org/html/rosinstalls/%s'%os.path.basename(filename))
        cmds = [['scp', filename, dest]]
        if not roslib.scriptutil.ask_and_call(cmds):    
            print "create_rosinstall will not copy the rosinstall to wgs32"
    except:
        traceback.print_exc()
        print >> sys.stderr, "COPY FAILED, please redo manually"

if __name__ == '__main__':
    main()

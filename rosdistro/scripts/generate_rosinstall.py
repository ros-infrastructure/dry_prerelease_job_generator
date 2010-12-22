#!/usr/bin/env python



# source code refers to 'stacks', but this can work with apps as well
from __future__ import with_statement
PKG = 'rosdistro'
import roslib; roslib.load_manifest(PKG)
NAME="generate_rosinstalls.py"

import sys
import os
import os.path
import traceback

import rosdistro 

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
        #distro = Distro("http://ros.org/distros/%s.rosdistro"%release_name)
        # now loading from direct svn copy
        distro = rosdistro.Distro("https://code.ros.org/svn/release/trunk/distros/%s.rosdistro"%release_name)
        
        checkouts = {}
        for stack_name, stack in distro.stacks.iteritems():
            checkouts[stack_name] = stack.distro_svn

        # create text for rosinstalls
        variant_rosinstalls = []

        variant_stacks = {}
        variant_stacks_extended = {}
        # create the ros-only variant
        local_name = 'ros'
        uri = checkouts['ros']

        pkg_dir = roslib.packages.get_pkg_dir('release_resources')
        rosinstall_dir = os.path.join(pkg_dir, 'rosinstalls')

        ri_dict = rosdistro.stack_to_rosinstall(distro.stacks['ros'], 'distro')

        filename = os.path.join(rosinstall_dir, '%s_ros.rosinstall'%(release_name))
        variant_rosinstalls.append((filename,yaml.dump(ri_dict, default_flow_style=False)))

        for name, variant in distro.variants.iteritems():

            variant_props = variant.props

            # the variant class computes the extended list, we also need the unextended list
            variant_stacks[name] = variant_props['stacks']
            variant_stacks_extended[name] = variant.stack_names
                
            # create two rosinstalls per variant: 'extended' (non-overlay) and normal (overlay)

            # create non-overlay rosinstall
            rosinstall_variant = rosdistro.extended_variant_to_rosinstall(name, distro, 'distro')
            filename = os.path.join(rosinstall_dir, '%s_%s.rosinstall'%(release_name, name))
            variant_rosinstalls.append((filename, yaml.dump(rosinstall_variant, default_flow_style=False)))

            # create variant overlay
            rosinstall_variant = rosdistro.variant_to_rosinstall(name, distro, 'distro')
            filename = os.path.join(rosinstall_dir, '%s_%s_overlay.rosinstall'%(release_name, name))
            variant_rosinstalls.append((filename, yaml.dump(rosinstall_variant, default_flow_style=False)))

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

#!/usr/bin/env python

from __future__ import with_statement
import roslib; roslib.load_manifest('rosdistro')

import sys
import os
import os.path
import traceback
import subprocess
import rosdistro 
import urllib
import yaml

def get_depends(stack):
    name = '%s-%s'%(stack.name, stack.version)
    url = urllib.urlopen('https://code.ros.org/svn/release/download/stacks/%s/%s/%s.yaml'%(stack.name, name, name))
    conf = url.read()
    if '404 Not Found' in conf:
        return []
    depends = yaml.load(conf)['depends']
    if depends:
        return depends
    else:
        return []

def get_rosdistro_file(rosdistro):
    return 'https://code.ros.org/svn/release/trunk/distros/%s.rosdistro'%rosdistro


def main():
    if len(sys.argv) != 2:
        print "Usage: variant_dependencies.py rosdistro"
        return

    # parse rosdistro file
    rosdistro_obj = rosdistro.Distro(get_rosdistro_file(sys.argv[1]))
    print 'Operating on ROS distro %s'%rosdistro_obj.release_name

    # loop through all variants
    for variant_name, variant in rosdistro_obj.variants.iteritems():
        print 'Variant %s'%variant_name
        for stack_name in variant.stack_names_explicit:
            stack = rosdistro_obj.stacks[stack_name]
            depends = get_depends(stack)
            for d in depends:
                if not d in variant.stack_names:
                    print ' - Stack %s depends on %s, which is not part of the variant'%(stack.name, d)


if __name__ == '__main__':
    main()

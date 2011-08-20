#!/usr/bin/env python

from __future__ import print_function

import roslib; roslib.load_manifest('rosdistro')

import sys
import os
import rosdistro 
import urllib2
import yaml

def get_depends(stack):
    name = '%s-%s'%(stack.name, stack.version)
    try:
        url = urllib2.urlopen('https://code.ros.org/svn/release/download/stacks/%s/%s/%s.yaml'%(stack.name, name, name))
        depends = yaml.load(url)['depends']
    except urllib2.HTTPError:
        print("failed to load depends for stack [%s]"%(stack.name), file=sys.stderr)
        return []
    except yaml.YAMLError:
        print("bad YAML data for stack [%s]"%(stack.name), file=sys.stderr)
        return []
    return depends or []

def main():
    if len(sys.argv) < 2:
        print("Usage: variant_dependencies.py <rosdistro> [variants]...")
        return

    # parse rosdistro file
    if os.path.isfile(sys.argv[1]):
        rosdistro_obj = rosdistro.Distro(sys.argv[1])
    else:
        rosdistro_obj = rosdistro.Distro(rosdistro.distro_uri(sys.argv[1]))
    print('Operating on ROS distro %s'%rosdistro_obj.release_name)

    # use all variants or user-specified set
    if len(sys.argv) > 2:
        variants = sys.argv[2:]
    else:
        variants = rosdistro_obj.variants.keys()
    # loop through all variants
    for variant_name in variants:
        try:
            variant = rosdistro_obj.variants[variant_name]
        except KeyError:
            print(sys.stderr, "No variant [%s]"%(variant_name), file=sys.stderr)
            continue
        header = True
        for stack_name in variant.stack_names_explicit:
            if not stack_name in rosdistro_obj.released_stacks:
                print('Variant %s depends on %s, which is not released'%(variant_name, stack_name))
                continue
            stack = rosdistro_obj.stacks[stack_name]
            depends = get_depends(stack)
            for d in depends:
                if not d in variant.stack_names:
                    if header:
                        print('Variant %s'%variant_name)
                        header = False
                    print(' - Stack %s depends on %s, which is not part of the variant'%(stack.name, d))

if __name__ == '__main__':
    main()

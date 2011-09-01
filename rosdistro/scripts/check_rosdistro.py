#!/usr/bin/env python

from __future__ import print_function
import roslib; roslib.load_manifest('rosdistro')

NAME='check_rosdistro.py'

import sys
import os
import urllib2
import yaml

import rosdistro 

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
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog [options] <rosdistro> [variants]...", prog=NAME)
    parser.add_option("-b", "--brief",
                      dest="brief", default=None, action="store_true",
                      help="only check parsing, don't do full validation")
    options, args = parser.parse_args()
    if not args:
        parser.error('please specify a distro')

    # parse rosdistro file
    arg0 = args[0]
    if os.path.isfile(arg0):
        rosdistro_obj = rosdistro.Distro(arg0)
    else:
        rosdistro_obj = rosdistro.Distro(rosdistro.distro_uri(arg0))

    for name, s in rosdistro_obj.stacks.iteritems():
        tmp = s.vcs_config.type
        
    print('Rosdistro file for %s parses succesfully'%rosdistro_obj.release_name)
    if options.brief:
        return
    else:
        print("Validating variants")
    
    # use all variants or user-specified set
    if len(args) > 1:
        variants = args[1:]
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

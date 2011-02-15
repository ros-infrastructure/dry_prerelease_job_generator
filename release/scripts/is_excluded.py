#!/usr/bin/env python

PKG = 'release'
NAME='is_excluded.py'
import roslib; roslib.load_manifest(PKG)

import os
import sys
import yaml
import urllib2

from rosdistro import Distro

def load_distro(distro_name):
    distro_uri = "https://code.ros.org/svn/release/trunk/distros/%s.rosdistro"%(distro_name)
    return Distro(distro_uri)

def load_excluded(distro_name):
    try:
        uri = "https://code.ros.org/svn/release/trunk/distros/%s.excludes"%(distro_name)
        return yaml.load(urllib2.urlopen(uri)) or {}
    except urllib2.HTTPError:
        # assume 404, no excludes
        return {}

def is_excluded(stack_name, distro_name, os_platform, os_arch):
    try:
        d = load_distro(distro_name)
    except:
        raise Exception("cannot load distro [%s]"%(distro_name))
    e = load_excluded(distro_name)
    if type(e) == dict:
        if stack_name in e:
            key = "%s-%s"%(os_platform, os_arch)
            if key in e[stack_name]:
                return True
    return False
    
def ex_main():
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog <stack> <release-name> <os-platform> <os-arch>", prog=NAME)
    options, args = parser.parse_args()
    stack_name, distro_name, os_platform, os_arch = args

    if is_excluded(stack_name, distro_name, os_platform, os_arch):
        print "excluded"
        sys.exit(1)
    else:
        print "not excluded"

if __name__ == '__main__':
    ex_main()

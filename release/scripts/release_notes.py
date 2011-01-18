#!/usr/bin/env python
from __future__ import with_statement

PKG = 'release'
import roslib; roslib.load_manifest(PKG)

import os
import sys

import roslib.packages

from rosdistro import Distro
from rosdeb import get_repo_version, get_stack_version, load_Packages


# hack until I refactor config into actual importable module
d = roslib.packages.get_pkg_dir('rosdeb')
sys.path.append(os.path.join(d, 'scripts'))
from list_missing import ROS_REPO, SHADOW_FIXED_REPO, load_distro

def load_distro(distro_name):
    distro_uri = "https://code.ros.org/svn/release/trunk/distros/%s.rosdistro"%(distro_name)
    return Distro(distro_uri)

def create_notes(released):
    s = ', '.join(["%s %s"%(stack, version) for stack, version in released.iteritems()])
    s += "\n"

    keys = sorted(released.iterkeys())
    for stack in keys:
        version = released[stack]
        stack_safe = stack.replace('_', '\_')
        s += " * [%(stack_safe)s](http://ros.org/wiki/%(stack)s/ChangeList) %(version)s\n"%locals()

    s += ','.join(keys)
    return s


def load_additional():
    d = roslib.packages.get_pkg_dir(PKG)
    released = []
    if not os.path.exists(os.path.join(d, 'scripts', 'additional.txt')): 
        return {}
    with open(os.path.join(d, 'scripts', 'additional.txt')) as f:
        for l in f:
            if l.strip():
                released.append(l.split())
    return dict(released)

def compute_diff(distro_name, os_platform, arch, released=None):
    if released is None:
        released = {}

    distro = load_distro(distro_name)
    packagelist = load_Packages(ROS_REPO, os_platform, arch)
    for name, stack in distro.stacks.iteritems():
        stack_version = stack.version
        repo_stack_version = get_stack_version(packagelist, distro_name, name)
        if stack_version != repo_stack_version:
            released[name] = stack_version
    return released
        
def rn_main():
    distro_name = sys.argv[1]    
    os_platform = 'lucid'
    arch = 'amd64'
    
    released = load_additional()
    if 0:
        compute_diff(distro_name, os_platform, arch, released)
    notes = create_notes(released)
    print notes


if __name__ == '__main__':
    rn_main()

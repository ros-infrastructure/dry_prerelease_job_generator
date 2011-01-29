#!/usr/bin/env python

"""
This script syncs the diamondback rosdistro file from unstable
"""
import roslib; roslib.load_manifest('release')
NAME="sync_distro.py"

import sys
import os

import yaml
import roslib.packages

def main():
    d = roslib.packages.get_pkg_dir('release_resources')
    unstable_f = os.path.join(d, '..', 'distros', 'unstable.rosdistro')
    dback_f = os.path.join(d, '..', 'distros', 'diamondback2.rosdistro')
    with open(unstable_f) as f:
        print "loading rosdistro [%s]"%(unstable_f)
        data = yaml.load(f)
    data['release'] = 'diamondback'
    with open(dback_f, 'w') as f:
        print "writing rosdistro [%s]"%(dback_f)
        f.write(yaml.safe_dump(data))

if __name__ == '__main__':
    main()

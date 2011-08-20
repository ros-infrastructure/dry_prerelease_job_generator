#!/usr/bin/env python

from __future__ import print_function
import roslib; roslib.load_manifest('rosdistro')

import rosdistro 
import sys

def main():
    if len(sys.argv) != 2:
        print "Usage: check_rosdistro.py rosdistro_file"
        return

    # parse rosdistro file
    rosdistro_obj = rosdistro.Distro(sys.argv[1])
    for name, s in rosdistro_obj.stacks.iteritems():
        tmp = s.vcs_config.type
    print('Rosdistro file for %s parses succesfully'%rosdistro_obj.release_name)
    

if __name__ == '__main__':
    main()

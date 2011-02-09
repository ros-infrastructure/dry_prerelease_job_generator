#!/usr/bin/env python

from __future__ import with_statement
import roslib; roslib.load_manifest('rosdistro')

import rosdistro 
import sys

def main():
    if len(sys.argv) != 2:
        print "Usage: check_rosdistro.py rosdistro_file"
        return

    # parse rosdistro file
    rosdistro_obj = rosdistro.Distro(sys.argv[1])
    print 'Rosdistro file for %s parses succesfully'%rosdistro_obj.release_name

if __name__ == '__main__':
    main()
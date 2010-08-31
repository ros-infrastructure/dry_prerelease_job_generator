#!/usr/bin/python

import roslib; roslib.load_manifest("hudson")
from roslib import distro, rospack, stack_manifest
import hudson
import sys
import re
import urllib2
import optparse 
from job_generation_defines import *



def main():
    parser = optparse.OptionParser()
    parser.add_option('--stack', dest = 'stack', action='store',
                      help="Specify the stacks to operate on (defaults to all stacks)")
    parser.add_option('--rosdistro', dest = 'rosdistro', action='store', default='cturtle',
                      help="Specify the ros distro to operate on (defaults to cturtle)")
    (options, args) = parser.parse_args()

    # Parse distro file
    distro_obj = distro.Distro(get_ros_distro_map()[options.rosdistro])

    # create list of stack dependencies
    stack_file = urllib2.urlopen(distro_obj.stacks[options.stack].dev_svn+'/stack.xml')
    depends = roslib.stack_manifest.parse(stack_file.read()).depends
    stack_file.close()
    print ' '.join(['-'.join(['ros', str(distro_obj.release_name), str(pkg).replace('_','-')]) for pkg in depends])


if __name__ == '__main__':
    main()
    

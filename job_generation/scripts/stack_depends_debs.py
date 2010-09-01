#!/usr/bin/python

import sys
import re
import urllib2
import optparse 
from roslib import stack_manifest
from job_generation_defines import *


def main():
    parser = optparse.OptionParser()
    parser.add_option('--stackuri', dest = 'stackuri', action='store',
                      help="Specify the stacks to operate on (defaults to all stacks)")
    parser.add_option('--rosdistro', dest = 'rosdistro', action='store', default='cturtle',
                      help="Specify the ros distro to operate on (defaults to cturtle)")
    (options, args) = parser.parse_args()

    # create list of stack dependencies
    stack_file = urllib2.urlopen(options.stackuri+'/stack.xml')
    depends = stack_manifest.parse(stack_file.read()).depends
    stack_file.close()
    print ' '.join(['-'.join(['ros', options.rosdistro, str(pkg).replace('_','-')]) for pkg in depends])


if __name__ == '__main__':
    main()
    

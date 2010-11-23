#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Revision $Id: rosutil.py 11648 2010-10-21 04:43:34Z tfoote $
# $Author: tfoote $

import roslib; roslib.load_manifest('rosdeb')
import os
import sys

import roslib.stacks
from rosdeb.targets import os_platform
from rosdeb.rosutil import missing_stack_rosdeps

def usage():
    print """Usage: check_depends.py <stack-name> <distro>"""
    sys.exit(os.EX_USAGE)
    
def print_missing(stack_name, release_name):
    d = roslib.stacks.get_stack_dir(stack_name)
    targets = os_platform[release_name]
    print "Targets: %s"%(', '.join(targets))
    bad = False
    for platform in targets:
        missing = missing_stack_rosdeps(stack_name, d, platform)
        for p, l in missing.iteritems():
            if l:
                if not bad:
                    print "\nMissing:"
                print "[%s][%s]: %s"%(p,platform, ','.join(l))
                bad = True
    return bad
    
def check_depends_main():
    if len(sys.argv) != 3:
        usage()
    stack_name, release_name = sys.argv[1:]
    if print_missing(stack_name, release_name):
        sys.exit(1)
    
if __name__ == '__main__':
    check_depends_main()
    

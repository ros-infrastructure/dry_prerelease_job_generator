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
# Revision $Id$

"""
THIS SCRIPT IS NO LONGER USED FOR ANYTHING OTHER THAN BOXTURTLE
"""

from __future__ import with_statement

import roslib; roslib.load_manifest('rosdeb')

import os
import sys
import optparse

from roslib.distro import Distro

def print_usage():
    print "./checkrepo.py ros_distro_uri repo_uri"
 
def main(argv=sys.argv):
    if len(argv) != 3:
        print_usage()
        sys.exit(os.EX_USAGE)
    ros_distro_uri, repo_uri = argv[1:]

    if repo_uri.endswith('.rosdistro'):
        raise ValueError("I think you have the arguments reversed, repo URI looks like a rosdistro file: %s"%repo_uri)
    
    repo_packages = get_deb_packages(repo_uri)
    distro = get_distro(ros_distro_uri)

    diff = compare_distro_dpkg(distro, repo_packages)
    if diff:
        print "%s packages have changed\n"%(len(diff)), '\n'.join(diff)
        sys.exit(1)
    else:
        print "no changes"

def compare_distro_dpkg(distro, repo_packages):
    changed = []
    for stack_name, stack_obj in distro.stacks.iteritems():
        
        debian_name =  stack_obj.debian_name
        if debian_name not in repo_packages:
            changed.append(stack_obj.name)
        else:
            # remove ubuntu release tag
            distro_version = stack_obj.debian_version.split('~')[0]
            deb_version = repo_packages[debian_name]['Version'].split('~')[0]
            if distro_version != deb_version:
                changed.append(stack_obj.name)
    return changed
    
def get_distro(ros_distro_uri):
    return Distro(ros_distro_uri)
    
import yaml
def parse_deb_packages(text):
    packages = []
    buff = ''
    for l in text.split('\n'):
        if not l.strip():
            if buff.strip():
                packages.append(buff)
            buff = ''
        else:
            buff += l + '\n'
    parsed = {}
    for p in packages:
        d = yaml.load(p)
        if not 'Package' in d:
            print "INVALID!", d
        else:
            parsed[d['Package']] = d
    return parsed
        
import urllib2
def get_deb_packages(uri):
    text = urllib2.urlopen(uri).read()
    return parse_deb_packages(text)

# for testing purposes
urls = [
    'http://packages.ros.org/ros/ubuntu/dists/hardy/main/binary-amd64/Packages',
    'http://packages.ros.org/ros/ubuntu/dists/hardy/main/binary-i386/Packages',
    'http://packages.ros.org/ros/ubuntu/dists/jaunty/main/binary-amd64/Packages',
    'http://packages.ros.org/ros/ubuntu/dists/jaunty/main/binary-i386/Packages',
    'http://packages.ros.org/ros/ubuntu/dists/karmic/main/binary-amd64/Packages',
    'http://packages.ros.org/ros/ubuntu/dists/karmic/main/binary-i386/Packages',
    'http://packages.ros.org/ros/ubuntu/dists/lucid/main/binary-amd64/Packages',
    'http://packages.ros.org/ros/ubuntu/dists/lucid/main/binary-i386/Packages',
    ]

distros = [
    'http://www.ros.org/distros/latest.rosdistro',
    'http://www.ros.org/distros/boxturtle.rosdistro',    
    ]

def test(i, j):
    argv = ['checkrepo.py', distros[j], urls[i]]
    main(argv)

def testall():
    for u in urls:
        main(['checkrepo.py', distros[0], u])
        main(['checkrepo.py', distros[1], u])             

if __name__ == "__main__":
    main()

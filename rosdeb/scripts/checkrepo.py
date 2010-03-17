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
http://code.ros.org/packages/ros/ubuntu/dists/hardy/main/binary-amd64/Packages
http://code.ros.org/packages/ros/ubuntu/dists/hardy/main/binary-i386/Packages
http://code.ros.org/packages/ros/ubuntu/dists/jaunty/main/binary-amd64/Packages
http://code.ros.org/packages/ros/ubuntu/dists/jaunty/main/binary-i386/Packages
http://code.ros.org/packages/ros/ubuntu/dists/karmic/main/binary-amd64/Packages
http://code.ros.org/packages/ros/ubuntu/dists/karmic/main/binary-i386/Packages

Contain the current versions of the debs in the repo.  They should be
fairly easily parseable for versions of the lates/rosdistro file.

Ken, you were talking about making a meta-build that just looks at
these files and determines whether or not the .distro file matches
what's in the repo and then kicks off the other builds.  Instead, does
it maybe make sense to do this from the chroot_build.py /
build_release.py scripts?

Do you think you could set up build_relase so that it supported the command:

 build_release checkrepo   ros_distro_uri   repo_uri

And only returned a 0 status code if the repo contains all of the
packages that are supposed to get built?


Then I could make build.py run that check first, and just return
successfully if there's nothing to do.

Then we could just trigger all the builds periodically and they'll
simply no-op if the packages are already built.
"""

from __future__ import with_statement

import os
import sys
import optparse
def print_usage():
    print "./checkrepo.py ros_distro_uri repo_uri"
 
def main(argv=sys.argv):
    if len(argv) != 3:
        print_usage()
        sys.exit(os.EX_USAGE)
    ros_distro_uri, repo_uri = argv[1:]
    
    repo_packages = get_deb_packages(repo_uri)

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
    parsed = []
    for p in packages:
        parsed.append(yaml.load(p))
    return parsed
        
        
import urllib2
def get_deb_packages(uri):
    text = urllib2.urlopen(uri).read()
    return parse_deb_packages(text)

urls = [
    'http://code.ros.org/packages/ros/ubuntu/dists/hardy/main/binary-amd64/Packages',
    'http://code.ros.org/packages/ros/ubuntu/dists/hardy/main/binary-i386/Packages',
    'http://code.ros.org/packages/ros/ubuntu/dists/jaunty/main/binary-amd64/Packages',
    'http://code.ros.org/packages/ros/ubuntu/dists/jaunty/main/binary-i386/Packages',
    'http://code.ros.org/packages/ros/ubuntu/dists/karmic/main/binary-amd64/Packages',
    'http://code.ros.org/packages/ros/ubuntu/dists/karmic/main/binary-i386/Packages',
    ]

def test(i):
    return get_deb_packages(urls[i])
    
if '__target__' == '__main__':
    main()

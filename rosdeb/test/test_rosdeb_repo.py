#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
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
import roslib; roslib.load_manifest('rosdeb')

import os
import sys
import unittest

#TODO: these need to be in a config file somewhere
REPO_URL="http://code.ros.org/packages/%(repo)s/"
SHADOW_REPO=REPO_URL%{'repo': 'ros-shadow'}
SHADOW_FIXED_REPO=REPO_URL%{'repo': 'ros-shadow-fixed'}
ROS_REPO=REPO_URL%{'repo': 'ros'}

class RepoTest(unittest.TestCase):
  
    def test_get_Packages(self):
        from rosdeb import get_Packages
        # this will work for a couple of years, at least
        s1 = get_Packages(SHADOW_REPO, 'lucid', 'amd64')
        s2 = get_Packages(SHADOW_REPO, 'lucid', 'amd64')
        # this is cached, so it should always works
        self.assertEquals(s1, s2)
        # we will test parsing of this separately, just do a sanity check
        self.assert_('Package: ' in s1)
        
    def test_parse_Packages(self):
        from rosdeb import parse_Packages, get_Packages
        s1 = get_Packages(SHADOW_REPO, 'lucid', 'amd64')
        parsed = parse_Packages(s1)
        # make sure there are some ros packages in the repo
        matches = [x for x in parsed if x[0].startswith('ros-')]
        self.assert_(len(matches))

    def test_load_Packages(self):
        from rosdeb import load_Packages
        parsed = load_Packages(SHADOW_REPO, 'lucid', 'amd64')
        # make sure there are some ros packages in the repo
        matches = [x for x in parsed if x[0].startswith('ros-')]
        self.assert_(len(matches))

    def test_deb_in_repo(self):
        from rosdeb import deb_in_repo, load_Packages
        parsed = load_Packages(SHADOW_REPO, 'lucid', 'amd64')
        self.assert_(deb_in_repo(SHADOW_REPO, parsed[0][0], parsed[0][1], 'lucid', 'amd64'))
        self.failIf(deb_in_repo(SHADOW_REPO, 'fake', parsed[0][1], 'lucid', 'amd64'))        

if __name__ == '__main__':
    from ros import rostest
    rostest.unitrun('rosdeb', 'test_rosdeb_repo', RepoTest, coverage_packages=['rosdeb.repo'])


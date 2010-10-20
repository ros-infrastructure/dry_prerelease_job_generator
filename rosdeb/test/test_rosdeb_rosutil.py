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

import roslib.stack_manifest
import rostest

class RosutilTest(unittest.TestCase):
  
    def test_convert_html_to_text(self):
        import roslib.stacks
        from rosdeb.rosutil import convert_html_to_text
        from roslib.stack_manifest import parse_file, stack_file
        for stack_name in roslib.stacks.list_stacks():
            stack_xml = stack_file(stack_name)
            m = roslib.stack_manifest.parse_file(stack_xml)
            converted = convert_html_to_text(m.description)
            # some stacks do in fact have empty descriptions
            if stack_name in ['ros', 'common_msgs', 'navigation', 'geometry']:
                self.assert_(converted)
                
            # hard to actually validate output stable-y
            if stack_name == 'ros_release':
                self.assert_('* rosinstall' in converted, converted)
                self.assert_('* Debian toolchains' in converted, converted)
                self.assert_('p>' not in converted)                
                self.assert_('<ul>' not in converted)                
        
    def test_stack_rosdeps(self):
        import rosdeb
        from rosdeb.rosutil import stack_rosdeps
        from roslib.stacks import get_stack_dir

        # this test will have to be updated as we change our supported platform set
        platforms = ['lucid', 'jaunty', 'karmic']

        # stick to stacks that should have high confidence of resolving properly
        stacks = ['ros', 'common', 'common_msgs', 'driver_common', 'geometry', 'image_common', 'image_pipeline', 'joystick_drivers', 'navigation', 'sound_drivers', 'visualization', 'visualization_common']

        base_reqd = rosdeb.rosutil.IMPLICIT_DEPS
        
        rosdeps = {}
        for platform in platforms:
            rosdeps[platform] = {}
            for stack_name in stacks:
                stack_dir = get_stack_dir(stack_name)
                
                rosdeps[platform][stack_name] = deps = stack_rosdeps(stack_name, stack_dir, platform)
                for reqd in base_reqd:
                    self.assert_(reqd in deps)

        tests = [
            ('ros', ['python-yaml', 'python-paramiko']),
            ('navigation', ['python-yaml', 'libnetpbm10-dev']),
            ('geometry', ['libglut3-dev', 'graphviz', 'python-sip4-dev', 'sip4']),
            ]

        # make sure common_msgs has no additional rosdeps
        for p in ['lucid', 'karmic', 'jaunty']:
            self.failIf(set(rosdeps[p]['common_msgs']) ^ set(base_reqd))

        for stack, reqd in tests:
            for r in reqd:
                for p in ['lucid', 'karmic', 'jaunty']:
                    self.assert_(r in rosdeps[p][stack], r)

if __name__ == '__main__':
    rostest.unitrun('rosdeb', 'test_rosdeb_rosutil', RosutilTest, coverage_packages=['rosdeb.rosutil'])


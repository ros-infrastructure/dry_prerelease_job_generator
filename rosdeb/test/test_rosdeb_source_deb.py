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

import rostest

class SourceDebTest(unittest.TestCase):
  
    def test_control_data(self):
        
        import roslib.stacks
        from roslib.stack_manifest import parse_file, stack_file
        
        from rosdeb import debianize_name
        from rosdeb.source_deb import control_data
        import rosdeb.rosutil 

        stack_version = '1.2.3'
        for stack_name in roslib.stacks.list_stacks():
            if stack_name == 'sandbox':
                continue

            print "TESTING", stack_name

            stack_xml = stack_file(stack_name)
            d1 = control_data(stack_name, stack_version, stack_xml)
            d2 = control_data(stack_name, stack_version)

            self.assertEquals(d1, d2)

            self.assertEquals(d1['stack'], stack_name)
            self.assertEquals(d1['package'], debianize_name(stack_name))
            self.assertEquals(d1['version'], stack_version)
            
            self.assert_(d1['description-brief'] is not None)
            self.assert_(len(d1['description-brief']) <= 60)

            self.assert_(d1['rosdeps'] is not None)

            if stack_name == 'common_msgs':
                self.assertEquals(['ros'], d1['depends'])
                try:
                    self.assertEquals(rosdeb.rosutil.IMPLICIT_DEPS, d1['rosdeps']['lucid'])
                except:
                    self.fail(d1['rosdeps'])
                
            
if __name__ == '__main__':
    rostest.unitrun('rosdeb', 'test_rosdeb_source_deb', SourceDebTest, coverage_packages=['rosdeb.source_deb'])


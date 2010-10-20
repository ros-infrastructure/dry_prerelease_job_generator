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

# yaml control file from pr2_arm_navigation to simplify test data setup
yaml_control = """depends: [arm_navigation, collision_environment, common_msgs, image_pipeline, kinematics,
  laser_pipeline, motion_planners, motion_planning_common, motion_planning_environment,
  pr2_common, pr2_controllers, pr2_kinematics, pr2_kinematics_with_constraints, ros,
  trajectory_filters]
description-brief: pr2_arm_navigation
description-full: ' This stack contains the launch files for arm navigation with the
  PR2 robot arms.'
homepage: http://ros.org/wiki/pr2_arm_navigation
maintainer: Maintained by Sachin Chitta
package: pr2-arm-navigation
priority: optional
rosdeps:
  hardy: [libc6, build-essential, cmake, python-yaml, subversion]
  intrepid: [libc6, build-essential, cmake, python-yaml, subversion]
  jaunty: [libc6, build-essential, cmake, python-yaml, subversion]
  karmic: [libc6, build-essential, cmake, python-yaml, subversion]
  lucid: [libc6, build-essential, cmake, python-yaml, subversion]
  mighty: [libc6, build-essential, cmake, python-yaml, subversion]
stack: pr2_arm_navigation
version: 0.2.3
"""

class SourceDebTest(unittest.TestCase):
  
    def test_control_data(self):
        import roslib.stacks
        from roslib.stack_manifest import parse_file, stack_file
        
        from rosdeb import debianize_name
        from rosdeb.source_deb import control_data
        import rosdeb.rosutil 

        stack_version = '1.2.3'
        for stack_name in ['ros', 'navigation', 'simulator_gazebo', 'geometry', 'common', 'pr2_common']:
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
                
    def test_deb_depends(self):
        from rosdeb.source_deb import deb_depends
        import yaml

        # - should return None on unsupported platform
        self.assertEquals(None, deb_depends({}, 'cturtle', 'lucid'))

        # test that rosdeps pass-through for platform
        metadata = {'rosdeps': {'lucid': ['python-yaml', 'subversion']}}
        self.assertEquals(['python-yaml', 'subversion'], deb_depends(metadata, 'cturtle', 'lucid'))
        # - should return None on unsupported platform
        self.assertEquals(None, deb_depends(metadata, 'cturtle', 'karmic'))

        # test that ROS stacks are transformed to their debian equivalent
        metadata = yaml.load(yaml_control)

        testval = ['ros-cturtle-arm-navigation', 'ros-cturtle-collision-environment',
                   'ros-cturtle-common-msgs', 'ros-cturtle-image-pipeline', 'ros-cturtle-kinematics',
                   'ros-cturtle-laser-pipeline', 'ros-cturtle-motion-planners',
                   'ros-cturtle-motion-planning-common', 'ros-cturtle-motion-planning-environment',
                   'ros-cturtle-pr2-common', 'ros-cturtle-pr2-controllers', 'ros-cturtle-pr2-kinematics',
                   'ros-cturtle-pr2-kinematics-with-constraints', 'ros-cturtle-ros',
                   'ros-cturtle-trajectory-filters']
        testval = testval + metadata['rosdeps']['lucid']
        # - should return None on unsupported platform
        self.assertEquals(None, deb_depends(metadata, 'cturtle', 'badplatform'))

        diff = set(testval) ^ set(deb_depends(metadata, 'cturtle', 'lucid'))
        self.failIf(diff, diff)
        
    def test_control_file(self):
        import yaml
        metadata = yaml.load(yaml_control)
        from rosdeb.source_deb import control_file
        txt = control_file(metadata, 'cturtle', 'lucid')
        test = """Source: pr2-arm-navigation
Section: unknown
Priority: optional
Maintainer: Sachin Chitta
Build-Depends: debhelper (>= 5), chrpath, libc6, build-essential, cmake, python-yaml, subversion, ros-cturtle-arm-navigation, ros-cturtle-collision-environment, ros-cturtle-common-msgs, ros-cturtle-image-pipeline, ros-cturtle-kinematics, ros-cturtle-laser-pipeline, ros-cturtle-motion-planners, ros-cturtle-motion-planning-common, ros-cturtle-motion-planning-environment, ros-cturtle-pr2-common, ros-cturtle-pr2-controllers, ros-cturtle-pr2-kinematics, ros-cturtle-pr2-kinematics-with-constraints, ros-cturtle-ros, ros-cturtle-trajectory-filters
Standards-Version: 3.7.2

Package: pr2-arm-navigation
Architecture: any
Depends: ${shlibs:Depends}, ${misc:Depends}, libc6, build-essential, cmake, python-yaml, subversion, ros-cturtle-arm-navigation, ros-cturtle-collision-environment, ros-cturtle-common-msgs, ros-cturtle-image-pipeline, ros-cturtle-kinematics, ros-cturtle-laser-pipeline, ros-cturtle-motion-planners, ros-cturtle-motion-planning-common, ros-cturtle-motion-planning-environment, ros-cturtle-pr2-common, ros-cturtle-pr2-controllers, ros-cturtle-pr2-kinematics, ros-cturtle-pr2-kinematics-with-constraints, ros-cturtle-ros, ros-cturtle-trajectory-filters
Description: pr2_arm_navigation
 This stack contains the launch files for arm navigation with the PR2 robot arms."""

        for actual, real in zip(txt.split('\n'), test.split('\n')):
            self.assertEquals(actual, real)
            

if __name__ == '__main__':
    from ros import rostest
    rostest.unitrun('rosdeb', 'test_rosdeb_source_deb', SourceDebTest, coverage_packages=['rosdeb.source_deb'])


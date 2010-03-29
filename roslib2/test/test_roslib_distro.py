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
from __future__ import with_statement
PKG = 'roslib2'
import roslib; roslib.load_manifest(PKG)

import os
import sys
import unittest
import yaml

import roslib.packages
import rostest

def load_distros():
    d = roslib.packages.get_pkg_dir(PKG)
    distros = {}
    for release_name in ['latest', 'boxturtle']:
        with open(os.path.join(d, 'test', '%s.rosdistro'%release_name)) as f:
            distros[release_name] = yaml.load(f.read())
    return distros

class DistroTest(unittest.TestCase):
  
    def test_get_rules(self):
        distros = load_distros()
        # boxturtle tests
        boxturtle = distros['boxturtle']
        from roslib2.distro import get_rules

        rules = {'dev-svn': 'https://code.ros.org/svn/ros/stacks/ros/tags/rc',
                 'distro-svn': 'https://code.ros.org/svn/ros/stacks/ros/tags/$RELEASE_NAME',
                 'release-svn': 'https://code.ros.org/svn/ros/stacks/ros/tags/$STACK_NAME-$STACK_VERSION',
                 'source-tarball': 'http://ros.org/download/stacks/$STACK_NAME/$STACK_NAME-$STACK_VERSION.tar.bz2'}
        
        self.assertEquals(rules, get_rules(boxturtle, 'ros'))

        rules = {'dev-svn': 'https://code.ros.org/svn/ros-pkg/stacks/$STACK_NAME/branches/$STACK_NAME-1.0',
                 'distro-svn': 'https://code.ros.org/svn/ros-pkg/stacks/$STACK_NAME/tags/$RELEASE_NAME',
                 'release-svn': 'https://code.ros.org/svn/ros-pkg/stacks/$STACK_NAME/tags/$STACK_NAME-$STACK_VERSION',
                 'source-tarball': 'http://ros.org/download/stacks/$STACK_NAME/$STACK_NAME-$STACK_VERSION.tar.bz2'}
        for s in ['common', 'navigation', 'simulator_stage', 'visualization', 'visualization_common']:
            self.assertEquals(rules, get_rules(boxturtle, s))

        rules = {'dev-svn': 'https://code.ros.org/svn/wg-ros-pkg/stacks/$STACK_NAME/trunk',
                 'distro-svn': 'https://code.ros.org/svn/wg-ros-pkg/stacks/$STACK_NAME/tags/$RELEASE_NAME',
                 'release-svn': 'https://code.ros.org/svn/wg-ros-pkg/stacks/$STACK_NAME/tags/$STACK_NAME-$STACK_VERSION',
                 'source-tarball': 'http://ros.org/download/stacks/$STACK_NAME/$STACK_NAME-$STACK_VERSION.tar.bz2'}
            
        for s in ['arm_navigation', 'motion_planners', 'pr2_calibration', 'pr2_ethercat_drivers']:
            self.assertEquals(rules, get_rules(boxturtle, s))
        
    def test_get_variants(self):
        import roslib2.distro
        from roslib2.distro import get_variants

        distros = load_distros()
        # boxturtle tests
        boxturtle = distros['boxturtle']
        self.assertEquals(['base', 'pr2'], get_variants(boxturtle, 'ros'))
        self.assertEquals(['base', 'pr2'], get_variants(boxturtle, 'navigation'))        
        self.assertEquals(['pr2'], get_variants(boxturtle, 'pr2_mechanism'))        
        self.assertEquals([], get_variants(boxturtle, 'arm_navigation'))
        self.assertEquals([], get_variants(boxturtle, 'fake'))        

        # latest tests
        latest = distros['latest']
        self.assertEquals(['base', 'pr2', 'pr2all'], get_variants(latest, 'ros'))
        self.assertEquals(['base', 'pr2','pr2all'], get_variants(latest, 'navigation'))        
        self.assertEquals(['pr2','pr2all'], get_variants(latest, 'pr2_mechanism'))        
        self.assertEquals(['pr2all'], get_variants(latest, 'arm_navigation'))        
        self.assertEquals([], get_variants(latest, 'fake'))
        
if __name__ == '__main__':
  rostest.unitrun('roslib2', 'test_distro', DistroTest, coverage_packages=['roslib2.distro'])


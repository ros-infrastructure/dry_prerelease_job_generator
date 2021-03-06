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
PKG = 'rosdistro'
import roslib; roslib.load_manifest(PKG)

import os
import sys
import unittest
import yaml

import roslib.packages

def load_distros_legacy():
    """
    Load distro files as dicts
    """
    d = roslib.packages.get_pkg_dir(PKG)
    distros = {}
    for release_name in ['latest', 'boxturtle', 'latest-v2', 'boxturtle-v2']:
        with open(os.path.join(d, 'test', '%s.rosdistro'%release_name)) as f:
            try:
                distros[release_name] = yaml.load(f.read())
            except:
                raise Exception("failed to load "+release_name)
    return distros

def load_Distros_boxturtle():
    """
    Load distro files as Distro instances
    """
    from rosdistro import Distro
    d = roslib.packages.get_pkg_dir(PKG)
    distros = {}
    for release_name in ['latest', 'boxturtle', 'latest-v2', 'boxturtle-v2']:
        p = os.path.join(d, 'test', '%s.rosdistro'%release_name)
        distros[release_name] = Distro(p)
    return distros

def load_Distros_dback():
    """
    Load distro files as Distro instances
    """
    from rosdistro import Distro
    d = roslib.packages.get_pkg_dir(PKG)
    distros = {}
    for release_name in ['diamondback']:
        p = os.path.join(d, 'test', '%s.rosdistro'%release_name)
        distros[release_name] = Distro(p)
    return distros

boxturtle_ros_rules = {'dev-svn': 'https://code.ros.org/svn/ros/stacks/ros/tags/rc',
                       'distro-svn': 'https://code.ros.org/svn/ros/stacks/ros/tags/$RELEASE_NAME',
                       'release-svn': 'https://code.ros.org/svn/ros/stacks/ros/tags/$STACK_NAME-$STACK_VERSION'}
boxturtle_rospkg_rules = {'dev-svn': 'https://code.ros.org/svn/ros-pkg/stacks/$STACK_NAME/branches/$STACK_NAME-1.0',
                          'distro-svn': 'https://code.ros.org/svn/ros-pkg/stacks/$STACK_NAME/tags/$RELEASE_NAME',
                          'release-svn': 'https://code.ros.org/svn/ros-pkg/stacks/$STACK_NAME/tags/$STACK_NAME-$STACK_VERSION'}
boxturtle_wgrospkg_rules = {'dev-svn': 'https://code.ros.org/svn/wg-ros-pkg/stacks/$STACK_NAME/branches/$STACK_NAME-1.0',
                            'distro-svn': 'https://code.ros.org/svn/wg-ros-pkg/stacks/$STACK_NAME/tags/$RELEASE_NAME',
                            'release-svn': 'https://code.ros.org/svn/wg-ros-pkg/stacks/$STACK_NAME/tags/$STACK_NAME-$STACK_VERSION'}
wg_unbranched_rules = {'dev-svn': 'https://code.ros.org/svn/wg-ros-pkg/stacks/$STACK_NAME/trunk',
                       'distro-svn': 'https://code.ros.org/svn/wg-ros-pkg/stacks/$STACK_NAME/tags/$RELEASE_NAME',
                       'release-svn': 'https://code.ros.org/svn/wg-ros-pkg/stacks/$STACK_NAME/tags/$STACK_NAME-$STACK_VERSION'}

boxturtle_versions = {
  'common': '1.0.3',
  'common_msgs': '1.0.0',
  'geometry': '1.0.2',
  'navigation': '1.0.4',
  'pr2_common': '1.0.2',
  'pr2_mechanism': '1.0.2',
  'pr2_navigation': '0.1.1',
  'robot_model': '1.0.1',
  'ros':'1.0.1',
  'ros_experimental': '0.1.0',
  'simulator_gazebo': '1.0.3',
  'simulator_stage':  '1.0.0',
  'visualization': '1.0.1',
  'wg_common': '0.1.2',
  'wg_pr2_apps': '0.1.1',
  'wifi_drivers':'0.1.3',
  }

dback_ros_rules = {'svn': {'dev': 'https://code.ros.org/svn/ros/stacks/$STACK_NAME/trunk',
                           'distro-tag': 'https://code.ros.org/svn/ros/stacks/$STACK_NAME/tags/$RELEASE_NAME',
                           'release-tag': 'https://code.ros.org/svn/ros/stacks/$STACK_NAME/tags/$STACK_NAME-$STACK_VERSION'},
                   'repo': 'ros'}
dback_rospkg_rules = {'svn': {'dev': 'https://code.ros.org/svn/ros-pkg/stacks/$STACK_NAME/trunk',
                              'distro-tag': 'https://code.ros.org/svn/ros-pkg/stacks/$STACK_NAME/tags/$RELEASE_NAME',
                              'release-tag': 'https://code.ros.org/svn/ros-pkg/stacks/$STACK_NAME/tags/$STACK_NAME-$STACK_VERSION'},
                      'repo': 'ros-pkg'}

dback_versions = {
  'common': '1.3.3',
  'common_msgs': '1.3.5',
  'geometry': '1.3.1',
  'navigation': '1.3.1',
  'ros':'1.4.0',
  }

class DistroTest(unittest.TestCase):

    def test_Distro_dback(self):
        # TODO: better unit tests. For now this is mostly a tripwire
        from rosdistro import Distro, DistroStack, Variant
        distros = load_Distros_dback()

        r = 'diamondback'
        v = 'r8596'

        for d in ['diamondback']:
            dback = distros[d]

            self.assertEquals(r, dback.release_name)
            self.assertEquals(v, dback.version)        

            # make sure ros got assigned and is correct
            ros = DistroStack('ros', dback_ros_rules, dback_versions['ros'], r, v)
            self.assertEquals(ros, dback.ros)
            self.assertEquals(ros, dback.stacks['ros'])        

            # make sure the variants are configured
            self.assert_('base' not in dback.variants)
            
            ros_base = dback.variants['ros-base']
            self.assertEquals([], ros_base.parents)
            ros_base_stacks = ['ros', 'ros_comm']
            self.assertEquals(ros_base_stacks, ros_base.stack_names)
            
            robot = dback.variants['robot'] #extends ros-base
            self.assertEquals(set(['ros-base']), set(robot.parents))
            robot_stacks = ['common_msgs', 'common', 'diagnostics', 'driver_common', 'geometry', 'robot_model', 'executive_smach']
            self.assertEquals(set(ros_base_stacks+robot_stacks), set(robot.stack_names))
            self.assertEquals(set(robot_stacks), set(robot.stack_names_explicit))
            
            mobile = dback.variants['mobile'] #extends robot
            mobile_stacks = ['navigation', 'slam_gmapping']
            self.assertEquals(set(ros_base_stacks+robot_stacks+mobile_stacks), set(mobile.stack_names))
            self.assertEquals(set(mobile_stacks), set(mobile.stack_names_explicit))
            
            viz = dback.variants['viz'] 
            self.assertEquals([], viz.parents)
            viz_stacks = ['visualization_common', 'visualization'] 
            self.assertEquals(set(viz_stacks), set(viz.stack_names))
            self.assertEquals(set(viz_stacks), set(viz.stack_names_explicit))

            desktop = dback.variants['desktop'] #robot, rviz
            self.assertEquals(set(['robot', 'viz']), set(desktop.parents))
            desktop_stacks = ['ros_tutorials', 'common_tutorials', 'geometry_tutorials', 'visualization_tutorials']
            self.assertEquals(set(ros_base_stacks+robot_stacks+viz_stacks+desktop_stacks), set(desktop.stack_names))
            self.assertEquals(set(desktop_stacks), set(desktop.stack_names_explicit))
            
            simulator_stacks = ['simulator_stage', 'simulator_gazebo', 'physics_ode']
            perception_stacks = ['image_common', 'image_transport_plugins', 'image_pipeline', 'laser_pipeline', 'perception_pcl', 'vision_opencv']
            desktop_full = dback.variants['desktop-full'] 
            self.assertEquals(set(['desktop', 'mobile', 'perception', 'simulators']), set(desktop_full.parents))
            self.assertEquals(set(ros_base_stacks+robot_stacks+mobile_stacks+perception_stacks+simulator_stacks+desktop_stacks+viz_stacks), set(desktop_full.stack_names))
            self.assertEquals([], desktop_full.stack_names_explicit)


        # make sure we loaded the stacks
        stack_names = ['common', 'common_msgs', 'navigation']
        for s in stack_names:
            val = DistroStack(s, dback_rospkg_rules, dback_versions[s], r, v)
            self.assertEquals(val, dback.stacks[s])
            
        # test an hg rule
        dback_geometry_rules = {'hg':
                                {'dev-branch': 'tf_rework',
                                 'distro-tag': '$RELEASE_NAME',
                                 'release-tag': '$STACK_NAME-$STACK_VERSION',
                                 'uri': 'https://ros-geometry.googlecode.com/hg/'},
                                'repo': 'ros-pkg',
                                }
        s = 'geometry'
        val = DistroStack(s, dback_geometry_rules, dback_versions[s], r, v)
        self.assertEquals(val, dback.stacks[s])

        
    def test_Distro_boxturtle(self):
        # TODO: better unit tests. For now this is mostly a tripwire
        from rosdistro import Distro, DistroStack, Variant
        distros = load_Distros_boxturtle()

        r = 'boxturtle'
        v = '6'

        for bt in ['boxturtle', 'boxturtle-v2']:
            boxturtle = distros[bt]

            self.assertEquals(r, boxturtle.release_name)
            self.assertEquals(v, boxturtle.version)        

            # make sure ros got assigned and is correct
            ros = DistroStack('ros', boxturtle_ros_rules, boxturtle_versions['ros'], r, v)
            self.assertEquals(ros, boxturtle.ros)
            self.assertEquals(ros, boxturtle.stacks['ros'])        

            # make sure the variants are configured
            self.assert_('base' in boxturtle.variants)
            base = boxturtle.variants['base']
            pr2 = boxturtle.variants['pr2']

            self.assert_('base' in pr2.parents, pr2.parents)

            self.assertEquals([], base.parents)
            base_stacks = ['ros', 'camera_drivers', 'common_msgs', 'common', 'diagnostics', 'driver_common',
                           'geometry', 'image_common', 'image_pipeline', 'imu_drivers', 'joystick_drivers', 'laser_drivers',
                           'laser_pipeline', 'navigation', 'physics_ode', 'robot_model', 'simulator_gazebo', 'simulator_stage',
                           'slam_gmapping', 'sound_drivers', 'vision_opencv', 'visualization_common', 'visualization']
            self.assertEquals(set(base_stacks), set(base.stack_names))
            self.assertEquals(set(base_stacks), set(base.stack_names_explicit))

            pr2_stacks =['image_transport_plugins', 'pr2_apps', 'pr2_common', 'pr2_controllers', 'pr2_ethercat_drivers',
                         'pr2_gui', 'pr2_mechanism', 'pr2_power_drivers', 'pr2_robot', 'pr2_simulator', 'web_interface',
                         'wifi_drivers']

            self.assertEquals(set(pr2_stacks+base_stacks), set(pr2.stack_names))
            self.assertEquals(set(pr2_stacks), set(pr2.stack_names_explicit))
            

        # make sure we loaded the stacks
        stack_names = ['common', 'common_msgs', 'navigation', 'geometry']
        for s in stack_names:
            val = DistroStack(s, boxturtle_rospkg_rules, boxturtle_versions[s], r, v)
            self.assertEquals(val, boxturtle.stacks[s])

        self.assertEquals(['base', 'pr2'], sorted(boxturtle.variants.keys()))

        #TODO: much more to test

    def test_get_rules_legacy(self):
        distros = load_distros_legacy()
        # boxturtle tests
        for bt in ['boxturtle', 'boxturtle-v2']:
            boxturtle = distros['boxturtle']
            from rosdistro import get_rules

            self.assertEquals(boxturtle_ros_rules, get_rules(boxturtle, 'ros'))

            for s in ['common', 'navigation', 'simulator_stage', 'visualization', 'visualization_common']:
                self.assertEquals(boxturtle_rospkg_rules, get_rules(boxturtle, s))

            for s in ['arm_navigation', 'motion_planners', 'pr2_calibration', 'pr2_ethercat_drivers']:
                self.assertEquals(wg_unbranched_rules, get_rules(boxturtle, s))

    def test_load_vcs_config(self):
        from rosdistro import load_vcs_config
        def rule_eval(x):
            return x + "-evaled"

        # new svn
        rules = {'svn':
                     {'dev': 'http://dev-rule',
                      'distro-tag': 'http://distro-tag',
                      'release-tag': 'http://release-tag'}}
        
        def base_test(vc):
            self.assertEquals(vc, load_vcs_config(rules, rule_eval))
            self.assertEquals(vc.dev, 'http://dev-rule-evaled')
            self.assertEquals(vc.distro_tag, 'http://distro-tag-evaled')
            self.assertEquals(vc.release_tag, 'http://release-tag-evaled')
            
        vc = load_vcs_config(rules, rule_eval)
        base_test(vc)
        self.assertEquals(vc.anon_dev, 'http://dev-rule-evaled')
        self.assertEquals(vc.anon_distro_tag, 'http://distro-tag-evaled')
        self.assertEquals(vc.anon_release_tag, 'http://release-tag-evaled')

        # - test w/ anon
        rules['svn']['anon-dev'] = 'http://anon-dev'
        rules['svn']['anon-distro-tag'] = 'http://anon-distro-tag'
        rules['svn']['anon-release-tag'] = 'http://anon-release-tag'
        
        vc = load_vcs_config(rules, rule_eval)
        base_test(vc)
        self.assertEquals(vc.anon_dev, 'http://anon-dev-evaled')
        self.assertEquals(vc.anon_distro_tag, 'http://anon-distro-tag-evaled')
        self.assertEquals(vc.anon_release_tag, 'http://anon-release-tag-evaled')

        # legacy svn
        rules = {'dev-svn':'http://dev-rule',
                 'distro-svn': 'http://distro-tag',
                 'release-svn': 'http://release-tag'}
        vc = load_vcs_config(rules, rule_eval)
        base_test(vc)
        self.assertEquals(vc.anon_dev, 'http://dev-rule-evaled')
        self.assertEquals(vc.anon_distro_tag, 'http://distro-tag-evaled')
        self.assertEquals(vc.anon_release_tag, 'http://release-tag-evaled')

        # hg
        rules = {'hg':
                     {'uri': 'http://uri',
                      'anon-uri': 'http://anon-uri',
                      'dev-branch': 'http://dev-branch',
                      'release-tag': 'http://release-tag',
                      'distro-tag': 'http://distro-tag'}}
        vc = load_vcs_config(rules, rule_eval)
        self.assertEquals(vc.repo_uri, 'http://uri-evaled')
        self.assertEquals(vc.anon_repo_uri, 'http://anon-uri-evaled')
        self.assertEquals(vc.dev_branch, 'http://dev-branch-evaled')    
        self.assertEquals(vc.distro_tag, 'http://distro-tag-evaled')
        self.assertEquals(vc.release_tag, 'http://release-tag-evaled')
        
        # git
        rules = {'git':
                     {'uri': 'http://uri',
                      'anon-uri': 'http://anon-uri',
                      'dev-branch': 'http://dev-branch',
                      'release-tag': 'http://release-tag',
                      'distro-tag': 'http://distro-tag'}}
        vc = load_vcs_config(rules, rule_eval)
        self.assertEquals(vc.repo_uri, 'http://uri-evaled')
        self.assertEquals(vc.anon_repo_uri, 'http://anon-uri-evaled')
        self.assertEquals(vc.dev_branch, 'http://dev-branch-evaled')    
        self.assertEquals(vc.distro_tag, 'http://distro-tag-evaled')
        self.assertEquals(vc.release_tag, 'http://release-tag-evaled')
        
    def test_get_rules(self):
        from rosdistro import get_rules
        distros = load_distros_legacy()
        # boxturtle tests
        for t in ['cturtle']:
            boxturtle = distros['boxturtle']
            self.assertEquals(boxturtle_ros_rules, get_rules(boxturtle, 'ros'))
            # test aliasing of ROS == ros. Not sure why that code is
            # in there, but add a tripwire to investigate this if its
            # ever removed.
            self.assertEquals(get_rules(boxturtle, 'ros'), get_rules(boxturtle, 'ROS'))

            for s in ['common', 'navigation', 'simulator_stage', 'visualization', 'visualization_common']:
                self.assertEquals(boxturtle_rospkg_rules, get_rules(boxturtle, s))

            for s in ['arm_navigation', 'motion_planners', 'pr2_calibration', 'pr2_ethercat_drivers']:
                self.assertEquals(wg_unbranched_rules, get_rules(boxturtle, s))
        
    def test_load_distro_stacks(self):
        from rosdistro import load_distro_stacks, DistroStack

        distros = load_distros_legacy()

        v = '6'
        r = 'boxturtle'
        for f in ['boxturtle', 'boxturtle-v2']:
            boxturtle = distros[f]

            ros_version = boxturtle_versions['ros']
            self.assertEquals({}, load_distro_stacks(boxturtle, [], r, '5'))

            # - test with overrides
            ros = DistroStack('ros', boxturtle_ros_rules, ros_version, 'foxturtle', '55')
            other = load_distro_stacks(boxturtle, ['ros'], 'foxturtle', '55')['ros']
            self.assertEquals(ros.name, other.name)
            self.assertEquals(ros.version, other.version)
            self.assertEquals(ros.vcs_config, other.vcs_config)
            self.assertEquals(ros, other)

            # - test with actual distro values
            ros = DistroStack('ros', boxturtle_ros_rules, ros_version, r, v)
            self.assertEquals({'ros': ros}, load_distro_stacks(boxturtle, ['ros']))

            # test with the base stuff
            stack_names = ['ros', 'common', 'common_msgs', 'navigation', 'geometry']
            val = {'ros': ros}
            for s in [x for x in stack_names if x != 'ros']:
                val[s] = DistroStack(s, boxturtle_rospkg_rules, boxturtle_versions[s], r, v)

            self.assertEquals(val.keys(), load_distro_stacks(boxturtle, stack_names, r, v).keys())
            loaded = load_distro_stacks(boxturtle, stack_names, r, v)
            # iterate compare first for easy test diagnosis
            for k, item in val.iteritems():
                self.assertEquals(item, loaded[k], "failed on [%s]: %s"%(k, loaded[k]))
            # failsafe to ensure no extra items
            self.assertEquals(val, loaded)

            # add in some pr2 stacks which have different ways of setting rules
            pr2_stack_names = ['pr2_common', 'pr2_mechanism']
            for s in pr2_stack_names:
                val[s] = DistroStack(s, boxturtle_wgrospkg_rules, boxturtle_versions[s], r, v)
            stack_names = stack_names + pr2_stack_names
            self.assertEquals(val, load_distro_stacks(boxturtle, stack_names, r, v))

            # test an expanded rule
            pr2_common = load_distro_stacks(boxturtle, stack_names, r, v)['pr2_common']
            dev_svn = 'https://code.ros.org/svn/wg-ros-pkg/stacks/pr2_common/branches/pr2_common-1.0'
            distro_svn = 'https://code.ros.org/svn/wg-ros-pkg/stacks/pr2_common/tags/boxturtle'
            release_svn = 'https://code.ros.org/svn/wg-ros-pkg/stacks/pr2_common/tags/pr2_common-1.0.2'
            self.assertEquals(dev_svn, pr2_common.dev_svn)
            self.assertEquals(distro_svn, pr2_common.distro_svn)
            self.assertEquals(release_svn, pr2_common.release_svn)
            
    def test_get_variants(self):
        import rosdistro
        from rosdistro import get_variants

        distros = load_distros_legacy()
        # boxturtle tests
        for bt in ['boxturtle', 'boxturtle-v2']:
            boxturtle = distros[bt]
            self.assertEquals(['base', 'pr2'], get_variants(boxturtle, 'ros'))
            self.assertEquals(['base', 'pr2'], get_variants(boxturtle, 'navigation'))        
            self.assertEquals(['pr2'], get_variants(boxturtle, 'pr2_mechanism'))        
            self.assertEquals([], get_variants(boxturtle, 'arm_navigation'))
            self.assertEquals([], get_variants(boxturtle, 'fake'))        

        # latest tests
        for l in ['latest', 'latest-v2']:
            latest = distros[l]
            self.assertEquals(['base', 'pr2', 'pr2all'], get_variants(latest, 'ros'))
            self.assertEquals(['base', 'pr2','pr2all'], get_variants(latest, 'navigation'))        
            self.assertEquals(['pr2','pr2all'], get_variants(latest, 'pr2_mechanism'))        
            self.assertEquals(['pr2all'], get_variants(latest, 'arm_navigation'))        
            self.assertEquals([], get_variants(latest, 'fake'))
        
if __name__ == '__main__':
    from ros import rostest 
    rostest.unitrun('rosdistro', 'test_rosdistro', DistroTest, coverage_packages=['rosdistro'])


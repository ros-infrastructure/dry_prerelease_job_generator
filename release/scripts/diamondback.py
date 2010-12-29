#!/usr/bin/env python

import roslib; roslib.load_manifest('release')
import os
import roslib.packages
from rosdistro import Distro

DISTRO = 'unstable'

frozen = [
    'common',
    'common_msgs',
    'diagnostics',
    'documentation',
    'driver_common',
    'geometry',
    'image_common',
    'image_transport_plugins',
    'imu_drivers',
    'joystick_drivers',
    'laser_drivers',
    'laser_pipeline',
    'physics_ode',
    'pr2_common',
    'pr2_controllers',
    'pr2_gui',
    'pr2_power_drivers',
    'pr2_ethercat_drivers',
    'pr2_mechanism',
    'pr2_robot',
    'robot_model',
    'ros',
    'rx',
    'simulator_gazebo',
    'simulator_stage',
    'slam_gmapping',
    'sound_drivers',
    'visualization_common',
    'visualization',
    ]
excluded = [
    'common_tutorials',
    'geometry_experimental',
    'geometry_tutorials',
    'joystick_drivers_tutorials',
    'ros_tutorials',
    'visualization_tutorials',
    'web_interface',
    ]

d = roslib.packages.get_pkg_dir('release_resources')
p = os.path.join(d, '..', 'distros', '%s.rosdistro'%(DISTRO))
distro = Distro(p)

print "Variants"
for v in ['base', 'pr2']:
    variant = set(distro.variants[v].stack_names) - set(excluded)
    remaining = variant - set(frozen)
    print " * %s (%s/%s)"%(v, len(variant)-len(remaining), len(variant))


for v in ['base', 'pr2']:
    print "\n%s report"%(v)
    for s in sorted(distro.variants[v].props['stacks']):
        if s in frozen:
            print "[X] %s"%(s)
        elif s in excluded:
            pass
        else:
            print "[ ] %s"%(s)

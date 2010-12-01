#!/usr/bin/env python

import roslib; roslib.load_manifest('release')
import os
import roslib.packages
from rosdistro import Distro

DISTRO = 'unstable'

frozen = [
    'common',
    'common_msgs',
    'documentation',
    'driver_common',
    'image_common',
    'image_transport_plugins',
    'imu_drivers',
    'laser_pipeline',
    'physics_ode',
    'pr2_gui',
    'robot_model',
    'ros',
    'rx',
    'simulator_gazebo',
    'slam_gmapping',
    'visualization_common',
    ]
excluded = [
    'common_tutorials',
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

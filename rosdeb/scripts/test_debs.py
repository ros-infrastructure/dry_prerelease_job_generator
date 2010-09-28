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

"""
Build debs for a package and all of its dependencies as necessary
"""

import roslib; roslib.load_manifest('rosdeb')

import os
import sys
import subprocess
import shutil
import tempfile
import yaml
import urllib2
import stat
import tempfile

import rosdeb
from rosdeb.rosutil import checkout_svn_to_tmp

from roslib2.distro import Distro
from rosdeb.core import ubuntu_release, debianize_name, debianize_version, platforms, ubuntu_release_name

NAME = 'build_debs.py' 
TARBALL_URL = "https://code.ros.org/svn/release/download/stacks/%(stack_name)s/%(base_name)s/%(f_name)s"
SHADOW_REPO="http://code.ros.org/packages/ros-shadow/"
SHADOW_REPO_FIXED="http://code.ros.org/packages/ros-shadow/"

import traceback

# Stolen from chroot build
class TempRamFS:
    def __init__(self, path, size_str):
        self.path = path
        self.size= size_str
        
    def __enter__(self):
        
        cmd = ['sudo', 'mkdir', '-p', self.path]
        subprocess.check_call(cmd)
        cmd = ['sudo', 'mount', '-t', 'tmpfs', '-o', 'size=%s,mode=0755'%self.size, 'tmpfs', self.path]
        subprocess.check_call(cmd)
        cmd = ['sudo', 'chown', '-R', str(os.geteuid()), self.path]
        subprocess.check_call(cmd)
        return self

    def __exit__(self, mtype, value, tb):
        if tb:
            print "Caught exception, closing out ramdisk"
            traceback.print_exception(mtype, value, tb, file=sys.stdout)
            
        cmd = ['sudo', 'umount', '-f', self.path]
        subprocess.check_call(cmd)



def compute_deps(distro, stack_name):

    seen = set()
    ordered_deps = []

    def add_stack(s):
        if s in seen:
            return
        if s not in distro.stacks:
            print >> sys.stderr, "[%s] not found in distro."%(s)
            sys.exit(1)
        seen.add(s)
        v = distro.stacks[s].version
        si = load_info(s, v)
        for d in si['depends']:
            add_stack(d)
        ordered_deps.append((s,v))

    if stack_name == 'ALL':
        for s in distro.stacks.keys():
            add_stack(s)
    else:
        add_stack(stack_name)

    return ordered_deps



# TODO: this should be pulled into a centralized location
def create_chroot(distro, distro_name, os_platform, arch):

    distro_tgz = os.path.join('/var/cache/pbuilder', "%s-%s.tgz"%(os_platform, arch))

    if os.path.exists(distro_tgz):
        return

    ros_info = load_info('ros', distro.stacks['ros'].version)

    # Things that this build infrastructure depends on
    basedeps = ['wget', 'lsb-release', 'debhelper']
    # Deps we claimed to have needed for building ROS
    basedeps += ['build-essential', 'python-yaml', 'cmake', 'subversion', 'python-setuptools']
    # Extra deps that some stacks seem to be missing
    basedeps += ['libxml2-dev', 'libtool', 'unzip']
    # For debugging
    basedeps += ['strace']

    deplist = ' '.join(basedeps+ros_info['rosdeps'][os_platform])

    subprocess.check_call(['sudo', 'pbuilder', '--create', '--distribution', os_platform, '--debootstrapopts', '--arch=%s'%arch, '--othermirror', 'deb http://code.ros.org/packages/ros-shadow/ubuntu %s main'%(os_platform), '--basetgz', distro_tgz, '--components', 'main restricted universe multiverse', '--extrapackages', deplist])




def test_debs(distro_name, stack_name, os_platform, arch, staging_dir, interactive, testresults):


    distro_tgz = os.path.join('/var/cache/pbuilder', "%s-%s.tgz"%(os_platform, arch))
    deb_name = "ros-%s-%s"%(distro_name, debianize_name(stack_name))

    conf_file = os.path.join(roslib.packages.get_pkg_dir('rosdeb'),'config','pbuilder.conf')

    # Make sure the distro chroot exists
    if not os.path.exists(distro_tgz):
        print >> sys.stderr, "%s does not exist."%(distro_tgz)
        sys.exit(1)


    # Create build directory
    results_dir = os.path.join(staging_dir, 'results')
    build_dir = os.path.join(staging_dir, 'pbuilder')

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    if arch == 'amd64':
        archcmd = []
    else:
        archcmd = ['setarch', arch]

    # Load the distro from the URL
    # TODO: Should this be done from file in release repo instead (and maybe updated in case of failure)
    distro_uri = "https://code.ros.org/svn/release/trunk/distros/%s.rosdistro"%distro_name
    distro = Distro(distro_uri)

    # Create the environment where we build the debs, if necessary
    create_chroot(distro, distro_name, os_platform, arch)

    # Script to execute for deb verification
    # TODO: Add code to run all the unit-tests for the deb!
    verify_script = os.path.join(staging_dir, 'verify_script.sh')

    if interactive:
        interactive_txt="""
echo "Entering interactive environment.  Exit when done to continue pbuilder operation."
bash </dev/tty
echo "Resuming pbuilder"
"""
    else:
        interactive_txt=''

    verify_txt="""#!/bin/bash
set -o errexit
echo "deb http://code.ros.org/packages/ros-shadow-fixed/ubuntu %(os_platform)s main" > /etc/apt/sources.list.d/ros-shadow-fixed.list
wget https://code.ros.org/svn/ros/stacks/ros_release/trunk/rosdeb/resources/test_debs/test-nobuild.patch -O /tmp/test-nobuild.patch
apt-get update
apt-get install %(deb_name)s -y --force-yes
. /opt/ros/%(distro_name)s/setup.sh
mkdir -p /opt/ros/%(distro_name)s/stacks
roscd ros
patch -p0 < /tmp/test-nobuild.patch
mkdir -p /tmp/home
export HOME=/tmp/home
export ROS_HOME=${HOME}/.ros"
%(interactive_txt)s
for p in `rosstack contents %(stack_name)s`;
  do rm -rf `rospack find $p`/build;
done
set +o errexit
export ROS_TEST_RESULTS_DIR=%(results_dir)s
(for p in `rosstack contents %(stack_name)s`;
  do roscd $p && if [ -e Makefile ]; then echo "Running unit tests for $p...";
  make test-nobuild; fi
done) 2>&1 | tee %(results_dir)s/nobuild.out
set -o errexit
rosrun rostest cleanunit
"""%locals()

    with open(verify_script, 'w') as f:
        f.write(verify_txt)
        os.chmod(verify_script, stat.S_IRWXU)

    print "starting verify script for %s:"%(stack_name)
    subprocess.check_call(archcmd + ['sudo', 'pbuilder', '--execute', '--basetgz', distro_tgz, '--configfile', conf_file, '--bindmounts', results_dir, '--buildplace', build_dir, verify_script])

    if testresults:
        shutil.copytree(os.path.join(results_dir, '_hudson'), os.path.join(testresults, '_hudson'))



def test_debs_main():

    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog <distro> <stack> <os-platform> <arch>", prog=NAME)

    parser.add_option("-d", "--dir",
                      dest="staging_dir", default=None,
                      help="directory to use for staging source debs", metavar="STAGING_DIR")
    parser.add_option("--noramdisk",
                      dest="ramdisk", default=True, action="store_false")
    parser.add_option("--interactive",
                      dest="interactive", default=False, action="store_true")
    parser.add_option("--testresults",
                      dest="testresults", default=None)

    (options, args) = parser.parse_args()

    if len(args) != 4:
        parser.error('invalid args')
        
    (distro_name, stack_name, os_platform, arch) = args

    if options.staging_dir is not None:
        staging_dir    = options.staging_dir
        staging_dir = os.path.abspath(staging_dir)
    else:
        staging_dir = tempfile.mkdtemp()

    if os_platform not in rosdeb.platforms():
        print >> sys.stderr, "[%s] is not a known platform.\nSupported platforms are: %s"%(os_platform, ' '.join(rosdeb.platforms()))
        sys.exit(1)
    
    if not os.path.exists(staging_dir):
        print "creating staging dir: %s"%(staging_dir)
        os.makedirs(staging_dir)

    if options.ramdisk:
        with TempRamFS(staging_dir, "25G"):
            test_debs(distro_name, stack_name, os_platform, arch, staging_dir, options.interactive, options.testresults)
    else:
        test_debs(distro_name, stack_name, os_platform, arch, staging_dir, options.interactive, options.testresults)
            
    if options.staging_dir is None:
        shutil.rmtree(staging_dir)
        
if __name__ == '__main__':
    test_debs_main()


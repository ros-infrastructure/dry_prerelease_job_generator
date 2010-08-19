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
    
def download_files(stack_name, stack_version, staging_dir, files):
    import urllib
    
    base_name = "%s-%s"%(stack_name, stack_version)

    dl_files = []

    for f_name in files:
        dest = os.path.join(staging_dir, f_name)
        url = TARBALL_URL%locals()
        urllib.urlretrieve(url, dest)
        dl_files.append(dest)

    return dl_files

def load_info(stack_name, stack_version):
    import urllib
    
    base_name = "%s-%s"%(stack_name, stack_version)
    f_name = base_name + '.yaml'

    url = TARBALL_URL%locals()

    return yaml.load(urllib2.urlopen(url))


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
    basedeps += ['libxml2-dev', 'swig']

    deplist = ' '.join(basedeps+ros_info['rosdeps'][os_platform])

    subprocess.check_call(['sudo', 'pbuilder', '--create', '--distribution', os_platform, '--debootstrapopts', '--arch=%s'%arch, '--othermirror', 'deb http://code.ros.org/packages/ros-shadow/ubuntu %s main'%(os_platform), '--basetgz', distro_tgz, '--components', 'main restricted universe multiverse', '--extrapackages', deplist])


def do_deb_build(distro_name, stack_name, stack_version, os_platform, arch, staging_dir):
    print "Actually trying to build %s..."%(stack_name)

    distro_tgz = os.path.join('/var/cache/pbuilder', "%s-%s.tgz"%(os_platform, arch))
    deb_name = "ros-%s-%s"%(distro_name, debianize_name(stack_name))
    deb_version = debianize_version(stack_version, '0', os_platform)
    ros_file = "%s-%s"%(stack_name, stack_version)
    deb_file = "%s_%s"%(deb_name, deb_version)

    # Make sure the distro chroot exists
    if not os.path.exists(distro_tgz):
        print >> sys.stderr, "%s does not exist."%(distro_tgz)
        sys.exit(1)

    # Download deb and tar.gz files:
    dsc_name = '%s.dsc'%(deb_file)
    tar_gz_name = '%s.tar.gz'%(deb_file)
    (dsc_file, tar_gz_file) = download_files(stack_name, stack_version, staging_dir, [dsc_name, tar_gz_name])

    # Create hook and results directories
    hook_dir = os.path.join(staging_dir, 'hooks')
    results_dir = os.path.join(staging_dir, 'results')

    if not os.path.exists(hook_dir):
        os.makedirs(hook_dir)

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    # Hook script which will download our tar.bz2 into environment
    p = os.path.join(hook_dir, 'A50fetch')
    with open(p, 'w') as f:
        f.write("""#!/bin/sh
set -o errexit
wget https://code.ros.org/svn/release/download/stacks/%(stack_name)s/%(stack_name)s-%(stack_version)s/%(stack_name)s-%(stack_version)s.tar.bz2 -O /tmp/buildd/%(stack_name)s-%(stack_version)s.tar.bz2"""%locals())
        os.chmod(p, stat.S_IRWXU)

    # Hook script which makes sure we have updated our apt cache
    p = os.path.join(hook_dir, 'D50update')
    with open(p, 'w') as f:
        f.write("""#!/bin/sh
set -o errexit
apt-get update"""%locals())
        os.chmod(p, stat.S_IRWXU)

    # Actually build the deb.  This results in the deb being located in results_dir
    subprocess.check_call(['sudo', 'pbuilder', '--build', '--basetgz', distro_tgz, '--hookdir', hook_dir, '--buildresult', results_dir, '--binary-arch', dsc_file])

    # Build a package db if we have to
    subprocess.check_call(['bash', '-c', 'cd %(staging_dir)s && dpkg-scanpackages . > %(results_dir)s/Packages'%locals()])

    # Script to execute for deb verification
    # TODO: Add code to run all the unit-tests for the deb!
    verify_script = os.path.join(staging_dir, 'verify_script.sh')
    with open(verify_script, 'w') as f:
        f.write("""#!/bin/sh
set -o errexit
echo "deb file:%(staging_dir)s results/" > /etc/apt/sources.list.d/pbuild.list
apt-get update
apt-get install %(deb_name)s=%(deb_version)s -y --force-yes
dpkg -l %(deb_name)s
"""%locals())
        os.chmod(verify_script, stat.S_IRWXU)

    # Run pbuilder to verify that the deb can be installed
    subprocess.check_call(['sudo', 'pbuilder', '--execute', '--basetgz', distro_tgz, '--bindmounts', results_dir, verify_script])

    # Upload the debs to the server
    base_files = [deb_file + x for x in ['_%s.deb'%(arch), '_%s.changes'%(arch)]]
    files = [os.path.join(results_dir, x) for x in base_files]
    subprocess.check_call(['scp'] + files + ['rosbuild@pub5:/var/packages/ros-shadow/ubuntu/incoming/%s'%os_platform])

    # Assemble string for moving all files from incoming to queue (while lock is being held)
    mvstr = '\n'.join(['mv '+os.path.join('/var/packages/ros-shadow/ubuntu/incoming',os_platform,x)+' '+os.path.join('/var/packages/ros-shadow/ubuntu/queue',os_platform,x) for x in base_files])

    # This script moves files into queue directory, removes all dependent debs, removes the existing deb, and then processes the incoming files
    remote_cmd = "TMPFILE=`mktemp` || exit 1 && cat > ${TMPFILE} && chmod +x ${TMPFILE} && ${TMPFILE}; ret=${?}; rm ${TMPFILE}; exit ${ret}"
    run_script = subprocess.Popen(['ssh', 'rosbuild@pub5', remote_cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    script_content = """
#!/bin/bash
set -o errexit
(
flock 200
# Move from incoming to queue
%(mvstr)s
# Remove all debs that depend on this package
cat /var/packages/ros-shadow/ubuntu/dists/%(os_platform)s/main/binary-%(arch)s/Packages | sed -nre 's/^Package: (.*)/\\1/;t hold;/^Depends: .*%(deb_name)s.*/{g;p};b;:hold h' | xargs -I{} reprepro -b /var/packages/ros-shadow/ubuntu -V -A %(arch)s removefilter %(os_platform)s 'Package (=={})'
# Remove this deb itself
reprepro -b /var/packages/ros-shadow/ubuntu -V -A %(arch)s removefilter %(os_platform)s 'Package (==%(deb_name)s)'
# Load it into the repo
reprepro -b /var/packages/ros-shadow/ubuntu -V processincoming %(os_platform)s
) 200>/var/lock/ros-shadow.lock
"""%locals()

    #Actually run script and check result
    (o,e) = run_script.communicate(script_content)
    res = run_script.wait()
    print o
    if res != 0:
        print >> sys.stderr, "Could not run upload script"
        print >> sys.stderr, o
        sys.exit(1)


def deb_in_repo(deb_name, deb_version, os_platform, arch):
    # Retrieve the package list from the shadow repo
    packageurl="http://code.ros.org/packages/ros-shadow/ubuntu/dists/%(os_platform)s/main/binary-%(arch)s/Packages"%locals()
    packagelist = urllib2.urlopen(packageurl).read()
    str = 'Package: %s\nVersion: %s'%(deb_name, deb_version)
    return str in packagelist


def build_debs(distro_name, stack_name, os_platform, arch, staging_dir, force):

    # Load the distro from the URL
    # TODO: Should this be done from file in release repo instead (and maybe updated in case of failure)
    distro_uri = "https://code.ros.org/svn/release/trunk/distros/%s.rosdistro"%distro_name
    distro = Distro(distro_uri)

    if stack_name != 'ALL' and stack_name not in distro.stacks:
        print >> sys.stderr, "[%s] not found in distro."%(stack_name)
        sys.exit(1)

    # Create the environment where we build the debs, if necessary
    create_chroot(distro, distro_name, os_platform, arch)

    # Find all the deps in the distro for this stack
    deps = compute_deps(distro, stack_name)

    broken = set()
    skipped = set()

    # Build the deps in order
    for (sn, sv) in deps:
        deb_name = "ros-%s-%s"%(distro_name, debianize_name(sn))
        deb_version = debianize_version(sv, '0', os_platform)
        if not deb_in_repo(deb_name, deb_version, os_platform, arch) or (force and sn == stack_name):
            si = load_info(sn, sv)
            if set(si['depends']).isdisjoint(broken.union(skipped)):
                try:
                    do_deb_build(distro_name, sn, sv, os_platform, arch, staging_dir)
                except:
                    broken.add(sn)
            else:
                print "Skipping %s (%s) since dependencies not built: %s"%(sn, sv, broken.union(skipped))
                skipped.add(sn)
        else:
            print "Skipping %s (%s) since already built."%(sn,sv)


    if broken.union(skipped):
        print >> sys.stderr, "Broken stacks: %s.  Skipped stacks: %s"%(broken, skipped)
        sys.exit(1)


def build_debs_main():

    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog <distro> <stack> <version> <os-platform>", prog=NAME)

    parser.add_option("-d", "--dir",
                      dest="staging_dir", default=None,
                      help="directory to use for staging source debs", metavar="STAGING_DIR")
    parser.add_option("--force",
                      dest="force", default=False, action="store_true")

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

    build_debs(distro_name, stack_name, os_platform, arch, staging_dir, options.force)

    if options.staging_dir is None:
        shutil.rmtree(staging_dir)
        
if __name__ == '__main__':
    build_debs_main()


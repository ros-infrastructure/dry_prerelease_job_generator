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
import urllib
import urllib2
import stat
import tempfile

import rosdeb
import rosdeb.targets

from rosdeb.rosutil import checkout_svn_to_tmp

from rosdistro import Distro
from rosdeb import ubuntu_release, debianize_name, debianize_version, \
    platforms, ubuntu_release_name, load_Packages, get_repo_version

import list_missing

NAME = 'stamp_versions.py' 
TARBALL_URL = "https://code.ros.org/svn/release/download/stacks/%(stack_name)s/%(base_name)s/%(f_name)s"
SOURCE_REPO='ros-shadow'
DEST_REPO='ros-shadow-fixed'
    
def parse_deb_packages(text):
    parsed = {}
    (key,val,pkg) = (None,'',{})
    count = 0
    for l in text.split('\n'):
        count += 1
        if len(l) == 0:
            if len(pkg) > 0:
                if not 'Package' in pkg:
                    print 'INVALID at %d'%count
                else:
                    if key:
                        pkg[key] = val
                    parsed[pkg['Package']] = pkg
                    (key,val,pkg) = (None,'',{})
        elif l[0].isspace():
            val += '\n'+l.strip()
        else:
            if key:
                pkg[key] = val
            (key, val) = l.split(':',1)
            key = key.strip()
            val = val.strip()

    return parsed


def create_meta_pkg(packagelist, distro, distro_name, metapackage, deps, os_platform, arch, staging_dir):
    workdir = staging_dir
    metadir = os.path.join(workdir, 'meta')
    if not os.path.exists(metadir):
        os.makedirs(metadir)
    debdir = os.path.join(metadir, 'DEBIAN')
    if not os.path.exists(debdir):
        os.makedirs(debdir)
    control_file = os.path.join(debdir, 'control')

    deb_name = "ros-%s-%s"%(distro_name, debianize_name(metapackage))
    deb_version = "1.0.0-%s~%s"%(distro.version, os_platform)

    ros_depends = []

    missing = False

    for stack in deps:
        if stack in distro.released_stacks:
            stack_deb_name = "ros-%s-%s"%(distro_name, stack.replace('_','-'))
            if stack_deb_name in packagelist:
                ros_depends.append(stack_deb_name)
            else:
                print >> sys.stderr, "Variant %s depends on non-built deb, %s"%(metapackage, stack)
                missing = True
        else:
            print >> sys.stderr, "Variant %s depends on non-exist stack, %s"%(metapackage, stack)
            missing = True

    ros_depends_str = ', '.join(ros_depends)

    with open(control_file, 'w') as f:
        f.write("""
Package: %(deb_name)s
Version: %(deb_version)s
Architecture: %(arch)s
Maintainer: The ROS community <ros-user@lists.sourceforge.net>
Installed-Size:
Depends: %(ros_depends_str)s
Section: unknown
Priority: optional
WG-rosdistro: %(distro_name)s
Description: Meta package for %(metapackage)s variant of ROS.
"""%locals())

    if not missing:
        dest_deb = os.path.join(workdir, "%(deb_name)s_%(deb_version)s_%(arch)s.deb"%locals())
        subprocess.check_call(['dpkg-deb', '--nocheck', '--build', metadir, dest_deb])
    else:
        dest_deb = None

    shutil.rmtree(metadir)
    return dest_deb


def upload_debs(files,distro_name,os_platform,arch):

    subprocess.check_call(['scp'] + files + ['rosbuild@pub8:/var/packages/%s/ubuntu/incoming/%s'%(DEST_REPO,os_platform)])

    base_files = [x.split('/')[-1] for x in files]

    # Assemble string for moving all files from incoming to queue (while lock is being held)
    mvstr = '\n'.join(['mv '+os.path.join('/var/packages/%s/ubuntu/incoming'%(DEST_REPO),os_platform,x)+' '+os.path.join('/var/packages/%s/ubuntu/queue'%(DEST_REPO),os_platform,x) for x in base_files])
    new_files = ' '.join(os.path.join('/var/packages/%s/ubuntu/queue'%(DEST_REPO),os_platform,x) for x in base_files)

    # hacky
    dest_repo = DEST_REPO

    # This script moves files into queue directory, removes all dependent debs, removes the existing deb, and then processes the incoming files
    remote_cmd = "TMPFILE=`mktemp` || exit 1 && cat > ${TMPFILE} && chmod +x ${TMPFILE} && ${TMPFILE}; ret=${?}; rm ${TMPFILE}; exit ${ret}"
    run_script = subprocess.Popen(['ssh', 'rosbuild@pub8', remote_cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    script_content = """
#!/bin/bash
set -o errexit
(
flock 200
# Move from incoming to queue
%(mvstr)s
reprepro -V -b /var/packages/%(dest_repo)s/ubuntu includedeb %(os_platform)s %(new_files)s
rm %(new_files)s
) 200>/var/lock/ros-shadow.lock
"""%locals()

    #Actually run script and check result
    (o,e) = run_script.communicate(script_content)
    res = run_script.wait()
    print o
    if res != 0:
        print >> sys.stderr, "Could not run upload script"
        print >> sys.stderr, o
        return 1
    else:
        return 0


def load_distro(distro_name):
    # Load the distro from the URL
    distro_uri = "https://code.ros.org/svn/release/trunk/distros/%s.rosdistro"%distro_name
    return Distro(distro_uri)
    
def gen_metapkgs(distro, os_platform, arch, staging_dir, force=False):
    distro_name = distro.release_name

    # Retrieve the package list from the shadow-fixed repo
    packageurl="http://packages.ros.org/ros-shadow-fixed/ubuntu/dists/%(os_platform)s/main/binary-%(arch)s/Packages"%locals()
    packagetxt = urllib2.urlopen(packageurl).read()
    packagelist = parse_deb_packages(packagetxt)

    debs = []

    missing = False

    missing_primary, missing_dep, missing_excluded, missing_excluded_dep = list_missing.get_missing(distro, os_platform, arch)

    missing_ok = missing_excluded.union(missing_excluded_dep)

    # Build the new meta packages
    for (v,d) in distro.variants.iteritems():
        mp = create_meta_pkg(packagelist, distro, distro_name, v, set(d.stack_names) - missing_ok, os_platform, arch, staging_dir)
        if mp:
            debs.append(mp)
        else:
            missing = True

    # Build the special "all" metapackage
    mp = create_meta_pkg(packagelist, distro, distro_name, "all", set(distro.released_stacks.keys()) - missing_ok, os_platform, arch, staging_dir)
    if mp:
        debs.append(mp)
    else:
        missing = True

    if not missing or force:
        return upload_debs(debs, distro_name, os_platform, arch)
    else:
        print >> sys.stderr, "Missing debs expected from distro file.  Aborting"
        print >> sys.stderr, "Missing: %s"%(missing)
        return 1

def gen_metapkgs_main():

    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog <distro> <os-platform> <arch>", prog=NAME)

    parser.add_option("-d", "--dir",
                      dest="staging_dir", default=None,
                      help="directory to use for staging source debs", metavar="STAGING_DIR")
    parser.add_option("--force",
                      dest="force", default=False, action="store_true")
    parser.add_option("--all", help="stamp all os/arch combinations",
                      dest="all", default=False, action="store_true")

    (options, args) = parser.parse_args()

    if not options.all:
        if len(args) != 3:
            parser.error('invalid args')
    elif len(args) != 1:
        parser.error('invalid args. please only specify a distro name')
    distro_name = args[0]

    if not options.all:
        to_stamp = [args]
    else:
        try:
            platforms = rosdeb.targets.os_platform[distro_name]
        except:
            parser.error("unknown distro [%s]"%(distro_name))
        to_stamp = []
        for os_platform in platforms:
            for arch in ['i386', 'amd64']:
                to_stamp.append((distro_name, os_platform, arch))

    failed = 0

    for distro_name, os_platform, arch in to_stamp:

        # create and delete staging_dir per distro so as to not flood
        # the tmp dir
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

        distro = load_distro(distro_name)

        # compare versions
        failed += gen_metapkgs(distro, os_platform, arch, staging_dir, options.force)

        if options.staging_dir is None:
            shutil.rmtree(staging_dir)

    sys.exit(failed)
        
if __name__ == '__main__':
    gen_metapkgs_main()


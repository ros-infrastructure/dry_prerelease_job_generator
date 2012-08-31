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
import re
import time

from rospkg.distro import distro_uri, load_distro
import rosdeb
from rosdeb import ubuntu_release, debianize_name, debianize_version, \
    platforms, ubuntu_release_name, load_Packages, get_repo_version, targets
from rosdeb.rosutil import send_email
from rosdeb.source_deb import download_control

import list_missing

NAME = 'build_debs.py' 
TARBALL_URL = "https://code.ros.org/svn/release/download/stacks/%(stack_name)s/%(base_name)s/%(f_name)s"


REPO_URL='http://50.28.27.175/repos/building'

REPO_HOSTNAME='50.28.27.175'
REPO_PATH ='/var/www/repos/building'
REPO_USERNAME='rosbuild'

TGZ_VERSION='dry_4'

import traceback

class StackBuildFailure(Exception):

    def __init__(self, message):
        self._message = message
    def __str__(self):
       return self._message

class BuildFailure(Exception):

    def __init__(self, message):
        self._message = message
    def __str__(self):
        return self._message

class InternalBuildFailure(Exception):

    def __init__(self, message):
        self._message = message
    def __str__(self):
        return self._message

    
def deb_in_repo(deb_name, deb_version, os_platform, arch, cache=None):
    return rosdeb.deb_in_repo(REPO_URL, deb_name, deb_version, os_platform, arch, use_regex=True, cache=cache)

def get_depends(deb_name, os_platform, arch):
    debug("get_depends from %s"%(REPO_URL))
    return rosdeb.get_depends(REPO_URL, deb_name, os_platform, arch)
    
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
    try:
        return download_control(stack_name, stack_version)
    except:
        traceback.print_exc()
        raise BuildFailure("Problem fetching yaml info for %s %s.\nThis yaml info is usually created when a release is uploaded. If it is missing, either the stack version is wrong, or the release did not occur correctly."%(stack_name, stack_version))

def compute_deps(distro, stack_name):

    seen = set()
    ordered_deps = []

    def add_stack(s):
        if s in seen:
            return
        if s not in distro.released_stacks:
            # ignore, possibly catkinized
            return
        seen.add(s)
        v = distro.released_stacks[s].version
        if not v:
            raise BuildFailure("[%s] has not been released (version-less)."%(s))
        # version-less entries are ignored
        si = load_info(s, v)
        loaded_deps = si['depends']
        for d in loaded_deps:
            try:
                add_stack(d)
            except BuildFailure as e:
                raise BuildFailure("[%s] build failure loading dependency [%s]: %s"%(s, d, e))
        ordered_deps.append((s,v))

    if stack_name == 'ALL':
        for s in distro.released_stacks.keys():
            try:
                add_stack(s)
            except BuildFailure as e:
                print "WARNING: Failed loading stack [%s] removing from ALL.  Error:\n%s"%(s, e)
                
    else:
        add_stack(stack_name)

    return ordered_deps

def create_chroot(distro, distro_name, os_platform, arch):

    distro_tgz = os.path.join('/var/cache/pbuilder', "%s-%s-%s.tgz"%(os_platform, arch, TGZ_VERSION))
    cache_dir = '/home/rosbuild/aptcache/%s-%s'%(os_platform, arch)

    if os.path.exists(distro_tgz) and os.path.getsize(distro_tgz) > 0:  # Zero sized file left in place if last build crashed
        return

    debug("re-creating pbuilder cache")

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    try:
        debug('loading ros stack info')
        ros_info = load_info('ros', distro.released_stacks['ros'].version)
        debug('loaded ros stack info: %s'%(ros_info))
    except:
        # mock in data if we are in fuerte+
        ros_info = {'rosdeps': {os_platform: []}}

    # force update of apt index
    subprocess.check_call(['sudo', 'apt-get', 'update'], stderr=subprocess.STDOUT)
    
    # Things that this build infrastructure depends on
    basedeps = ['wget', 'lsb-release', 'debhelper']
    # Deps we claimed to have needed for building ROS
    # TODO:FIXME: remove pkg-config
    basedeps += ['build-essential', 'python-yaml', 'cmake', 'subversion', 'python-setuptools', 'pkg-config']
    # Extra deps that some stacks seem to be missing
    basedeps += ['libxml2-dev', 'libtool', 'unzip']
    # For debugging
    basedeps += ['strace']

    rosdeps = ros_info['rosdeps']
    # hack due to bug in ubuntu_platform map
    if os_platform == 'maverick' and 'mighty' in rosdeps:
        rosdeps = rosdeps['mighty']
    else:
        rosdeps = rosdeps[os_platform]

    deplist = ' '.join(basedeps+rosdeps)

    debootstrap_type = 'debootstrap' # use default
    mirror = 'http://aptproxy.willowgarage.com/archive.ubuntu.com/ubuntu' # use wg mirror
    if arch == 'armel':
        debootstrap_type = 'qemu-debootstrap'
        mirror = 'http://ports.ubuntu.com/ubuntu-ports/'
    shadow_mirror = 'deb %s %s main' % (REPO_URL, os_platform)
    updates_mirror = "deb http://aptproxy.willowgarage.com/us.archive.ubuntu.com/ubuntu/ %s-updates main restricted"%(os_platform)
    # --othermirror uses a | as a separator
    other_mirror = '%s|%s'%(updates_mirror, shadow_mirror)
    command = ['dpkg', '-l', 'pbuilder']
    debug("pbuilder verison : [%s]"%(str(command)))
    subprocess.check_call(command, stderr=subprocess.STDOUT)

    command = ['sudo', 'pbuilder', '--create', '--distribution', os_platform, '--debootstrap', debootstrap_type, '--debootstrapopts', '--arch=%s'%arch, '--mirror', mirror, '--othermirror', other_mirror, '--basetgz', distro_tgz, '--components', 'main restricted universe multiverse', '--extrapackages', deplist, '--aptcache', cache_dir]
    command.extend(['--debootstrapopts', '--keyring=/etc/apt/trusted.gpg', '--keyring', '/etc/apt/trusted.gpg'])
    debug("Setting up chroot: [%s]"%(str(command)))
    subprocess.check_call(command, stderr=subprocess.STDOUT)


def do_deb_build(distro_name, stack_name, stack_version, os_platform, arch, staging_dir, noupload, interactive):
    debug("Actually trying to build %s-%s..."%(stack_name, stack_version))

    distro_tgz = os.path.join('/var/cache/pbuilder', "%s-%s-%s.tgz"%(os_platform, arch, TGZ_VERSION))
    cache_dir = '/home/rosbuild/aptcache/%s-%s'%(os_platform, arch)

    deb_name = "ros-%s-%s"%(distro_name, debianize_name(stack_name))
    deb_version = debianize_version(stack_version, '0', os_platform)
    ros_file = "%s-%s"%(stack_name, stack_version)
    deb_file = "%s_%s"%(deb_name, deb_version)

    conf_file = os.path.join(roslib.packages.get_pkg_dir('rosdeb'),'config','pbuilder.conf')

    # Make sure the distro chroot exists
    if not os.path.exists(distro_tgz):
        raise InternalBuildFailure("%s does not exist."%(distro_tgz))

    # Download deb and tar.gz files:
    dsc_name = '%s.dsc'%(deb_file)
    tar_gz_name = '%s.tar.gz'%(deb_file)

    (dsc_file, tar_gz_file) = download_files(stack_name, stack_version, staging_dir, [dsc_name, tar_gz_name])

    # Create hook and results directories
    hook_dir = os.path.join(staging_dir, 'hooks')
    results_dir = os.path.join(staging_dir, 'results')
    build_dir = os.path.join(staging_dir, 'pbuilder')

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    if not os.path.exists(hook_dir):
        os.makedirs(hook_dir)

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

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

    if interactive:

        # Hook scripts to make us interactive:
        p = os.path.join(hook_dir, 'B50interactive')
        with open(p, 'w') as f:
            f.write("""#!/bin/sh
echo "Entering interactive environment.  Exit when done to continue pbuilder operation."
export ROS_DESTDIR=/tmp/buildd/%(deb_name)s-%(stack_version)s/debian/%(deb_name)s
source /tmp/buildd/%(deb_name)s-%(stack_version)s/setup_deb.sh
roscd %(stack_name)s
bash </dev/tty
echo "Resuming pbuilder"
"""%locals())
            os.chmod(p, stat.S_IRWXU)

        # Hook scripts to make us interactive:
        p = os.path.join(hook_dir, 'C50interactive')
        with open(p, 'w') as f:
            f.write("""#!/bin/sh
echo "Entering interactive environment.  Exit when done to continue pbuilder operation."
export ROS_DESTDIR=/tmp/buildd/%(deb_name)s-%(stack_version)s/debian/%(deb_name)s
source /tmp/buildd/%(deb_name)s-%(stack_version)s/setup_deb.sh
roscd %(stack_name)s
bash </dev/tty
echo "Resuming pbuilder"
"""%locals())
            os.chmod(p, stat.S_IRWXU)


    if arch == 'amd64' or arch == 'armel':
        archcmd = []
    else:
        archcmd = ['setarch', arch]

    # Actually build the deb.  This results in the deb being located in results_dir
    debug("starting pbuilder build of %s-%s"%(stack_name, stack_version))
    subprocess.check_call(archcmd+ ['sudo', 'pbuilder', '--build', '--basetgz', distro_tgz, '--configfile', conf_file, '--hookdir', hook_dir, '--buildresult', results_dir, '--binary-arch', '--buildplace', build_dir, '--aptcache', cache_dir, dsc_file], stderr=subprocess.STDOUT)

    # Set up an RE to look for the debian file and find the build_version
    deb_version_wild = debianize_version(stack_version, '(\w*)', os_platform)
    deb_file_wild = "%s_%s_%s\.deb"%(deb_name, deb_version_wild, arch)
    build_version = None

    # Extract the version number we just built:
    files = os.listdir(results_dir)

    for f in files:
        M = re.match(deb_file_wild, f)
        if M:
            build_version = M.group(1)

    if not build_version:
        raise InternalBuildFailure("No deb-file generated matching template: %s"%deb_file_wild)

    deb_version_final = debianize_version(stack_version, build_version, os_platform)
    deb_file_final = "%s_%s"%(deb_name, deb_version_final)

    # Build a package db if we have to
    debug("starting package db build of %s-%s"%(stack_name, stack_version))
    subprocess.check_call(['bash', '-c', 'cd %(staging_dir)s && dpkg-scanpackages . > %(results_dir)s/Packages'%locals()])


    # Script to execute for deb verification
    # TODO: Add code to run all the unit-tests for the deb!
    verify_script = os.path.join(staging_dir, 'verify_script.sh')
    with open(verify_script, 'w') as f:
        f.write("""#!/bin/sh
set -o errexit
echo "deb file:%(staging_dir)s results/" > /etc/apt/sources.list.d/pbuild.list
apt-get update
apt-get install %(deb_name)s=%(deb_version_final)s -y --force-yes
dpkg -l %(deb_name)s
"""%locals())
        os.chmod(verify_script, stat.S_IRWXU)
            


    debug("starting verify script for %s-%s"%(stack_name, stack_version))
    subprocess.check_call(archcmd + ['sudo', 'pbuilder', '--execute', '--basetgz', distro_tgz, '--configfile', conf_file, '--bindmounts', results_dir, '--buildplace', build_dir, '--aptcache', cache_dir, verify_script], stderr=subprocess.STDOUT)

    # Upload the debs to the server
    base_files = ['%s_%s.changes'%(deb_file, arch)] # , "%s_%s.deb"%(deb_file_final, arch)
    files = [os.path.join(results_dir, x) for x in base_files]
    print "Generated debian change files: %s" % files




    if not noupload:
        replace_elements  = {}
        replace_elements['repo_hostname'] = REPO_HOSTNAME
        replace_elements['repo_incoming_path'] = os.path.join(REPO_PATH, 'queue', os_platform)
        replace_elements['repo_path'] = os.path.join(REPO_PATH, os_platform)
        replace_elements['distro'] = os_platform

        try:
            tf_name = None
            with tempfile.NameTemporaryFile(delete=False)  as tf:
                tf.write("""
[debtarget]
method                  = scp
fqdn                    = %(repo_hostname)s
incoming                = %(repo_path)s
run_dinstall            = 0
post_upload_command     = ssh %(repo_username)@@%(repo_hostname)s -- /usr/bin/reprepro -b %(repo_path) --ignore=emptyfilenamepart -V processincoming %(distro)s
""" % replace_elements)
                tf_name = tf.name
            
            p = subprocess.call(['cat', tf_name])
        finally:
            if tf_name:
                if os.path.exists(tf_name):
                    os.remove(tf_name)

            
            # The cache is no longer valid, we clear it so that we won't skip debs that have been invalidated
            # ??? What was this doing?
            #rosdeb.repo._Packages_cache = {}

def lock_debs(distro, os_platform, arch):

        remote_cmd = "TMPFILE=`mktemp` || exit 1 && cat > ${TMPFILE} && chmod +x ${TMPFILE} && ${TMPFILE}; ret=${?}; rm ${TMPFILE}; exit ${ret}"
        run_script = subprocess.Popen(['ssh', REPO_LOGIN, remote_cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        platform_upper = os_platform.upper()

        # This script:
        #  * Sets up the update to pull the os/distro/arch set that we want
        #  * Purges all of the existing os/distro/arch debs from the repo
        #  * Invokes the update to pull down the new debs
        script_content = """
#!/bin/bash
set -o errexit
(
flock 200
export %(platform_upper)s_UPDATE=ros-%(os_platform)s-%(distro)s-%(arch)s
/var/packages/ros-shadow-fixed/ubuntu/conf/gen_distributions.sh > /var/packages/ros-shadow-fixed/ubuntu/conf/distributions
reprepro -V -b /var/packages/ros-shadow-fixed/ubuntu -A %(arch)s removefilter %(os_platform)s 'Package (%% ros-%(distro)s-*)'
reprepro -V -b /var/packages/ros-shadow-fixed/ubuntu --noskipold update %(os_platform)s
) 200>/var/lock/ros-shadow.lock
"""%locals()

        #Actually run script and check result
        debug("locking debs into fixed repo: \n[[[%s]]]"%(script_content))
        (o,e) = run_script.communicate(script_content)
        res = run_script.wait()
        debug("output of run_script: %s"%o)
        if res != 0:
            raise InternalBuildFailure("Could not run version-locking script:\n%s\n%s"%(o, e))

def debug(msg):
    print "[build_debs]: %s"%(msg)
    
    
def build_debs(distro, stack_name, os_platform, arch, staging_dir, force, noupload, interactive):
    distro_name = distro.release_name

    if stack_name not in distro.released_stacks:
        raise BuildFailure("stack [%s] not found in distro [%s]."%(stack_name, distro_name))

    # Create the environment where we build the debs, if necessary
    create_chroot(distro, distro_name, os_platform, arch)
    subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'pkg-config'])

    # Load blacklisted information
    missing_primary, missing_dep, missing_excluded, missing_excluded_dep = list_missing.get_missing(distro, os_platform, arch)
    missing_ok = missing_excluded.union(missing_excluded_dep)

    try:
        stack_version = distro.released_stacks[stack_name].version
    except KeyError, ex:
        debug("Stack [%s] is not in in the distro: %s" % (stack_name, ex) )

    
    broken = set()
    skipped = set()


    debug("Attempting to build: %s"%(str(stack_name)))
    si = load_info(stack_name, stack_version)
    depends = set(si['depends'])
    if depends.isdisjoint(broken.union(skipped)):
        debug("Initiating build of: %s"%(str(stack_name)))
        try:
            do_deb_build(distro_name, stack_name, stack_version, os_platform, arch, staging_dir, noupload, interactive)
        except Exception, ex:
            debug("Exception was %s" % ex)
            debug("Build of [%s] failed, adding to broken list"%(str(stack_name)))
            broken.add(stack_name)
    else:
        debug("Skipping %s (%s) since dependencies not built: %s"%(stack_name, sv, broken.union(skipped)&depends))
        skipped.add(stack_name)

    if broken.union(skipped):
        raise StackBuildFailure("debbuild did not complete successfully. A list of broken and skipped stacks are below. Broken means the stack itself did not build. Skipped stacks means that the stack's dependencies could not be built.\n\nBroken stacks: %s.  Skipped stacks: %s"%(broken, skipped))

EMAIL_FROM_ADDR = 'ROS debian build system <noreply@willowgarage.com>'


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
    deb_version = "1.0.0-s%d~%s"%(time.mktime(time.gmtime()), os_platform)

    ros_depends = []

    missing = False

    for stack in deps:
        if stack in distro.released_stacks:
            stack_deb_name = "ros-%s-%s"%(distro_name, debianize_name(stack))
            if stack_deb_name in packagelist:
                stack_deb_version = packagelist[stack_deb_name]['Version']
                ros_depends.append('%s (= %s)'%(stack_deb_name, stack_deb_version))
            else:
                debug("WARNING: Variant %s depends on non-built deb, %s"%(metapackage, stack))
                missing = True
        else:
            debug("WARNING: Variant %s depends on non-exist stack, %s"%(metapackage, stack))
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
        subprocess.check_call(['dpkg-deb', '--nocheck', '--build', metadir, dest_deb], stderr=subprocess.STDOUT)
    else:
        dest_deb = None

    shutil.rmtree(metadir)
    return dest_deb


def upload_debs(files,distro_name,os_platform,arch):

    if len(files) == 0:
        debug("No debs to upload.")
        return 1 # no files to upload

#    subprocess.check_call(['scp'] + files + ['%s:/var/packages/%s/ubuntu/incoming/%s'%(REPO_LOGIN, SHADOW_REPO,os_platform)], stderr=subprocess.STDOUT)

#    base_files = [x.split('/')[-1] for x in files]

    # Assemble string for moving all files from incoming to queue (while lock is being held)
#    mvstr = '\n'.join(['mv '+os.path.join('/var/packages/%s/ubuntu/incoming'%(SHADOW_REPO),os_platform,x)+' '+os.path.join('/var/packages/%s/ubuntu/queue'%(SHADOW_REPO),os_platform,x) for x in base_files])
#    new_files = ' '.join(os.path.join('/var/packages/%s/ubuntu/queue'%(SHADOW_REPO),os_platform,x) for x in base_files)

    # hacky
#    shadow_repo = SHADOW_REPO

    # This script moves files into queue directory, removes all dependent debs, removes the existing deb, and then processes the incoming files
#    remote_cmd = "TMPFILE=`mktemp` || exit 1 && cat > ${TMPFILE} && chmod +x ${TMPFILE} && ${TMPFILE}; ret=${?}; rm ${TMPFILE}; exit ${ret}"
#    run_script = subprocess.Popen(['ssh', REPO_LOGIN, remote_cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    script_content = """
#!/bin/bash
set -o errexit
(
flock 200
# Move from incoming to queue
%(mvstr)s
reprepro -V -b /var/packages/%(shadow_repo)s/ubuntu includedeb %(os_platform)s %(new_files)s
rm %(new_files)s
) 200>/var/lock/ros-shadow.lock
"""%locals()

    #Actually run script and check result
#    (o,e) = run_script.communicate(script_content)
#    res = run_script.wait()
#    debug("result of run script: %s"%o)
#    if res != 0:
#        debug("ERROR: Could not run upload script")
#        debug("ERROR: output of upload script: %s"%o)
#        return 1
#    else:
#        return 0

def gen_metapkgs(distro, os_platform, arch, staging_dir, force=False):
    distro_name = distro.release_name

    # Retrieve the package list from the shadow repo
    packageurl="http://packages.ros.org/ros-shadow/ubuntu/dists/%(os_platform)s/main/binary-%(arch)s/Packages"%locals()
    packagetxt = urllib2.urlopen(packageurl).read()
    packagelist = parse_deb_packages(packagetxt)

    debs = []

    missing = []

    missing_primary, missing_dep, missing_excluded, missing_excluded_dep = list_missing.get_missing(distro, os_platform, arch)

    missing_ok = missing_excluded.union(missing_excluded_dep)

    
    # if (metapkg missing) or (metapkg missing deps), then create
    # modify create to version-lock deps

    # Build the new meta packages
    for (v,d) in distro.variants.iteritems():

        deb_name = "ros-%s-%s"%(distro_name, debianize_name(v))

        # If the metapkg is in the packagelist AND already has the right deps, we leave it:
        if deb_name in packagelist:
            list_deps = set([x.split()[0].strip() for x in packagelist[deb_name]['Depends'].split(',')])
            mp_deps = set(["ros-%s-%s"%(distro_name, debianize_name(x)) for x in set(d.stack_names) - missing_ok])
            if list_deps == mp_deps:
                debug("Metapackage %s already has correct deps"%deb_name)
                continue

        # Else, we create the new metapkg
        mp = create_meta_pkg(packagelist, distro, distro_name, v, set(d.stack_names) - missing_ok, os_platform, arch, staging_dir)
        if mp:
            debs.append(mp)
        else:
            missing.append(v)

    # We should always need to build the special "all" metapackage
    mp = create_meta_pkg(packagelist, distro, distro_name, "all", set(distro.released_stacks.keys()) - missing_ok, os_platform, arch, staging_dir)
    if mp:
        debs.append(mp)
    else:
        missing.append('all')

    upload_debs(debs, distro_name, os_platform, arch)

    if missing:
        raise StackBuildFailure("Did not generate all metapkgs: %s."%missing)


def single_deb_main():

    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog <distro> <stack> <os-platform> <arch>", prog=NAME)

    parser.add_option("-d", "--dir",
                      dest="staging_dir", default=None,
                      help="directory to use for staging source debs", metavar="STAGING_DIR")
    parser.add_option("--force",
                      dest="force", default=False, action="store_true")
    parser.add_option("--noupload",
                      dest="noupload", default=False, action="store_true")
#    parser.add_option("--repo",
#                      dest="repo-hostname", default='pub8', action="store")
    parser.add_option("--interactive",
                      dest="interactive", default=False, action="store_true")
    parser.add_option('--smtp', dest="smtp", default='pub1.willowgarage.com', metavar="SMTP_SERVER")

    (options, args) = parser.parse_args()

    if len(args) != 4:
        parser.error('invalid args')
        
    (distro_name, stack_name, os_platform, arch) = args
    distro = failure_message = warning_message = None

    if options.staging_dir is not None:
        staging_dir    = options.staging_dir
        staging_dir = os.path.abspath(staging_dir)
    else:
        staging_dir = tempfile.mkdtemp()

    try:
        if distro_name not in rosdeb.targets.os_platform:
            raise BuildFailure("[%s] is not a known rosdistro.\nValid rosdistros are: %s" % (distro_name, ' '.join(rosdeb.targets.os_platform.keys())))
        target_platforms = rosdeb.targets.os_platform[distro_name]
        if os_platform not in target_platforms:
            raise BuildFailure("[%s] is not a known platformfor distro %s.\nSupported platforms are: %s" % (os_platform, distro_name, ' '.join(target_platforms)))

        if not os.path.exists(staging_dir):
            debug("creating staging dir: %s"%(staging_dir))
            os.makedirs(staging_dir)

        uri = distro_uri(distro_name)
        debug("loading distro file from %s"%(uri))
        distro = load_distro(uri)
        
        build_debs(distro, stack_name, os_platform, arch, staging_dir, options.force, options.noupload, options.interactive)

    except StackBuildFailure, e:
        warning_message = "Warning Message:\n"+"="*80+'\n'+str(e)
    except BuildFailure, e:
        failure_message = "Failure Message:\n"+"="*80+'\n'+str(e)
    except Exception, e:
        failure_message = "Internal failure release system. Please notify leibs and kwc @willowgarage.com:\n%s\n\n%s"%(e, traceback.format_exc(e))
    finally:
        # if we created our own staging dir, we are responsible for cleaning it up
        if options.staging_dir is None:
            shutil.rmtree(staging_dir)
            

    # Try to create metapkgs as necessary
    if not failure_message and stack_name == 'ALL':

        if options.staging_dir is not None:
            staging_dir    = options.staging_dir
            staging_dir = os.path.abspath(staging_dir)
        else:
            staging_dir = tempfile.mkdtemp()

        try:
            gen_metapkgs(distro, os_platform, arch, staging_dir)
        except BuildFailure, e:
            failure_message = "Failure Message:\n"+"="*80+'\n'+str(e)
        except StackBuildFailure, e:
            warning_message = "Warning Message:\n"+"="*80+'\n'+str(e)
        except Exception, e:
            failure_message = "Internal failure in the release system. Please notify leibs and kwc @willowgarage.com:\n%s\n\n%s"%(e, traceback.format_exc(e))
        finally:
            if options.staging_dir is None:
                shutil.rmtree(staging_dir)


    if failure_message or warning_message:
        debug("FAILURE: %s"%failure_message)
        debug("WARNING: %s"%warning_message)

        if not options.interactive:
            failure_message = "%s\n%s\n%s"%(failure_message, warning_message, os.environ.get('BUILD_URL', ''))
            if options.smtp and stack_name != 'ALL' and distro is not None:
                stack_version = distro.stacks[stack_name].version
                control = download_control(stack_name, stack_version)
                if  'contact' in control and distro_name != 'diamondback':
                    to_addr = control['contact']
                    subject = 'debian build [%s-%s-%s-%s] failed'%(distro_name, stack_name, os_platform, arch)
                    send_email(options.smtp, EMAIL_FROM_ADDR, to_addr, subject, failure_message)
        sys.exit(1)
            

    
if __name__ == '__main__':
    single_deb_main()


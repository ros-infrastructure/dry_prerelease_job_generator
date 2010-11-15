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
from rosdeb.rosutil import checkout_svn_to_tmp, send_email

from rosdistro import Distro
from rosdeb.core import ubuntu_release, debianize_name, debianize_version, platforms, ubuntu_release_name
from rosdeb.source_deb import download_control

from rosdeb import get_repo_version

import list_missing
import stamp_versions

NAME = 'build_debs.py' 
TARBALL_URL = "https://code.ros.org/svn/release/download/stacks/%(stack_name)s/%(base_name)s/%(f_name)s"
SHADOW_REPO="http://code.ros.org/packages/ros-shadow/"

import traceback

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

    
def deb_in_repo(deb_name, deb_version, os_platform, arch):
    return rosdeb.deb_in_repo(SHADOW_REPO, deb_name, deb_version, os_platform, arch)

def get_depends(deb_name, os_platform, arch):
    return rosdeb.get_depends(SHADOW_REPO, deb_name, os_platform, arch)
    
def download_files(stack_name, stack_version, staging_dir, files):
    import urllib
    
    base_name = "%s-%s"%(stack_name, stack_version)

    dl_files = []

    for f_name in files:
        dest = os.path.join(staging_dir, f_name)
        url = TARBALL_URL%locals()
        try:
            urllib.urlretrieve(url, dest)
        except Exception,e:
            print e
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
        if s not in distro.stacks:
            raise BuildFailure("[%s] not found in distro."%(s))
        seen.add(s)
        v = distro.stacks[s].version
        if v:
            # version-less entries are ignored
            si = load_info(s, v)
            for d in si['depends']:
                add_stack(d)
            ordered_deps.append((s,v))

    if stack_name == 'ALL':
        for s in distro.stacks.keys():
            add_stack(s)
    else:
        add_stack(stack_name)

    # #3100: REMOVE THIS AROUND PHASE 3
    if distro.release_name == 'unstable':
        if stack_name not in ['ros', 'ros_comm', 'documentation'] and 'ros_comm' not in ordered_deps:
            ordered_deps.append(('ros_comm', distro.stacks['ros_comm'].version))
    # END #3100
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

    subprocess.check_call(['sudo', 'pbuilder', '--create', '--distribution', os_platform, '--debootstrapopts', '--arch=%s'%arch, '--othermirror', 'deb http://code.ros.org/packages/ros-shadow/ubuntu %s main'%(os_platform), '--basetgz', distro_tgz, '--components', 'main restricted universe multiverse', '--extrapackages', deplist])


def do_deb_build(distro_name, stack_name, stack_version, os_platform, arch, staging_dir, noupload, interactive):
    print "Actually trying to build %s-%s..."%(stack_name, stack_version)

    distro_tgz = os.path.join('/var/cache/pbuilder', "%s-%s.tgz"%(os_platform, arch))
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
bash </dev/tty
echo "Resuming pbuilder"
"""%locals())
            os.chmod(p, stat.S_IRWXU)

        # Hook scripts to make us interactive:
        p = os.path.join(hook_dir, 'C50interactive')
        with open(p, 'w') as f:
            f.write("""#!/bin/sh
echo "Entering interactive environment.  Exit when done to continue pbuilder operation."
bash </dev/tty
echo "Resuming pbuilder"
"""%locals())
            os.chmod(p, stat.S_IRWXU)


    if arch == 'amd64':
        archcmd = []
    else:
        archcmd = ['setarch', arch]

    # Actually build the deb.  This results in the deb being located in results_dir
    print "starting pbuilder build of %s-%s"%(stack_name, stack_version)
    subprocess.check_call(archcmd+ ['sudo', 'pbuilder', '--build', '--basetgz', distro_tgz, '--configfile', conf_file, '--hookdir', hook_dir, '--buildresult', results_dir, '--binary-arch', '--buildplace', build_dir, dsc_file])

    # Build a package db if we have to
    print "starting package db build of %s-%s"%(stack_name, stack_version)
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

            
    print "starting verify script for %s-%s"%(stack_name, stack_version)
    subprocess.check_call(archcmd + ['sudo', 'pbuilder', '--execute', '--basetgz', distro_tgz, '--configfile', conf_file, '--bindmounts', results_dir, '--buildplace', build_dir, verify_script])

    if not noupload:
        # Upload the debs to the server
        base_files = [deb_file + x for x in ['_%s.deb'%(arch), '_%s.changes'%(arch)]]
        files = [os.path.join(results_dir, x) for x in base_files]
    
        print "uploading debs for %s-%s to pub5"%(stack_name, stack_version)
        subprocess.check_call(['scp'] + files + ['rosbuild@pub5:/var/packages/ros-shadow/ubuntu/incoming/%s'%os_platform])

        # Assemble string for moving all files from incoming to queue (while lock is being held)
        move_str = '\n'.join(['mv '+os.path.join('/var/packages/ros-shadow/ubuntu/incoming',os_platform,x)+' '+os.path.join('/var/packages/ros-shadow/ubuntu/queue',os_platform,x) for x in base_files])

        # This script moves files into queue directory, removes all dependent debs, removes the existing deb, and then processes the incoming files
        remote_cmd = "TMPFILE=`mktemp` || exit 1 && cat > ${TMPFILE} && chmod +x ${TMPFILE} && ${TMPFILE}; ret=${?}; rm ${TMPFILE}; exit ${ret}"
        run_script = subprocess.Popen(['ssh', 'rosbuild@pub5', remote_cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        invalidate = [deb_name] + get_depends(deb_name, os_platform, arch)
        invalidate_cmds = ["reprepro -b /var/packages/ros-shadow/ubuntu -V -A %(arch)s removefilter %(os_platform)s 'Package (==%(deb_name_x)s)'"%locals() for deb_name_x in  invalidate]
        invalidate_str = "\n".join(invalidate_cmds)
        script_content = """
#!/bin/bash
set -o errexit
(
flock 200
# Move from incoming to queue
%(move_str)s
# Remove all debs that depend on this package
%(invalidate_str)s
# Load it into the repo
reprepro -b /var/packages/ros-shadow/ubuntu -V processincoming %(os_platform)s
) 200>/var/lock/ros-shadow.lock
"""%locals()

        #Actually run script and check result
        (o,e) = run_script.communicate(script_content)
        res = run_script.wait()
        print o
        if res != 0:
            raise InternalBuildFailure("Could not run upload script:\n%s\n%s"%(o, e))

def build_debs(distro, stack_name, os_platform, arch, staging_dir, force, noupload, interactive):
    distro_name = distro.release_name

    if stack_name != 'ALL' and stack_name not in distro.stacks:
        raise BuildFailure("stack [%s] not found in distro [%s]."%(stack_name, distro_name))

    # Create the environment where we build the debs, if necessary
    create_chroot(distro, distro_name, os_platform, arch)


    # Load blacklisted information
    missing_primary, missing_dep, missing_excluded, missing_excluded_dep = list_missing.get_missing(distro, os_platform, arch)
    missing_ok = missing_excluded.union(missing_excluded_dep)

    # Find all the deps in the distro for this stack
    deps = compute_deps(distro, stack_name)

    broken = set()
    skipped = set()

    # Build the deps in order
    for (sn, sv) in deps:
        # Only build debs we expect to be there
        if sn not in missing_ok:
            deb_name = "ros-%s-%s"%(distro_name, debianize_name(sn))
            deb_version = debianize_version(sv, '0', os_platform)
            if not deb_in_repo(deb_name, deb_version, os_platform, arch) or (force and sn == stack_name):
                si = load_info(sn, sv)
                depends = set(si['depends'])
                if depends.isdisjoint(broken.union(skipped)):
                    try:
                        do_deb_build(distro_name, sn, sv, os_platform, arch, staging_dir, noupload, interactive and sn == stack_name)
                    except:
                        broken.add(sn)
                else:
                    print "Skipping %s (%s) since dependencies not built: %s"%(sn, sv, broken.union(skipped)&depends)
                    skipped.add(sn)
            else:
                print "Skipping %s (%s) since already built."%(sn,sv)


    if broken.union(skipped):
        raise BuildFailure("debbuild did not complete successfully. A list of broken and skipped stacks are below. Broken means the stack itself did not build. Skipped stacks means that the stack's dependencies could not be built.\n\nBroken stacks: %s.  Skipped stacks: %s"%(broken, skipped))

EMAIL_FROM_ADDR = 'ROS debian build system <noreply@willowgarage.com>'

def build_debs_main():

    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog <distro> <stack> <os-platform> <arch>", prog=NAME)

    parser.add_option("-d", "--dir",
                      dest="staging_dir", default=None,
                      help="directory to use for staging source debs", metavar="STAGING_DIR")
    parser.add_option("--force",
                      dest="force", default=False, action="store_true")
    parser.add_option("--noupload",
                      dest="noupload", default=False, action="store_true")
    parser.add_option("--noramdisk",
                      dest="ramdisk", default=True, action="store_false")
    parser.add_option("--interactive",
                      dest="interactive", default=False, action="store_true")
    parser.add_option('--smtp', dest="smtp", default='pub1.willowgarage.com', metavar="SMTP_SERVER")

    (options, args) = parser.parse_args()

    if len(args) != 4:
        parser.error('invalid args')
        
    (distro_name, stack_name, os_platform, arch) = args
    distro = failure_message = None

    if options.staging_dir is not None:
        staging_dir    = options.staging_dir
        staging_dir = os.path.abspath(staging_dir)
    else:
        staging_dir = tempfile.mkdtemp()

    try:
        if os_platform not in rosdeb.platforms():
            raise BuildFailure("[%s] is not a known platform.\nSupported platforms are: %s"%(os_platform, ' '.join(rosdeb.platforms())))

        if not os.path.exists(staging_dir):
            print "creating staging dir: %s"%(staging_dir)
            os.makedirs(staging_dir)

        # Load the distro from the URL
        distro_uri = "https://code.ros.org/svn/release/trunk/distros/%s.rosdistro"%distro_name
        distro = Distro(distro_uri)

        if options.ramdisk:
            with TempRamFS(staging_dir, "20G"):
                build_debs(distro, stack_name, os_platform, arch, staging_dir, options.force, options.noupload, options.interactive)
        else:
            build_debs(distro, stack_name, os_platform, arch, staging_dir, options.force, options.noupload, options.interactive)

    except BuildFailure, e:
        failure_message = "Failure Message:\n"+"="*80+'\n'+str(e)
    except Exception, e:
        failure_message = "Internal failure release system. Please notify leibs and kwc @willowgarage.com:\n%s\n\n%s"%(e, traceback.format_exc(e))
    finally:
        # if we created our own staging dir, we are responsible for cleaning it up
        if options.staging_dir is None:
            shutil.rmtree(staging_dir)
            
    # If there was no failure and we did a build of ALL, so we go ahead and stamp the debs now
    if not failure_message and stack_name == 'ALL':
        try:
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

            # compare versions
            old_version = get_repo_version(list_missing.SHADOW_FIXED_REPO, distro, os_platform, arch)

            if old_version != distro.version:
                if stamp_versions.stamp_debs(distro, os_platform, arch, staging_dir) != 0:
                    failure_message = "Could not upload debs"

        except Exception, e:
            failure_message = "Internal failure in the release system. Please notify leibs and kwc @willowgarage.com:\n%s\n\n%s"%(e, traceback.format_exc(e))
        finally:
            if options.staging_dir is None:
                shutil.rmtree(staging_dir)

    if failure_message:
        print >> sys.stderr, failure_message

        failure_message = "%s\n\n%s"%(failure_message, os.environ['BUILD_URL'])
        if options.smtp and stack_name != 'ALL' and distro is not None:
            stack_version = distro.stacks[stack_name].version
            control = download_control(stack_name, stack_version)
            if  'contact' in control:
                to_addr = control['contact']
                subject = 'debian build [%s-%s-%s-%s] failed'%(distro_name, stack_name, os_platform, arch)
                send_email(options.smtp, EMAIL_FROM_ADDR, to_addr, subject, failure_message)
        sys.exit(1)
            

    
if __name__ == '__main__':
    build_debs_main()


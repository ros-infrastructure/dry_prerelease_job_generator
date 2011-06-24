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
import re
import time

from rosdistro import Distro
import rosdeb
from rosdeb import ubuntu_release, debianize_name, debianize_version, \
    platforms, ubuntu_release_name, load_Packages, get_repo_version
from rosdeb.rosutil import checkout_svn_to_tmp, send_email
from rosdeb.source_deb import download_control

import list_missing
import stamp_versions

NAME = 'build_sourcedebs.py' 
TARBALL_URL = "https://code.ros.org/svn/release/download/stacks/%(stack_name)s/%(base_name)s/%(f_name)s"

SHADOW_REPO = 'ros-shadow'
DEST_REPO = 'ros-shadow-fixed'

REPO_URL = 'http://packages.ros.org/%s/'
SHADOW_REPO_URL = REPO_URL % SHADOW_REPO
DEST_REPO_URL = REPO_URL % DEST_REPO

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

# Stolen from chroot build
class TempRamFS:
    def __init__(self, path, size_str):
        self.path = path
        self.size = size_str
        
    def __enter__(self):
        
        cmd = ['sudo', 'mkdir', '-p', self.path]
        subprocess.check_call(cmd)
        cmd = ['sudo', 'mount', '-t', 'tmpfs', '-o', 'size=%s,mode=0755' % self.size, 'tmpfs', self.path]
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
    return rosdeb.deb_in_repo(SHADOW_REPO_URL, deb_name, deb_version, os_platform, arch, use_regex=True)


def create_chroot(distro, distro_name, os_platform, arch):

    distro_tgz = os.path.join('/var/cache/pbuilder', "%s-%s.tgz" % (os_platform, arch))
    cache_dir = '/home/rosbuild/aptcache/%s-%s' % (os_platform, arch)

    if os.path.exists(distro_tgz) and os.path.getsize(distro_tgz) > 0:  # Zero sized file left in place if last build crashed
        return

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    #ros_info = load_info('ros', distro.released_stacks['ros'].version)

    # Things that this build infrastructure depends on
    basedeps = ['wget', 'lsb-release', 'debhelper']
    # Deps we claimed to have needed for building ROS
    basedeps += ['build-essential', 'python-yaml', 'cmake', 'subversion', 'python-setuptools', 'git-core', 'git-buildpackage']
    # Extra deps that some stacks seem to be missing
    basedeps += ['libxml2-dev', 'libtool', 'unzip']
    # For debugging
    basedeps += ['strace']

    #rosdeps = ros_info['rosdeps']
    # hack due to bug in ubuntu_platform map
    #if os_platform == 'maverick' and 'mighty' in rosdeps:
    #    rosdeps = rosdeps['mighty']
    #else:
    #    rosdeps = rosdeps[os_platform]

    #deplist = ' '.join(basedeps+rosdeps)

    subprocess.check_call(['sudo', 'pbuilder', '--create', '--distribution', os_platform, '--debootstrapopts', '--arch=%s' % arch, '--othermirror', 'deb http://packages.ros.org/ros-shadow/ubuntu %s main' % (os_platform), '--basetgz', distro_tgz, '--components', 'main restricted universe multiverse', '--extrapackages', deplist, '--aptcache', cache_dir])

#def push_built_deb(os_platform, repo_name, upload_files, change_files):
#    # Upload the debs to the server
#    print "uploading debs for %s-%s to pub8"%(stack_name, stack_version)
#    subprocess.check_call(['scp'] + upload_files + ['rosbuild@pub8:/var/packages/%s/ubuntu/queue/%s'%(repo_name,os_platform)])
#
#    for change_file in change_files:
#        #runs processing
#        remote_cmd = "reprepro -b /var/packages/%s/ubuntu -V processincoming %s %s"%(repo_name, os_platform, change_file)
#        print "running on pub8", remote_cmd
#        cmd = ['ssh', 'rosbuild@pub8', remote_cmd]
#        success = subprocess.call(cmd) == 0
#        if( not success ):
#            print "Failed to update package. Go fix it.", change_file
            
def do_deb_build(distro_name, stack_name, stack_version, os_platform, arch, staging_dir, noupload, interactive):
    print "Actually trying to build %s-%s..." % (stack_name, stack_version)
    project_name = stack_name.split('/')[-1].rstrip('.git')
    subprocess.check_call(['sudo', 'apt-get', 'install', 'git-core', 'git-buildpackage','gnupg','-y'])
    subprocess.check_call(["/bin/bash", "-c", "cd %(staging_dir)s && gbp-clone %(stack_name)s" % locals()])

    subprocess.check_call(["/bin/bash", "-c", "cd %(staging_dir)s/%(project_name)s && git-buildpackage -S" % locals()])

    distro_tgz = os.path.join('/var/cache/pbuilder', "%s-%s.tgz" % (os_platform, arch))
    cache_dir = '/home/rosbuild/aptcache/%s-%s' % (os_platform, arch)

    deb_name = "ros-%s-%s" % (distro_name, debianize_name(stack_name))
    deb_version = debianize_version(stack_version, '0', os_platform)
    ros_file = "%s-%s" % (stack_name, stack_version)
    deb_file = "%s_%s" % (deb_name, deb_version)

    conf_file = os.path.join(roslib.packages.get_pkg_dir('rosdeb'), 'config', 'pbuilder.conf')

    # Make sure the distro chroot exists
    if not os.path.exists(distro_tgz):
        raise InternalBuildFailure("%s does not exist." % (distro_tgz))


    staging_dir_contents = os.listdir(staging_dir)
    dsc_files = [f for f in staging_dir_contents if ".dsc" in f]
    if len(dsc_files) != 1:
        raise InternalBuildFailure("Too many dsc files found %s" % dsc_files)
    dsc_file = os.path.join(staging_dir, dsc_files[0])

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


    # Hook script which makes sure we have updated our apt cache
    p = os.path.join(hook_dir, 'D50update')
    with open(p, 'w') as f:
        f.write("""#!/bin/sh
set -o errexit
apt-get update""" % locals())
        os.chmod(p, stat.S_IRWXU)



    if arch == 'amd64':
        archcmd = []
    else:
        archcmd = ['setarch', arch]

    # Actually build the deb.  This results in the deb being located in results_dir
    print "starting pbuilder build of %s-%s" % (stack_name, stack_version)
    subprocess.check_call(archcmd + ['sudo', 'pbuilder', '--build', '--basetgz', distro_tgz, '--configfile', conf_file, '--hookdir', hook_dir, '--buildresult', results_dir, '--binary-arch', '--buildplace', build_dir, '--aptcache', cache_dir, dsc_file])



    # Extract the version number we just built:
    files = os.listdir(results_dir)

    # Find debian file outputs
    deb_files_detected = [f for f in files if f.endswith('.deb')]
    deb_names = [d.split('_')[0] for d in deb_files_detected]


    if len(deb_files_detected) < 1:
        raise InternalBuildFailure("No deb-file generated")

    # Build a package db if we have to
    print "starting package db build of %s-%s" % (stack_name, stack_version)
    subprocess.check_call(['bash', '-c', 'cd %(staging_dir)s && dpkg-scanpackages . > %(results_dir)s/Packages' % locals()])

    for d in deb_names:
        # Script to execute for deb verification
        # TODO: Add code to run all the unit-tests for the deb!
        verify_script = os.path.join(staging_dir, 'verify_script.sh')
        with open(verify_script, 'w') as f:
            f.write("""#!/bin/sh
set -o errexit
echo "deb file:%(staging_dir)s results/" > /etc/apt/sources.list.d/pbuild.list
apt-get update
apt-get install %(d)s -y --force-yes
dpkg -l %(d)s
""" % locals())
            os.chmod(verify_script, stat.S_IRWXU)



        print "starting verify script for %s-%s" % (stack_name, stack_version)
        subprocess.check_call(archcmd + ['sudo', 'pbuilder', '--execute', '--basetgz', distro_tgz, '--configfile', conf_file, '--bindmounts', results_dir, '--buildplace', build_dir, '--aptcache', cache_dir, verify_script])


    # Detect changes files
    change_files = [f for f in files if '.changes' in f]
    upload_files = [os.path.join(results_dir, x) for x in deb_files_detected]
        
    if not noupload:
        upload_debs(upload_files, SHADOW_REPO, distro_name, os_platform, arch)
        upload_debs(upload_files, DEST_REPO, distro_name, os_platform, arch) 
    else:
        print "No Upload option selected, I would have uploaded the files:", upload_files

 
def build_debs(distro, sourcedeb_name, os_platform, arch, staging_dir, force, noupload, interactive):
    distro_name = distro.release_name

    # Create the environment where we build the debs, if necessary
    create_chroot(distro, distro_name, os_platform, arch)

    #try:
    do_deb_build(distro_name, sourcedeb_name, "undefined", os_platform, arch, staging_dir, noupload, interactive)
    #except Exception, ex:
    #    raise StackBuildFailure("source debbuild did not complete successfully when building %s %s"%(sourcedeb_name, ex))
    return



EMAIL_FROM_ADDR = 'ROS debian build system <noreply@willowgarage.com>'




def parse_deb_packages(text):
    parsed = {}
    (key, val, pkg) = (None, '', {})
    count = 0
    for l in text.split('\n'):
        count += 1
        if len(l) == 0:
            if len(pkg) > 0:
                if not 'Package' in pkg:
                    print 'INVALID at %d' % count
                else:
                    if key:
                        pkg[key] = val
                    parsed[pkg['Package']] = pkg
                    (key, val, pkg) = (None, '', {})
        elif l[0].isspace():
            val += '\n' + l.strip()
        else:
            if key:
                pkg[key] = val
            (key, val) = l.split(':', 1)
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

    deb_name = "ros-%s-%s" % (distro_name, debianize_name(metapackage))
    deb_version = "1.0.0-s%d~%s" % (time.mktime(time.gmtime()), os_platform)

    ros_depends = []

    missing = False

    for stack in deps:
        if stack in distro.released_stacks:
            stack_deb_name = "ros-%s-%s" % (distro_name, debianize_name(stack))
            if stack_deb_name in packagelist:
                stack_deb_version = packagelist[stack_deb_name]['Version']
                ros_depends.append('%s (= %s)' % (stack_deb_name, stack_deb_version))
            else:
                print >> sys.stderr, "Variant %s depends on non-built deb, %s" % (metapackage, stack)
                missing = True
        else:
            print >> sys.stderr, "Variant %s depends on non-exist stack, %s" % (metapackage, stack)
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
""" % locals())

    if not missing:
        dest_deb = os.path.join(workdir, "%(deb_name)s_%(deb_version)s_%(arch)s.deb" % locals())
        subprocess.check_call(['dpkg-deb', '--nocheck', '--build', metadir, dest_deb])
    else:
        dest_deb = None

    shutil.rmtree(metadir)
    return dest_deb


def upload_debs(files, repo_name, distro_name, os_platform, arch):
    if len(files) == 0:
        print >> sys.stderr, "No debs to upload."
        return 1 # no files to upload

    subprocess.check_call(['scp'] + files + ['rosbuild@pub8:/var/packages/%s/ubuntu/incoming/%s' % (repo_name, os_platform)])

    base_files = [x.split('/')[-1] for x in files]

    # Assemble string for moving all files from incoming to queue (while lock is being held)
    mvstr = '\n'.join(['mv ' + os.path.join('/var/packages/%s/ubuntu/incoming' % (repo_name), os_platform, x) + ' ' + os.path.join('/var/packages/%s/ubuntu/queue' % (repo_name), os_platform, x) for x in base_files])
    new_files = ' '.join(os.path.join('/var/packages/%s/ubuntu/queue' % (repo_name), os_platform, x) for x in base_files)


    # This script moves files into queue directory, removes all dependent debs, removes the existing deb, and then processes the incoming files
    remote_cmd = "TMPFILE=`mktemp` || exit 1 && cat > ${TMPFILE} && chmod +x ${TMPFILE} && ${TMPFILE}; ret=${?}; rm ${TMPFILE}; exit ${ret}"
    run_script = subprocess.Popen(['ssh', 'rosbuild@pub8', remote_cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    script_content = """
#!/bin/bash
(
flock 200
# Move from incoming to queue
%(mvstr)s
reprepro -V -b /var/packages/%(repo_name)s/ubuntu includedeb %(os_platform)s %(new_files)s
rm %(new_files)s
) 200>/var/lock/%(repo_name)s.lock
""" % locals()

    #Actually run script and check result
    (o, e) = run_script.communicate(script_content)
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
    distro_uri = "https://code.ros.org/svn/release/trunk/distros/%s.rosdistro" % distro_name
    return Distro(distro_uri)
    
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
    distro = failure_message = warning_message = None

    if options.staging_dir is not None:
        staging_dir = options.staging_dir
        staging_dir = os.path.abspath(staging_dir)
    else:
        staging_dir = tempfile.mkdtemp()

    try:
        if os_platform not in rosdeb.platforms():
            raise BuildFailure("[%s] is not a known platform.\nSupported platforms are: %s" % (os_platform, ' '.join(rosdeb.platforms())))

        if not os.path.exists(staging_dir):
            print "creating staging dir: %s" % (staging_dir)
            os.makedirs(staging_dir)

        # Load the distro from the URL
        distro_uri = "https://code.ros.org/svn/release/trunk/distros/%s.rosdistro" % distro_name
        distro = Distro(distro_uri)

        if options.ramdisk:
            with TempRamFS(staging_dir, "20G"):
                build_debs(distro, stack_name, os_platform, arch, staging_dir, options.force, options.noupload, options.interactive)
        else:
            build_debs(distro, stack_name, os_platform, arch, staging_dir, options.force, options.noupload, options.interactive)

    except StackBuildFailure, e:
        warning_message = "Warning Message:\n" + "=" * 80 + '\n' + str(e)
    except BuildFailure, e:
        failure_message = "Failure Message:\n" + "=" * 80 + '\n' + str(e)
    except Exception, e:
        failure_message = "Internal failure release system. Please notify leibs and kwc @willowgarage.com:\n%s\n\n%s" % (e, traceback.format_exc(e))
    finally:
        # if we created our own staging dir, we are responsible for cleaning it up
        if options.staging_dir is None:
            shutil.rmtree(staging_dir)
            



    #TODO COPY INTO SHADOW FIXED  equivilant of lock_deps in build_debs.py
    

    if failure_message or warning_message:
        print >> sys.stderr, failure_message
        print >> sys.stderr, warning_message

        if not options.interactive:
            failure_message = "%s\n%s\n%s" % (failure_message, warning_message, os.environ.get('BUILD_URL', ''))
            if False and options.smtp and stack_name != 'ALL' and distro is not None:
                stack_version = distro.stacks[stack_name].version
                control = download_control(stack_name, stack_version)
                if  'contact' in control and distro_name != 'diamondback':
                    to_addr = control['contact']
                    subject = 'debian build [%s-%s-%s-%s] failed' % (distro_name, stack_name, os_platform, arch)
                    send_email(options.smtp, EMAIL_FROM_ADDR, to_addr, subject, failure_message)
        sys.exit(1)
            

    
if __name__ == '__main__':
    build_debs_main()


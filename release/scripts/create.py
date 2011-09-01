#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
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
#
# Revision $Id: create.py 5643 2010-11-11 20:09:27Z kwc $
# $Author: kwc $

PKG = 'release'
NAME="create.py"

VERSION=7

import roslib; roslib.load_manifest(PKG)

import sys
import os
from subprocess import Popen, PIPE, call, check_call
import shutil
import yaml
import urllib2
import tempfile
import subprocess

import hudson
import roslib.packages
import roslib.stacks

from vcstools import VcsClient

from release import ReleaseException, update_rosdistro_yaml, make_dist, \
    compute_stack_depends, get_stack_version, \
    checkout_svn_to_tmp, get_source_version, checkout_stack, make_dist_of_dir

from rosdistro import Distro

pkg_dir = roslib.packages.get_pkg_dir('release_resources')
distros_dir = os.path.join(pkg_dir, '..', 'distros')
    
TARBALL_DIR_URL = 'https://code.ros.org/svn/release/download/stacks/%(stack_name)s/%(stack_name)s-%(stack_version)s'
ROSORG_URL = 'http://ros.org/download/stacks/%(stack_name)s/%(stack_name)s-%(stack_version)s.tar.bz2'
SERVER = 'http://build.willowgarage.com/'
    
def svn_url_exists(url):
    """
    @return: True if SVN url points to an existing resource
    """
    import subprocess
    try:
        p = subprocess.Popen(['svn', 'info', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        return p.returncode == 0
    except:
        return False

def yes_or_no():
    print ("(y/n)")
    while 1:
        input = sys.stdin.readline().strip()
        if input in ['y', 'n']:
            break
    return input == 'y'

def prompt(msg):
    while True:
        prompt = raw_input("Would you like to tag %s as %s in %s, [y/n]"%(config.dev_branch, tag_name, from_url))
        if prompt == 'y':
            return True
        elif prompt == 'n':
            return False

#NOTE: ROS 1.2 does not have the cwd arg
def ask_and_call(cmds, cwd=None):
    """
    Pretty print cmds, ask if they should be run, and if so, runs
    them using subprocess.check_call.

    @return: True if cmds were run.
    """
    # Pretty-print a string version of the commands
    def quote(s):
        return '"%s"'%s if ' ' in s else s
    print "Okay to execute:\n"
    print_bold('\n'.join([' '.join([quote(s) for s in c]) for c in cmds]))
    accepted = yes_or_no()
    import subprocess
    if accepted:
        for c in cmds:
            if cwd:
                subprocess.check_call(c, cwd=cwd)
            else:
                subprocess.check_call(c)                
    return accepted

def get_email():
    if 'ROS_EMAIL' in os.environ:
        email = os.environ['ROS_EMAIL']
    else:
        print_bold("Please enter e-mail address (set ROS_EMAIL to get rid of this prompt):")
        while 1:
            email = sys.stdin.readline().strip()
            if email:
                break
    if '@' in email:
        return email
    else:
        return None

def load_sys_args():
    """
    @return: name, version, distro_file, distro_name
    @rtype: (str, str, str, str)
    """
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog <stack> <version> <release-name>", prog=NAME)
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error("""You must specify: 
 * stack name (e.g. common_msgs)
 * version (e.g. 1.0.1)
 * distro release name (e.g. cturtle)""")
    name, version, release_name = args
    distro_file = os.path.join(distros_dir, '%s.rosdistro'%(release_name))
    distro_file = os.path.abspath(distro_file)
    if not os.path.isfile(distro_file):
        parser.error("Could not find rosdistro file for [%s].\nExpected it in %s"%(release_name, distro_file))
    # brittle test to make sure that user got the args correct
    if not '.' in version:
        parser.error("[%s] doesn't appear to be a version number"%version)
    return name, version, distro_file

def load_and_validate_properties(name, distro, distro_file):
    """
    @return: name, version, distro_file, distro
    @rtype: (str, str, str, release.Distro)
    """
    try:
        props = distro.stacks[name]
    except KeyError:
        raise ReleaseException("%s is not listed in distro file %s"%(name, distro_file))
    
    print_bold("Release Properties")
    for p in ['name', 'dev_svn', 'release_svn']:
        print " * %s: %s"%(p, getattr(props, p))
    print "Release target is [%s]"%(distro.release_name)


    
def confirm_stack_version(local_path, checkout_path, stack_name, version):
    vcs_version = get_stack_version(checkout_path, stack_name)
    local_version = get_stack_version(local_path, stack_name)
    if vcs_version != version:
        raise ReleaseException("The version number of stack %s stored in version control does not match specified release version:\n\n%s"%(stack_name, vcs_version))
    if local_version != version:
        raise ReleaseException("The version number of stack %s on your ROS_PACKAGE_PATH does not match specified release version:\n\n%s"%(stack_name, local_version))
    

def copy_to_server(name, version, tarball, control, control_only=False):
    """
    @param name: stack name
    @type  name: str
    @param version: stack version
    @type  version: str
    @param tarball: path to tarball file to upload
    @param control: debian control file data
    @type  control: dict
    """
    # create a separate directory for new tarball inside of stack-specific directory
    # - rename vars for URL pattern
    stack_name = name
    stack_version = version
    url = TARBALL_DIR_URL%locals()

    if not svn_url_exists(url):
        cmd = ['svn', 'mkdir', '--parents', "-m", "creating new tarball directory", url]
        print "creating new tarball directory"
        print ' '.join(cmd)
        check_call(cmd)

    tarball_name = os.path.basename(tarball)

    # check to see if tarball already exists. This happens in
    # multi-distro releases. It's best to reuse the existing tarball.
    tarball_url = url + '/' + tarball_name
    if svn_url_exists(tarball_url):
        # no longer ask user to reuse, always reuse b/c people answer
        # this wrong and it breaks things.  the correct way to
        # invalidate is to delete the tarball manually with SVN from
        # now on.
        print "reusing existing tarball of release for this distribution"
        return

    # checkout tarball tree so we can add new tarball
    dir_name = "%s-%s"%(name, version)
    tmp_dir = checkout_svn_to_tmp(dir_name, url)
    subdir = os.path.join(tmp_dir, dir_name)
    if not control_only:
        to_path = os.path.join(subdir, tarball_name)
        print "copying %s to %s"%(tarball, to_path)
        assert os.path.exists(tarball)
        shutil.copyfile(tarball, to_path)

    # write control data to file
    control_f = '%s-%s.yaml'%(name, version)
    with open(os.path.join(subdir, control_f), 'w') as f:
        f.write(yaml.safe_dump(control))
    
    # svn add tarball and control file data
    if not control_only:
        check_call(['svn', 'add', tarball_name], cwd=subdir)
    check_call(['svn', 'add', control_f], cwd=subdir)
    if control_only:
        check_call(['svn', 'ci', '-m', "new release %s-%s"%(name, version), control_f], cwd=subdir)
    else:
        check_call(['svn', 'ci', '-m', "new release %s-%s"%(name, version), tarball_name, control_f], cwd=subdir)

def checkout_distro_stack(distro_stack, from_url, spec):
    vcs_type = distro_stack.vcs_config.type
    tempdir = tempfile.mkdtemp()
    temp_repo = os.path.join(tempdir, distro_stack.name)
    client = VcsClient(vcs_type, temp_repo)
    client.checkout(from_url, config.dev_branch)
    return temp_repo

def tag_release(distro_stack):
    if 'svn' in distro_stack._rules:
        tag_subversion(distro_stack)
    elif 'git' in distro_stack._rules:
        tag_git(distro_stack)
    elif 'hg' in distro_stack._rules:
        tag_mercurial(distro_stack)
    elif 'bzr' in distro_stack._rules:
        tag_bzr(distro_stack)
    else:
        raise Exception("unsupported VCS")
    
def tag_subversion(distro_stack):
    cmds = []
    config = distro_stack.vcs_config
    for tag_url in [config.release_tag, config.distro_tag]:
        from_url = config.dev
        release_name = "%s-%s"%(distro_stack.name, distro_stack.version)

        # delete old svn tag if it's present
        append_rm_if_exists(tag_url, cmds, 'Making room for new release')
        # svn cp command to create new tag
        cmds.append(['svn', 'cp', '--parents', '-m', 'Tagging %s new release'%(release_name), from_url, tag_url])
    if not ask_and_call(cmds):    
        print "create_release will not create this tag in subversion"
        return []
    else:
        return [tag_url]
    
def tag_mercurial(distro_stack):
    config = distro_stack.vcs_config
    for tag_name in [config.release_tag, config.distro_tag]:
        from_url = config.repo_uri
        if prompt("Would you like to tag %s as %s in %s, [y/n]"%(config.dev_branch, tag_name, from_url)):
            temp_repo = checkout_distro_stack(distro_stack, from_url, config.dev_branch)
            subprocess.check_call(['hg', 'tag', '-f', tag_name], cwd=temp_repo)
            subprocess.check_call(['hg', 'push'], cwd=temp_repo)
    return [tag_name]

def tag_bzr(distro_stack):
    config = distro_stack.vcs_config
    from_url = config.repo_uri

    # First create a release tag in the bzr repository.
    if prompt("Would you like to tag %s as %s in %s, [y/n]"%(config.dev_branch, config.release_tag, from_url)):
        temp_repo = checkout_distro_stack(distro_stack, from_url, config.dev_branch)
        #directly create and push the tag to the repo
        subprocess.check_call(['bzr', 'tag', '-d', config.dev_branch,'--force',config.release_tag], cwd=temp_repo)

    # Now create a distro branch.
    # In bzr a branch is a much better solution since
    # branches can be force-updated by fetch.
    branch_name = config.release_tag
    if prompt("Would you like to create the branch %s as %s in %s, [y/n]"%(config.dev_branch, branch_name, from_url)):
        temp_repo = checkout_distro_stack(distro_stack, from_url, config.dev_branch)
        subprocess.check_call(['bzr', 'push', '--create-prefix', from_url+"/"+branch_name], cwd=temp_repo)
    return [config.distro_tag]

def tag_git(distro_stack):
    config = distro_stack.vcs_config
    from_url = config.repo_uri

    # First create a release tag in the git repository.
    if prompt("Would you like to tag %s as %s in %s, [y/n]"%(config.dev_branch, config.release_tag, from_url)):
        temp_repo = checkout_distro_stack(distro_stack, from_url, config.dev_branch)
        subprocess.check_call(['git', 'tag', '-f', config.release_tag], cwd=temp_repo)
        subprocess.check_call(['git', 'push', '--tags'], cwd=temp_repo)

    # Now create a distro branch. In git tags are not overwritten
    # during updates, so a branch is a much better solution since
    # branches can be force-updated by fetch.
    branch_name = config.distro_tag
    if prompt("Would you like to create the branch %s as %s in %s, [y/n]"%(config.dev_branch, branch_name, from_url)):
        temp_repo = checkout_distro_stack(distro_stack, from_url, config.dev_branch)
        subprocess.check_call(['git', 'branch', '-f', branch_name, config.dev_branch], cwd=temp_repo)
        subprocess.check_call(['git', 'push', from_url, branch_name], cwd=temp_repo)
    return [config.distro_tag]

def print_bold(m):
    print '\033[1m%s\033[0m'%m    

def append_rm_if_exists(url, cmds, msg):
    if svn_url_exists(url):
        cmds.append(['svn', 'rm', '-m', msg, url]) 
    
def checkin_distro_file(name, version, distro_file):
    cwd = os.path.dirname(distro_file)
    check_call(['svn', 'diff', distro_file], cwd=cwd)
    cmd = ['svn', 'ci', '-m', "%s %s"%(name, version), distro_file]
    ask_and_call([cmd], cwd=cwd)
    
def trigger_hudson_source_deb(name, version, distro):
    h = hudson.Hudson(SERVER)
    parameters = {
        'DISTRO_NAME': distro.release_name,
        'STACK_NAME': name,
        'STACK_VERSION': version,        
        }
    h.build_job('debbuild-sourcedeb', parameters=parameters, token='RELEASE_SOURCE_DEB')

def trigger_debs(distro, os_platform, arch):
    h = hudson.Hudson(SERVER)
    parameters = {
        'DISTRO_NAME': distro,
        'STACK_NAME': 'ALL',
        'OS_PLATFORM': os_platform,
        'ARCH': arch,        
        }
    h.build_job('debbuild-build-debs-%s-%s-%s'%(distro, os_platform, arch), parameters=parameters, token='RELEASE_BUILD_DEBS')

def check_stack_depends(local_path, stack_name):
    """
    @param local_path: stack directory
    @param stack_name: stack name
    @raise ReleaseException: if declared dependencies for stack do not match actual depends
    """
    depends = compute_stack_depends(local_path)
    m = roslib.stack_manifest.parse_file(os.path.join(local_path, roslib.stack_manifest.STACK_FILE))
    declared = [d.stack for d in m.depends]

    # we enable one more level down for forwarded depends
    # (e.g. metastacks), but go no further.
    for d in m.depends:
        try:
            m_depend = roslib.stack_manifest.parse_file(roslib.stack_manifest.stack_file(d.stack))
            declared.extend([d.stack for d in m_depend.depends])
        except:
            pass
    
    # we enable one more level down for forwarded depends
    # (e.g. metastacks), but go no further.
    for d in m.depends:
        try:
            m_depend = roslib.stack_manifest.parse_file(roslib.stack_manifest.stack_file(d.stack))
            declared.extend([d.stack for d in m_depend.depends])
        except:
            pass
    
    # it is okay for a stack to overdeclare as it may be doing
    # something metapackage-like, but it must have every dependency
    # that is calculated.
    missing = set(depends) - set(declared)
    if missing:
        raise ReleaseException("Stack's declared dependencies are missing calculated dependencies:\n"+'\n'.join(list(missing)))
        

def check_version():
    url = 'https://code.ros.org/svn/release/trunk/VERSION'
    f = urllib2.urlopen(url)
    req_version = int(f.read())
    f.close()
    if VERSION < req_version:
        print "This release script is out-of-date.\nPlease upgrade your release and ros_release scripts"
        sys.exit(1)
    
def main():
    check_version()
    
    try:
        repair = '--repair' in sys.argv
        sys.argv = [a for a in sys.argv if a != '--repair']
        
        # load the args
        name, version, distro_file = load_sys_args()
        try:
            local_path = roslib.stacks.get_stack_dir(name)
        except:
            sys.stderr.write("ERROR: Cannot find local checkout of stack [%s].\nThis script requires a local version of the stack that you wish to release.\n"%(name))
            sys.exit(1)


        # ask if stack got tested
        print 'Did you run prerelease tests on your stack?'
        if not yes_or_no():
            print """Before releasing a stack, you should make sure your stack works well,
 and that the new release does not break any already released stacks
 that depend on your stack.
Willow Garage offers a pre-release test set that tests your stack and all
 released stacks that depend on your stack, on all distributions and architectures
 supported by Willow Garage. 
You can trigger pre-release builds for your stack on <http://code.ros.org/prerelease/>"""
            return

        # make sure distro_file is up-to-date
        print "Retrieving up-to-date %s"%(distro_file)
        subprocess.check_call(['svn', 'up', distro_file])
        
        distro = Distro(distro_file)
        load_and_validate_properties(name, distro, distro_file)

        distro_stack = distro.stacks[name]
        
        #checkout the stack
        tmp_dir = checkout_stack(name, distro_stack, repair)
        confirm_stack_version(local_path, os.path.join(tmp_dir, name), name, version)
        check_stack_depends(local_path, name)

        distro_stack.update_version(version)
        email = get_email()            
        
        # create the tarball
        tarball, control = make_dist_of_dir(tmp_dir, name, version, distro_stack)
        #tarball, control = make_dist(name, version, distro_stack, repair=repair)
        if not control['rosdeps']:
            sys.stderr.write("""Misconfiguration: control rosdeps are empty.\n
    In order to run create.py, the stack you are releasing must be on your current
    ROS_PACKAGE_PATH. This is so create.py can access the stack's rosdeps.\n""")
            sys.exit(1)
            
        print_bold("Release should be in %s"%(tarball))
        if email:
            print "including contact e-mail"
            control['contact'] = email
        else:
            print "no valid contact e-mail, will not send build failure messages"
        
        # create the VCS tags
        if not repair:
            tag_release(distro_stack)

        # checkin the tarball
        copy_to_server(name, version, tarball, control)

        # cleanup temporary file
        os.remove(tarball)

        # update the rosdistro file
        if not repair:
            update_rosdistro_yaml(name, version, distro_file)
            checkin_distro_file(name, version, distro_file)

        # trigger source deb system
        trigger_hudson_source_deb(name, version, distro)
        
        print """

Now:
 * update the changelist at http://www.ros.org/wiki/%s/ChangeList
"""%name
        
    except ReleaseException as e:
        print >> sys.stderr, "ERROR: %s"%str(e)
        sys.exit(1)


if __name__ == '__main__':
    main()

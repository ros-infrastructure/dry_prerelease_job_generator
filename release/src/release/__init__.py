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
# Revision $Id: __init__.py 4136 2010-10-20 00:13:02Z kwc $
# $Author: kwc $

from __future__ import with_statement

import os
import subprocess
import tempfile
import re
import tarfile
import shutil

import yaml

import roslib.packages
import roslib.stacks
import roslib.stack_manifest

from rosdistro import Distro
from rosdeb import control_data
# we export this symbol to create.py as well
from rosdeb.rosutil import checkout_svn_to_tmp, checkout_dev_to_tmp, checkout_tag_to_tmp

class ReleaseException(Exception): pass

def get_source_version(distro, stack_name):
    import urllib2
    import re
    dev_svn = distro.stacks[stack_name].dev_svn 
    print "Reading version number from %s"%(dev_svn)

    source_url = dev_svn + '/stack.xml'
    try:
        f = urllib2.urlopen(source_url)
        text = f.read()
        f.close()
    except urllib2.HTTPError:
        raise ReleaseException("failed to fetch stack.xml for stack.\nA common cause is the '_rules' are not set correctly for this stack.\nThe URL was %s"%(source_url))

    try:
        m = roslib.stack_manifest.parse(text)
        if m.version:
            return m.version
    except:
        raise ReleaseException("stack.xml failed validation. Read from URL [%s]"%(source_url))        
    
    version = get_stack_manifest_version(text)
    if version:
        return version

    # fallback on CMakeLists.txt version
    source_url = dev_svn + '/CMakeLists.txt'
    try:
        f = urllib2.urlopen(source_url)
        text = f.read()
        f.close()
    except urllib2.HTTPError:
        raise ReleaseException("failed to fetch CMakeLists.txt for stack.\nA common cause is the '_rules' are not set correctly for this stack.\nThe URL was %s"%(source_url))
    
    return get_cmake_version(text)

# this is mostly a copy of the roscreatestack version, but as it has
# different error behavior, I decided to copy it and slim it down (kwc)
def compute_stack_depends(stack_dir):
    """
    @return: depends, licenses
    @rtype: {str: [str]}, [str]
    @raise ReleaseException: if error occurs detecting dependencies
    """
    stack = os.path.basename(os.path.abspath(stack_dir))    
    if os.path.exists(stack_dir):
        packages = roslib.packages.list_pkgs_by_path(os.path.abspath(stack_dir))
        depends = _compute_stack_depends_and_licenses(stack, packages)
    else:
        depends = dict()
    # add in bare ros dependency into any stack as an implicit depend
    if not 'ros' in depends and stack != 'ros':
        depends['ros'] = []
    return depends
    
def _compute_stack_depends_and_licenses(stack, packages):
    pkg_depends = []
    for pkg in packages:
        m = roslib.manifest.parse_file(roslib.manifest.manifest_file(pkg))
        pkg_depends.extend([d.package for d in m.depends])
        
    stack_depends = {}
    for pkg in pkg_depends:
        if pkg in packages:
            continue
        try:
            st = roslib.stacks.stack_of(pkg)
        except roslib.packages.InvalidROSPkgException:
            raise ReleaseException("cannot locate package [%s], which is a dependency in the [%s] stack"%(pkg, stack))
        if not st:
            raise ReleaseException("WARNING: stack depends on [%s], which is not in a stack"%pkg)
        if st == stack:
            continue
        if not st in stack_depends:
            stack_depends[st] = []            
        stack_depends[st].append(pkg)
    return stack_depends


def get_stack_version(stack_dir, stack_name):
    return get_stack_version_by_dir(stack_dir)

# NOTE: this is a copy of roslib.stacks.get_stack_version_by_dir().  We copy
# it here for compatibility with cturtle/diamondback
def get_stack_version_by_dir(stack_dir):
    """
    Get stack version where stack_dir points to root directory of stack.
    
    @param env: override environment variables
    @type  env: {str: str}

    @return: version number of stack, or None if stack is unversioned.
    @rtype: str
    """
    # REP 109: check for <version> tag first, then CMakeLists.txt
    manifest_filename = os.path.join(stack_dir, roslib.stacks.STACK_FILE)
    if os.path.isfile(manifest_filename):
        m = roslib.stack_manifest.parse_file(manifest_filename)
        try:
            # version attribute only available in ROS 1.5.1+
            if m.version:
                return m.version
        except AttributeError:
            pass
    
    cmake_filename = os.path.join(stack_dir, 'CMakeLists.txt')
    if os.path.isfile(cmake_filename):
        with open(cmake_filename) as f:
            return get_cmake_version(f.read())
    else:
        return None

def get_cmake_version(text):
    for l in text.split('\n'):
        if l.strip().startswith('rosbuild_make_distribution'):
            x_re = re.compile(r'[()]')
            lsplit = x_re.split(l.strip())
            if len(lsplit) < 2:
                raise ReleaseException("couldn't find version number in CMakeLists.txt:\n\n%s"%l)
            return lsplit[1]

def update_rosdistro_yaml(stack_name, version, distro_file):
    """
    Update distro file for new stack version
    """
    if not os.path.exists(distro_file):
        raise ReleaseException("[%s] does not exist"%distro_file)

    with open(distro_file) as f:
        d = [d for d in yaml.load_all(f.read())]
        if len(d) != 1:
            raise ReleaseException("found more than one release document in [%s]"%distro_file)
        d = d[0]

    distro_d = d
    if not 'stacks' in d:
        d['stacks'] = {}
    d = d['stacks']
    if not stack_name in d:
        d[stack_name] = {}
    d = d[stack_name]
    # set the version key, assume not overriding properties
    d['version'] = str(version)

    print "Writing new release properties to [%s]"%distro_file
    with open(distro_file, 'w') as f:
        f.write(yaml.safe_dump(distro_d))
        
def make_dist(name, version, distro_stack, repair=False):
    """
    Create tarball in a temporary directory. 

    @param repair: if True, repair tarball from tagged release.
    @type  repair: bool
    @return: tarball file path, control data. 
    """
    tmp_dir = checkout_stack(name, distro_stack, repair)

    return make_dist_of_dir(tmp_dir, name, version, distro_stack)

def checkout_stack(name, distro_stack, repair):
    """ 
    Checkout the stack into a tempdir
    
    @return The temporary directory to find the stack inside
    """
    
    if not repair:
        tmp_dir = checkout_dev_to_tmp(name, distro_stack)
    else:
        tmp_dir = checkout_tag_to_tmp(name, distro_stack)        
    return tmp_dir

import hashlib

def md5sum_file(filename):
    m = hashlib.md5()
    with open(filename, 'rb') as f:
        data = f.read(4096)
        while data:
            m.update(data)
            data = f.read(4096)
    return m.hexdigest()

def make_dist_of_dir(tmp_dir, name, version, distro_stack):
    """
    Create tarball in a temporary directory. 
    It is expected the tempdir has a fresh checkout of the stack.

    @param name: stack name
    @param version: stack version
    @return: tarball file path, control data. 
    """
    tmp_source_dir = os.path.join(tmp_dir, name)
    print 'Building a distribution for %s in %s'%(name, tmp_source_dir)
    tarball = create_stack_tarball(tmp_source_dir, name, version)
    md5sum = md5sum_file(tarball)
    control = control_data(name, version, md5sum, stack_file=os.path.join(tmp_source_dir, 'stack.xml'))
    
    # move tarball outside tmp_dir so we can clean it up
    dst = os.path.join(tempfile.gettempdir(), os.path.basename(tarball))
    shutil.copyfile(tarball, dst)
    shutil.rmtree(tmp_dir)
    return dst, control

def svn_url_exists(url):
    try:
        stdout, stderr = subprocess.Popen(['svn', 'info', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if not stderr:
            return True
        else:
            return False            
    except:
        return False


TAR_IGNORE_TOP=['build']
TAR_IGNORE_ALL=['.svn', '.git', '.hg']

def tar_exclude(name):
    if name.split('/')[-1] in TAR_IGNORE_ALL:
        return True
    else:
        return False

def create_stack_tarball(path, stack_name, stack_version):
    """
    Create a source tarball from a stack at a particular path.
  
    @param name: name of stack
    @param stack_version: version number of stack
    @param path: the path of the stack to package up
    @return: the path of the resulting tarball, or else None
    """

    # Verify that the stack has both a stack.xml and CMakeLists.txt file
    stack_xml_path = os.path.join(path, roslib.stack_manifest.STACK_FILE)
    cmake_lists_path = os.path.join(path, 'CMakeLists.txt')

    if not os.path.exists(stack_xml_path):
        raise ReleaseException("Could not find stack manifest, expected [%s]."%(stack_xml_path))
    if not os.path.exists(cmake_lists_path):
        raise ReleaseException("Could not find CMakeLists.txt file, expected [%s]."%(cmake_lists_path))

    # Create the build directory
    build_dir = os.path.join(path, 'build')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    tarfile_name = os.path.join(build_dir,'%s-%s.tar.bz2'%(stack_name, stack_version))
    archive_dir = '%s-%s'%(stack_name, stack_version)

    tar = tarfile.open(tarfile_name, 'w:bz2')
  
    for x in os.listdir(path):
        if x not in TAR_IGNORE_TOP + TAR_IGNORE_ALL:
            # path of item
            p = os.path.join(path,x)
            # tar path of item
            tp = os.path.join(archive_dir, x)
            
            tar.add(p, tp, exclude=tar_exclude)
            
    tar.close()
    return tarfile_name


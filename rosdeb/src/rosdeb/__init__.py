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
# Revision $Id: distro.py 10301 2010-07-09 01:21:23Z kwc $

import os
import sys
import subprocess
import shutil

import yaml

import roslib.rosenv

from rosdeb.rosutil import convert_html_to_text, stack_rosdeps

_ubuntu_map = { '10.10': 'mighty', '10.04': 'lucid', '9.10': 'karmic', '9.04': 'jaunty', '8.10': 'intrepid', '8.04': 'hardy'}
def ubuntu_release():
    """
    WARNING: this can only be called on an Ubuntu system
    """
    if not os.path.isfile('/etc/issue'):
        raise Exception("this is not an ubuntu system")        
    f = open('/etc/issue')
    for s in f:
        if s.startswith('Ubuntu'):
            v = s.split()[1]
            v = '.'.join(v.split('.')[:2])
        try:
            return _ubuntu_map[v]
        except KeyError:
            raise Exception("unrecognized ubuntu version %s" % v)
    raise Exception("could not parse ubuntu release version")

def debianize_name(name):
    """
    Convert ROS stack name to debian conventions (dashes, not underscores)
    """
    return name.replace('_', '-')

def debianize_version(stack_version, distro_version, ubuntu_rel=None):
    """
    WARNING: this can only be called on an Ubuntu system and will lock to the platform it is called on
    """
    if ubuntu_rel is None:
        ubuntu_rel = ubuntu_release()
    return stack_version+'-'+distro_version+'~%s'%ubuntu_rel

def platforms():
    return _ubuntu_map.keys()

def debianize_Distro(distro):
    """
    Add debian-specific attributes to distro objects (DistroStack)
    """
    for stack in distro.stacks.itervalues():
        try:
            stack.debian_version = debianize_version(stack.stack_version, stack.release_version)
            stack.debian_name    = debianize_name("ros-%s-%s"%(stack.release_name,stack.stack_name))
        except DistroException:
            # ignore on non debian systems. This really belongs in an extension
            stack.debian_version = stack.debian_name = None

################################################################################
            
def make_source_deb(distro_name, stack_name, stack_version, staging_dir):
    debian_name = debianize_name(stack_name)

    tmpl_d = os.path.join(roslib.packages.get_pkg_dir('release'), 'resources', 'source_deb')
    
    tarball = os.path.join(staging_dir, "%s-%s.tar.bz2"%(stack_name, stack_version))
    if not os.path.exists(tarball):
        raise Exception("tarball must be copied to staging directory first")

    # make STACK/debian
    stack_d  = os.path.join(staging_dir, stack_name)
    debian_d = os.path.join(stack_d, 'debian')
    os.makedirs(debian_d)

    for f in ['Makefile', 'rules', 'compat', 'postinst']:
        if stack_name == 'ros':
            f_src = f+'-ros'
        else:
            f_src = f
            
        files.append( (os.path.join(tmpl_d, f), os.path.join(debian_d, f)) )

    for f in ['fixrpath.py']:
        files.append( (os.path.join(tmpl_d, f), os.path.join(stack_d, f)) )
        
    for f in ['setup-deb.sh']:
        if stack_name == 'ros':
            f_src = f+'-ros'
        else:
            f_src = f
        files.append( (os.path.join(tmpl_d, f), os.path.join(stack_d, f)) )
                      
    if stack_name == 'ros':
        file.append( (os.path.join(tmpl_d, 'setup.sh'), os.path.join(stack_d, 'setup.sh')))

    for src, dst in files:
        with open(src, 'r') as f:
            src_text = f.read()

        dst_text = src_text.replace('${ROS_DISTRO_NAME}', distro_name)
        dst_text = dst_text.replace('${ROS_STACK_NAME}', stack_name)
        dst_text = dst_text.replace('${ROS_STACK_DEBIAN_NAME}', debian_name)
        dst_text = dst_text.replace('${ROS_STACK_VERSION}', stack_version)
        with open(dst, 'w') as f:
            f.write(dst_text)
            
    # read in the control YAML data and convert it to an actual control file
    control_yaml = os.path.join(staging_dir, '%s-%s.yaml'%(stack_name, stack_version))
    with open(control_yaml, 'r') as f:
        metadata = yaml.loads(f.read())
    with open(os.path.join(debian_d, 'control'), 'w') as f:
        f.write(control_file(metadata))

    # TODO: changelog
    with open(os.path.join(debian_d, 'changelog'), 'w') as f:
        f.write(changelog_file(metadata))
    
    # Note: this creates 3 files.  A .dsc, a .tar.gz, and a .changes
    check_call(['dpkg-buildpackage', '-S'], cwd=stack_d)
    
def changelog_file(metadata, platform='lucid'):
    #TODO
    data = metadata.copy()
    #day-of-week, dd month yyyy hh:mm:ss +zzzz
    data['date'] = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
    data['platform'] = platform
    return """%(package)s ((version)s-0) jaunty karmic lucid; urgency=low
  * Please see https://ros.org/wiki/%(stack)s/ChangeList
 -- See control for maintainer <ros-users@code.ros.org>  %(date)s
"""%metadata
    
def control_file(metadata):
    data = metadata.copy()
    data['deb-depends'] = 'TODO'
    return """Source: %(package)s
Section: unknown
Priority: %(priority)s
Maintainer: %(maintainer)s
Build-Depends: debhelper (>= 5), chrpath, %(deb-depends)s
Standards-Version: 3.7.2

Package: %(package)s
Architecture: any
Depends: ${shlibs:Depends}, ${misc:Depends}, %(deb-depends)s
Description: %(description-brief)s
%(description-full)s
"""%data
    
def control_data(stack_name, stack_version, stack_file=None):
    """
    Generate metadata for control file. Cannot generate debian dependencies as these are platform specific.
    
    @type  stack_name: name of stack
    @type  stack_name: str
    @type  stack_version: stack version id
    @type  stack_version: str
    @param stack_file: location of stack file, or None to use default rosstack lookup
    @type  stack_file: str
    """
    from roslib.stack_manifest import parse_file, stack_file
    if stack_file is None:
        stack_xml = stack_file(stack_name)        
    m = roslib.stack_manifest.parse_file(stack_xml)

    metadata = {}
    
    metadata['stack']      = stack_name
    metadata['package']    = debianize_name(stack_name)
    metadata['version']    = stack_version
    metadata['homepage']   = m.url
    metadata['maintainer'] = m.author
    metadata['priority']   = 'optional'
    if m.brief:
        # 60-char limit on control files
        metadata['description-brief'] = m.brief[:60]
    else:
        metadata['description-brief'] = m.brief[:60]

    try:
        description = convert_html_to_text(m.description)
    except:
        description = "unknown"

    # per debian spec, single-space pad to signal paragraph
    for l in m.description.split('\n'):
        description += ' '+l+'\n'
    metadata['description-full']  = description

    # do deps in two parts as ros stack depends need to become version
    # locked later on due to lack of ABI compat
    metadata['depends'] = [d.stack for d in m.depends]
    
    return metadata


if __name__ == '__main__':
    # test out our HTML converter on all known stacks        
    import roslib.stacks
    from roslib.stack_manifest import parse_file, stack_file
    for stack_name in roslib.stacks.list_stacks():
        if 0:
            stack_xml = stack_file(stack_name)
            m = roslib.stack_manifest.parse_file(stack_xml)
            print '#' * 80
            print m.description
            print '---'
            print convert_html_to_text(m.description)
            print '---'
        if 1:
            print stack_name
            print stack_rosdeps(stack_name)
    

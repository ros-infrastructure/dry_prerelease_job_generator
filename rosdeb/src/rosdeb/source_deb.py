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
# Revision $Id: __init__.py 10652 2010-08-11 22:01:37Z kwc $

import os
import sys
import time
from subprocess import check_call

import yaml

import roslib.packages

from rosdeb.rosutil import convert_html_to_text, stack_rosdeps
from rosdeb.core import ubuntu_release, debianize_name, debianize_version, platforms, ubuntu_release_name

def make_source_deb(distro_name, stack_name, stack_version, os_platform_name, staging_dir):
    """
    @param os_platform_name: Name of OS platform/version, e.g. 'lucid'
    @type  os_platform_name: str
    """
    debian_name = debianize_name(stack_name)

    tmpl_d = os.path.join(roslib.packages.get_pkg_dir('rosdeb'), 'resources', 'source_deb')
    
    tarball = os.path.join(staging_dir, "%s-%s.tar.bz2"%(stack_name, stack_version))
    if not os.path.exists(tarball):
        raise Exception("tarball must be copied to staging directory first")

    # keep track of files we've copied in to modify
    files = []
    
    # make STACK/debian
    stack_d  = os.path.join(staging_dir, stack_name)
    debian_d = os.path.join(stack_d, 'debian')
    if not os.path.exists(debian_d):
        os.makedirs(debian_d)

    for f in ['Makefile', 'rules', 'compat', 'postinst']:
        if stack_name == 'ros':
            f_src = f+'-ros'
        else:
            f_src = f
            
        files.append( (os.path.join(tmpl_d, f), os.path.join(debian_d, f)) )

    for f in ['fixrpath.py']:
        files.append( (os.path.join(tmpl_d, f), os.path.join(stack_d, f)) )
        
    for f in ['setup_deb.sh']:
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

        # copy permission modes
        s = os.stat(src)
        os.chmod(dst, s.st_mode)
            
    # CONTROL: read in the control YAML data and convert it to an actual control file
    control_yaml = os.path.join(staging_dir, '%s-%s.yaml'%(stack_name, stack_version))
    with open(control_yaml, 'r') as f:
        metadata = yaml.load(f.read())
    with open(os.path.join(debian_d, 'control'), 'w') as f:
        f.write(control_file(metadata, os_platform_name))

    # CHANGELOG
    with open(os.path.join(debian_d, 'changelog'), 'w') as f:
        f.write(changelog_file(metadata))
    
    # Note: this creates 3 files.  A .dsc, a .tar.gz, and a .changes
    check_call(['dpkg-buildpackage', '-S'], cwd=stack_d)
    
def supported_platforms(control):
    return [version for version in control['rosdeps'].keys()]
    
def changelog_file(metadata, platform='lucid'):
    #TODO: want to use BeautifulSoup to rip actual changelog
    data = metadata.copy()
    #day-of-week, dd month yyyy hh:mm:ss +zzzz
    data['date'] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
    data['platform'] = platform
    data['supported'] = ' '.join(supported_platforms(metadata))
    
    return """%(package)s (%(version)s-0) %(supported)s; urgency=low

  * Please see https://ros.org/wiki/%(stack)s/ChangeList
\t
 -- See website <ros-users@code.ros.org>  %(date)s
\t
"""%data
    
def control_file(metadata, platform_name):
    data = metadata.copy()
    try:
        data['deb-depends'] = ', '.join(metadata['rosdeps'][platform_name])
    except KeyError:
        raise Exception("stack [%s] does not have rosdeps for release [%s]"%(metadata['stack'], platform_name))
    
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
    import roslib.stack_manifest
    if stack_file is None:
        stack_file = roslib.stack_manifest.stack_file(stack_name)
    m = roslib.stack_manifest.parse_file(stack_file)

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
    desc_padded = ''
    for l in description.split('\n'):
        desc_padded += ' '+l+'\n'
    metadata['description-full'] = desc_padded

    # do deps in two parts as ros stack depends need to become version
    # locked later on due to lack of ABI compat
    metadata['depends'] = [d.stack for d in m.depends]

    metadata['rosdeps'] = rosdeps = {}
    for platform in platforms():
        try:
            rosdeps[platform] = stack_rosdeps(stack_name, os.path.dirname(stack_file), platform)
        except:
            # ignore failures as these are generally unsupported
            # platforms. Later logic is responsible for erroring if
            # control file is missing bindings, and unit tests on
            # stack_rosdeps verify its functionality
            pass
    
    return metadata



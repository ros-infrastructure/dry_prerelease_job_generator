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
# Revision $Id$
# $Author$

import os


import roslib.manifest
import roslib.stack_manifest
import roslib.packages
import roslib.stacks

from rosdep.core import RosdepLookupPackage, YamlCache

def convert_html_to_text(d):
    """
    Convert a HTML description to plain text. This routine still has
    much work to do, but appears to handle the common uses of HTML in
    our current manifests.
    """
    # check for presence of tags
    if '<' in d:
        from release.BeautifulSoup import BeautifulSoup
        soup = BeautifulSoup(d)
        # convert all paragraphs to line breaks
        paragraphs = soup.findAll('p')
        for p in paragraphs:
            s = ''.join([str(x) for x in p.contents])+"\n"
            p.replaceWith(s)
        # replace all links tags with their link text. This is probably unnecessary
        tags = soup.findAll('a')
        for x in tags:
            x.replaceWith(x.string)

        # findAll text strips remaining tags
        d = ''.join(soup.findAll(text=True))
        
    # double-whitespace is meaningless in HTML, so now we need to reduce
    #  - remove leading whitespace
    d = '\n'.join([x.strip() for x in d.split('\n')])

    d_reduced = ''
    last = None
    for x in d.split('\n'):
        if last is None:
            d_reduced = x
        else:
            if x == '':
                if last == '':
                    pass
                else:
                    d_reduced += '\n'
            else:
                d_reduced += x + ' '
        last = x
    return d_reduced

# based on code in roslib.stacks
def package_manifests_of(stack_dir):
    """
    @return: list of package names and manifest file paths for stack
      dir. These will be returned as a list of (name, path) pairs.
    @rtype: [(str, str)]
    """
    l = [os.path.join(stack_dir, d) for d in os.listdir(stack_dir)]
    manifests = []
    packages = []
    while l:
        d = l.pop()
        if os.path.isdir(d):
            if roslib.packages.is_pkg_dir(d):
                p = os.path.basename(d)
                m_file = os.path.join(d, 'manifest.xml')
                # this is sometimes true if we've descended into a build directory
                if not p in packages:
                    packages.append(p)
                    manifests.append((p, m_file))
            elif os.path.exists(os.path.join(d, 'rospack_nosubdirs')):
                # don't descend
                pass
            elif os.path.basename(d) not in ['build', '.svn', '.git']: #recurse
                l.extend([os.path.join(d, e) for e in os.listdir(d)])
    return manifests

def stack_rosdeps(stack_name, stack_dir, ubuntu_platform):
    """
    Calculate dependencies of stack on an 'ubuntu' OS, including both
    ROS stacks and their rosdep dependencies, for the specified
    ubuntu release version.
    
    NOTE: one flaw in this implementation is that it uses the rosdep
    view from the *active environment* to generate the rosdeps. It
    does not generate them from specific versions of stacks. The hope
    is that rosdeps improve monotonically over time, so that this will
    not be a major issue.

    @return: list of debian package deps
    @rtype: [str]
    """
    
    # - implicit deps of all ROS packages
    deb_deps = ['libc6','build-essential','cmake','python-yaml','subversion']     

    os = 'ubuntu'
    yc = YamlCache(os, ubuntu_platform)

    package_manifests = package_manifests_of(stack_dir)
    for p, m_file in package_manifests:
        m = roslib.manifest.parse_file(m_file)
        rosdeps = [d.name for d in m.rosdeps]
        if not rosdeps:
            continue
            
        rdlp = RosdepLookupPackage(os, ubuntu_platform, p, yc)
        for r in rosdeps:
            value = rdlp.lookup_rosdep(r)
            if '\n' in value:
                raise Exception("cannot generate rosdeps for stack [%s] on platform [%s]:\n\trosdep [%s] has a script binding"%(stack_name, ubuntu_platform, r))
            deb_deps.extend([x for x in value.split(' ') if x.strip()])

    return deb_deps
        
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
    

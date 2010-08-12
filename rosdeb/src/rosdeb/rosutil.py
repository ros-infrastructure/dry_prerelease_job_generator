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

if __name__ == '__main__':
    import roslib; roslib.load_manifest('rosdeb')

import roslib.manifest
import roslib.stack_manifest
import roslib.packages
import roslib.stacks

import rosdeb.core
from rosdep.core import RosdepLookupPackage, YamlCache

IMPLICIT_DEPS = ['libc6','build-essential','cmake','python-yaml','subversion']

def _text_only(soup):
    return ''.join(soup.findAll(text=True))

def convert_html_to_text(d):
    """
    Convert a HTML description to plain text. This routine still has
    much work to do, but appears to handle the common uses of HTML in
    our current manifests.
    """
    # check for presence of tags
    if '<' in d:
        from rosdeb.BeautifulSoup import BeautifulSoup
        soup = BeautifulSoup(d)

        # first, target formatting tags with a straight replace
        for t in ['b', 'strong', 'em', 'i', 'tt', 'a']:
            tags = soup.findAll(t)
            for x in tags:
                x.replaceWith(_text_only(x))
                
        # second, target low-level container tags
        tags = soup.findAll('li')
        for x in tags:
            x.replaceWith('* '+_text_only(x)+'\n')

        # convert all high-level containers to line breaks
        for t in ['p', 'div']:
            tags = soup.findAll(t)
            for t in tags:
                t.replaceWith(_text_only(t)+'\n')

        # findAll text strips remaining tags
        d = ''.join(soup.findAll(text=True))
        
    # reduce the whitespace as the debian parsers have strict rules
    # about what is a paragraph and what is verbose based on leading
    # whitespace.
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

def stack_rosdeps(stack_name, stack_dir, platform):
    """
    Calculate dependencies of stack on an 'ubuntu' OS, including both
    ROS stacks and their rosdep dependencies, for the specified
    ubuntu release version.
    
    NOTE: one flaw in this implementation is that it uses the rosdep
    view from the *active environment* to generate the rosdeps. It
    does not generate them from specific versions of stacks. The hope
    is that rosdeps improve monotonically over time, so that this will
    not be a major issue.

    @param platform: platform name (e.g. lucid)
    
    @return: list of debian package deps
    @rtype: [str]
    """
    
    # - implicit deps of all ROS packages
    deb_deps = IMPLICIT_DEPS[:]

    # hardcode OS for now as we don't build straight debian
    os_name = 'ubuntu'
    # reverse lookup version number, which is the key for rosdep
    os_version = [k for k, v in rosdeb.core.ubuntu_map.iteritems() if v == platform][0]
    
    yc = YamlCache(os_name, os_version)

    package_manifests = package_manifests_of(stack_dir)
    for p, m_file in package_manifests:
        m = roslib.manifest.parse_file(m_file)
        rosdeps = [d.name for d in m.rosdeps]
        if not rosdeps:
            continue
            
        rdlp = RosdepLookupPackage(os_name, os_version, p, yc)
        for r in rosdeps:
            value = rdlp.lookup_rosdep(r)
            if '\n' in value:
                raise Exception("cannot generate rosdeps for stack [%s] on platform [%s]:\n\trosdep [%s] has a script binding"%(stack_name, os_version, r))
            deb_deps.extend([x for x in value.split(' ') if x.strip()])

    return deb_deps
        
if __name__ == '__main__':
    import roslib.stacks
    from rosdeb.rosutil import convert_html_to_text
    from roslib.stack_manifest import parse_file, stack_file
    for stack_name in roslib.stacks.list_stacks():
        stack_xml = stack_file(stack_name)
        m = roslib.stack_manifest.parse_file(stack_xml)
        if stack_name in ['ros_release']:
            print '='*80
            print stack_name
            print convert_html_to_text(m.description)
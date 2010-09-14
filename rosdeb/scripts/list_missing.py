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
import urllib
import urllib2
import stat
import tempfile

import rosdeb
from rosdeb.rosutil import checkout_svn_to_tmp

from roslib2.distro import Distro
from rosdeb.core import ubuntu_release, debianize_name, debianize_version, platforms, ubuntu_release_name

NAME = 'list_missing.py' 
TARBALL_URL = "https://code.ros.org/svn/release/download/stacks/%(stack_name)s/%(base_name)s/%(f_name)s"

import traceback

_distro_yaml_cache = {}

def load_info(stack_name, stack_version):
    
    base_name = "%s-%s"%(stack_name, stack_version)
    f_name = base_name + '.yaml'

    url = TARBALL_URL%locals()

    try:
        if url in _distro_yaml_cache:
            return _distro_yaml_cache[url]
        else:
            _distro_yaml_cache[url] = l = yaml.load(urllib2.urlopen(url))
            return l
    except:
        print >> sys.stderr, "Problem fetching yaml info for %s %s (%s)"%(stack_name, stack_version, url)
        sys.exit(1)

def compute_deps(distro, stack_name):

    seen = set()
    ordered_deps = []

    def add_stack(s):
        if s in seen:
            return
        if s not in distro.stacks:
            print >> sys.stderr, "[%s] not found in distro."%(s)
            sys.exit(1)
        seen.add(s)
        v = distro.stacks[s].version
        si = load_info(s, v)
        for d in si['depends']:
            add_stack(d)
        ordered_deps.append((s,v))

    if stack_name == 'ALL':
        for s in distro.stacks.keys():
            add_stack(s)
    else:
        add_stack(stack_name)

    return ordered_deps


_Packages_cache = {}

def deb_in_repo(deb_name, deb_version, os_platform, arch):
    # Retrieve the package list from the shadow repo
    packageurl="http://code.ros.org/packages/ros-shadow/ubuntu/dists/%(os_platform)s/main/binary-%(arch)s/Packages"%locals()
    if packageurl in _Packages_cache:
        packagelist = _Packages_cache[packageurl]
    else:
        _Packages_cache[packageurl] = packagelist = urllib2.urlopen(packageurl).read()
    str = 'Package: %s\nVersion: %s'%(deb_name, deb_version)
    return str in packagelist

class ExclusionList(object):
    def __init__(self, uri, distro_name, os_platform, arch):
        self.excludes_yaml = yaml.load(urllib2.urlopen(uri).read())
        if distro_name in self.excludes_yaml:
            self.excludes = self.excludes_yaml[distro_name]
        else:
            self.excludes = {}
        self.key = "%s-%s"%(os_platform,arch)

    def check(self, stack):
        return stack in self.excludes and self.key in self.excludes[stack]


def get_missing(distro, os_platform, arch):
    distro_name = distro.release_name
    # Load the list of exclusions
    excludes_uri = "https://code.ros.org/svn/release/trunk/distros/%s.excludes"%(distro_name)
    excludes = ExclusionList(excludes_uri, distro_name, os_platform, arch)

    # Find all the deps in the distro for this stack
    deps = compute_deps(distro, 'ALL')

    missing_primary = set()
    missing_dep = set()
    missing_excluded = set()
    missing_excluded_dep = set()

    # Build the deps in order
    for (sn, sv) in deps:
        deb_name = "ros-%s-%s"%(distro_name, debianize_name(sn))
        deb_version = debianize_version(sv, '0', os_platform)
        if not deb_in_repo(deb_name, deb_version, os_platform, arch):
            si = load_info(sn, sv)
            depends = set(si['depends'])
            if excludes.check(sn):
                missing_excluded.add(sn)
                missing_primary.add(sn)
            elif depends.isdisjoint(missing_primary.union(missing_dep)):
                missing_primary.add(sn)
            else:
                missing_dep.add(sn)
                if not depends.isdisjoint(missing_excluded.union(missing_excluded_dep)):
                    missing_excluded_dep.add(sn)

    missing_primary -= missing_excluded
    missing_dep -= missing_excluded_dep

    return missing_primary, missing_dep, missing_excluded, missing_excluded_dep

def list_missing(distro, os_platform, arch):
    distro_name = distro.release_name
    missing_primary, missing_dep, missing_excluded, missing_excluded_dep = get_missing(distro, os_platform, arch)

    print "[%s %s %s]"%(distro_name, os_platform, arch)
    print "\nThe following stacks are missing but have deps satisfied: (%s)"%(len(missing_primary))
    print '\n'.join([" %s"%x for x in missing_primary])
    print "\nThe following stacks are missing deps: (%s)"%(len(missing_dep))
    print '\n'.join([" %s"%x for x in missing_dep])
    if missing_excluded:
        print "\nThe following stacks are excluded: (%s)"%(len(missing_excluded))
        print '\n'.join([" %s"%x for x in missing_excluded])
    if missing_excluded_dep:
        print "\nThe following stacks have deps on excluded stacks: (%s)"%(len(missing_excluded_dep))
        print '\n'.join([" %s"%x for x in missing_excluded_dep])


    return missing_primary, missing_dep

def load_distro(distro_name):
    # Load the distro from the URL
    # TODO: Should this be done from file in release repo instead (and maybe updated in case of failure)
    distro_uri = "https://code.ros.org/svn/release/trunk/distros/%s.rosdistro"%distro_name
    return Distro(distro_uri)

def generate_allhtml_report(output, distro_name, os_platforms):
    distro = load_distro(distro_name)
    missing_primary = None
    missing_dep = None

    bad = {}
    for os_platform in os_platforms:
        bad[os_platform] = {}

    stacks = {}
    for stack in distro.stacks.keys():
        stacks[stack] = {}

    MISSING_PRIMARY = '-'
    MISSING_DEP = '<-'
    MISSING_EXCLUDED = 'X'
    MISSING_EXCLUDED_DEP = '<X'
    colors = {
        MISSING_PRIMARY: 'red',
        MISSING_DEP: 'pink',
        MISSING_EXCLUDED: 'grey',
        MISSING_EXCLUDED_DEP: 'grey',
        }
    
    arches = ['amd64', 'i386']
    for os_platform in os_platforms:
        for arch in arches:
           missing_primary, missing_dep, missing_excluded, missing_excluded_dep = get_missing(distro, os_platform, arch)
           key = "%s-%s"%(os_platform, arch)
           for s in missing_primary:
               stacks[s][key] = MISSING_PRIMARY
           for s in missing_dep:
               stacks[s][key] = MISSING_DEP
           for s in missing_excluded:
               stacks[s][key] = MISSING_EXCLUDED
           for s in missing_excluded_dep:
               stacks[s][key] = MISSING_EXCLUDED_DEP
           
    with open(output, 'w') as f:
        f.write("""<html>
<head>
<title>
%(distro_name)s: debbuild report
</title>
</head>
<style type="text/css">
body {
  font-family: 'Helvetica, Arial, Verdana, sans-serif';
}
</style>
<body>
<h1>%(distro_name)s: debbuild report</h1>"""%locals())

        f.write("""Legend:
<ul>
<li>Missing: %s</li>
<li>Depends Missing: %s</li>
<li>Excluded: %s</li>
<li>Depends Excluded: %s</li>
</ul>"""%(MISSING_PRIMARY, MISSING_DEP,MISSING_EXCLUDED, MISSING_EXCLUDED_DEP))
        f.write("""<table cellspacing=0 border="1">
<tr>
<th>Stack</th>""")
        
        for os_platform in os_platforms:
            for arch in arches:
                f.write('<th>%s-%s</th>'%(os_platform, arch))
        f.write('</tr>')

        stack_names = sorted(stacks.keys())
        for stack in stack_names:
            d = stacks[stack]
            f.write('<tr><td>%s</td>'%(stack))
            for os_platform in os_platforms:
                for arch in arches:
                    key = "%s-%s"%(os_platform, arch)
                    if key in d:
                        val = d[key]
                        color = colors[val]
                        f.write('<td bgcolor="%s">%s</td>'%(color, val))
                    else:
                        f.write('<td>&nbsp;</td>')
            f.write('</tr>\n')            

        f.write('\n</table></body></html>')
        

def list_missing_main():

    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog <distro> <os-platform> <arch>", prog=NAME)
    parser.add_option("--all", help="run on all os/arch combos for known distro",
                      dest="all", default=False, action="store_true")
    parser.add_option("--allhtml", help="generate html report", 
                      dest="allhtml", default=False, action="store_true")

    (options, args) = parser.parse_args()

    if not options.all and not options.allhtml:
        if len(args) != 3:
            parser.error('invalid args')
        
        distro_name, os_platform, arch = args
        list_missing(load_distro(distro_name), os_platform, arch)

    # the logic here allows both --all and --allhtml to be invoked 
    if options.all:
        if len(args) != 1:
            parser.error('invalid args: only specify <distro> when using --all')
        distro_name = args[0]
        try:
            import rosdeb.targets
            targets = rosdeb.targets.os_platform[distro_name]
        except:
            parser.error("unknown distro for --all target")

        distro = load_distro(distro_name)
        missing_primary = None
        missing_dep = None
        for os_platform in targets:
            for arch in ['amd64', 'i386']:
                list_missing(distro, os_platform, arch)
                print '-'*80
                
    if options.allhtml:

        if len(args) != 1:
            parser.error('invalid args: only specify <distro> when using --all')
        distro_name = args[0]
        try:
            import rosdeb.targets
            os_platforms = rosdeb.targets.os_platform[distro_name]
        except:
            parser.error("unknown distro for --all target")

        output = 'report.html'
        generate_allhtml_report(output, distro_name, os_platforms)
        
        
if __name__ == '__main__':
    list_missing_main()


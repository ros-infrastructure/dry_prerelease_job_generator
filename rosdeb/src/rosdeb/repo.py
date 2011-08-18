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

"""
Utilities for reading state from a debian repo
"""

import urllib2
import re

from .core import debianize_name

class BadRepo(Exception): pass

_Packages_cache = {}
def get_Packages(repo_url, os_platform, arch):
    """
    Retrieve the package list from the shadow repo. This routine
    utilizes a cache and should not be invoked in long-running
    processes.
    @raise BadRepo: if repo does not exist
    """
    packages_url = repo_url + '/ubuntu/dists/%(os_platform)s/main/binary-%(arch)s/Packages'%locals()
    if packages_url in _Packages_cache:
        return _Packages_cache[packages_url]
    else:
        try:
            _Packages_cache[packages_url] = retval = urllib2.urlopen(packages_url).read()
        except urllib2.HTTPError:
            raise BadRepo(repo_url)            
    return retval
    
def parse_Packages(packagelist):
    """
    Parse debian Packages list into (package, version, depends) tuples
    @return: parsed tuples or None if packagelist is None
    """
    package_deps = []
    package = deps = version = distro = None
    for l in packagelist.split('\n'):
        if l.startswith('Package: '):
            package = l[len('Package: '):]
        elif l.startswith('Version: '):
            version = l[len('Version: '):]
        elif l.startswith('Depends: '):
            deps = l[len('Depends: '):].split(',')
            deps = [d.strip() for d in deps]
        elif l.lower().startswith('wg-rosdistro: '):
            distro = l[len('wg-rosdistro: '):]
        if package != None and version != None and deps != None and distro != None:
            package_deps.append((package, version, deps, distro))
            package = version = deps = distro = None
    return package_deps
    
def load_Packages(repo_url, os_platform, arch):
    """
    Download and parse debian Packages list into (package, version, depends) tuples
    """
    return parse_Packages(get_Packages(repo_url, os_platform, arch))

def get_repo_version(repo_url, distro, os_platform, arch):
    """
    Return the greatest build-stamp for any deb in the repository
    """
    packagelist = load_Packages(repo_url, os_platform, arch)
    return max(['0'] + [x[1][x[1].find('-')+1:x[1].find('~')] for x in packagelist if x[3] == distro.release_name])

#    deb_name = "ros-%s-ros"%(distro.release_name)
#    matches = [x for x in packagelist if x[0] == deb_name]
#    if not matches:
#        return None
#    version = matches[0][1]
#    return version[version.find('-')+1:version.find('~')]



def deb_in_repo(repo_url, deb_name, deb_version, os_platform, arch, use_regex=True):
    packagelist = get_Packages(repo_url, os_platform, arch)
    if not use_regex:
        s = 'Package: %s\nVersion: %s'%(deb_name, deb_version)
        return s in packagelist
    else:
        M = re.search('^Package: %s\nVersion: %s$'%(deb_name, deb_version), packagelist, re.MULTILINE)
        return M is not None

def get_depends(repo_url, deb_name, os_platform, arch):
    """
    Get all debian package dependencies by scraping the Packages
    list. We mainly use this for invalidation logic. 
    """
    # There is probably something much simpler we could do, but this
    # more robust to any bad state we may have caused to the shadow
    # repo.
    #TODOXXX:remove print
    print "loading Packages from [%s]"%(repo_url)
    package_deps = load_Packages(repo_url, os_platform, arch)
    #TODOXXX:remove print
    print "got package list"
    done = False
    queue = [deb_name]
    depends = set()
    # This is not particularly efficient, but it does not need to
    # be. Basically, we find all the packages that depend on the
    # package, then find all the packages that depends on those,
    # etc...
    while queue:
        next  = queue[0]
        queue = queue[1:]
        #TODOXXX:remove
        print "QUEUE", queue
        for package, _, deps, _ in package_deps:
            #strip of version specifications from deps
            deps = [d.split()[0] for d in deps]
            if package not in depends and next in deps:
                queue.append(package)
                depends.add(package)
    print "get_depends done", depends
    return list(depends)

def get_stack_version(packageslist, distro_name, stack_name):
    """
    Get the ROS version number of the stack in the repository
    """
    deb_name = "ros-%s-%s"%(distro_name, debianize_name(stack_name))
    match = [vm for sm, vm, _, _ in packageslist if sm == deb_name]
    if match:
        return match[0].split('-')[0]
    else:
        return None


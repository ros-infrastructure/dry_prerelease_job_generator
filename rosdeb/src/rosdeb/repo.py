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

def get_Packages(packages_url):
    # Retrieve the package list from the shadow repo
    return urllib2.urlopen(packages_url).read()
    
def parse_Packages(packagelist):
    """
    Parse debian Packages list into (package, version, depends) tuples
    """
    package_deps = []
    package = deps = version = None
    for l in packagelist.split('\n'):
        if l.startswith('Package: '):
            package = l[len('Package: '):]
        elif l.startswith('Version: '):
            version = l[len('Version: '):]
        elif l.startswith('Depends: '):
            deps = l[len('Depends: '):].split(',')
            deps = [d.strip() for d in deps]
        if package != None and version != None and deps != None:
            package_deps.append((package, version, deps))
            package = version = deps = None
    return package_deps
    
def load_Packages(packages_url):
    """
    Download and parse debian Packages list into (package, version, depends) tuples
    """
    return parse_Packages(get_Packages(packages_url))

def deb_in_repo(packages_url, deb_name, deb_version):
    packagelist = get_Packages(packages_url)
    str = 'Package: %s\nVersion: %s'%(deb_name, deb_version)
    return str in packagelist

def get_depends(packages_url, deb_name):
    """
    Get all debian package dependencies by scraping the Packages
    list. We mainly use this for invalidation logic. 
    """
    # There is probably something much simpler we could do, but this
    # more robust to any bad state we may have caused to the shadow
    # repo.
    package_deps = load_Packages(packages_url)

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
        for package, _, deps in package_deps:
            if package not in depends and next in deps:
                queue.append(package)
                depends.add(package)
    return list(depends)


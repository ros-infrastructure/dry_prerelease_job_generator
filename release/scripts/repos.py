#!/usr/bin/env python

# source code refers to 'stacks', but this can work with apps as well
from __future__ import with_statement
PKG = 'release'
import roslib; roslib.load_manifest(PKG)
NAME="repos.py"

import sys
import os
import re
import os
import traceback
import yaml

from rosdistro import Distro, DistroException

def create_matchers(repo_name):
    return [
        # repo-name.git
        re.compile(".*/%s\.git*"%(repo_name)),
        # http://repo-name.com
        re.compile(".*//\.%s\..*"%(repo_name)),
        # /repo-name.
        re.compile("./*%s\..*"%(repo_name)),
        # /repo-name
        re.compile("./*%s"%(repo_name)),
        # /repo-name./
        re.compile("./*%s/.*"%(repo_name)),
        # www.repo-name.com
        re.compile(".*\.%s\..*"%(repo_name)),
        # bad, delete
        #re.compile('.*%s.*'%repo_name),

        ]

def main():
    try:
        from optparse import OptionParser
        parser = OptionParser(usage="usage: %prog <release> <repo>", prog=NAME)
        options, args = parser.parse_args()
        if len(args) != 2:
            parser.error("""You must specify: 
 * release name
 * repository name (e.g. ros-pkg)""")
        release_name, repo_name = args
        if release_name.endswith('.rosdistro'):
            release_name = release_name[:-len('.rosdistro')]

        print "release name", release_name
        
        # load in an expand URIs for rosinstalls
        #distro = Distro("http://ros.org/distros/%s.rosdistro"%release_name)
        # now loading from direct svn copy
        distro = Distro("https://code.ros.org/svn/release/trunk/distros/%s.rosdistro"%release_name)

        uris = {}
        for stack_name, stack in distro.stacks.iteritems():
            vcs = stack.vcs_config
            if vcs.type == 'svn':
                uri = vcs.dev
            elif vcs.type == 'hg':
                uri = vcs.repo_uri                
            uris[stack_name] = uri

        # Determine the stack list to use (in order of preference):
        #  - special handling for ros and ros-pkg
        #  - check for variant of same name
        #  - use regular expression match
        stack_list = []
        if repo_name in ['ros', 'ros-pkg']:
            match = 'https://code.ros.org/svn/%s/'%(repo_name)
            stack_list = [s for s, uri in uris.iteritems() if uri.startswith(match)]
        elif repo_name in distro.variants:
            stack_list = distro.variants[repo_name].stack_names
        else:
            # regular expression: search for /repo-name/ or .repo-name.
            matchers = create_matchers(repo_name)
            for s, uri in uris.iteritems():
                for m in matchers:
                    if m.search(uri):
                        stack_list.append(s)
                        break

        if not stack_list:
            raise Exception("no matches for [%s]"%(repo_name))
        stack_list.sort()

        # create text for rosinstall file
        variant_rosinstalls = []
        tmpl = """- svn:
    uri: %(uri)s
    local-name: %(stack_name)s
"""

        variant_stacks = {}
        variant_stacks_extended = {}

        pkg_dir = roslib.packages.get_pkg_dir('release_resources')
        rosinstall_dir = os.path.join(pkg_dir, 'repos', repo_name)
        filename = os.path.join(rosinstall_dir, "%s_%s.rosinstall"%(repo_name, release_name))
        filename = os.path.abspath(filename)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        text = ''
        for stack_name in stack_list:
            # TODO: this does not handle hg properly
            vcs = distro.stacks[stack_name].vcs_config
            if vcs.type != 'svn':
                raise Exception('only support svn so far')
            uri = distro.stacks[stack_name].vcs_config.distro_tag
            text += tmpl%locals()

        print "writing %s"%(filename)
        with open(filename, 'w') as f:
            f.write(text)

    except Exception, e:
        traceback.print_exc()
        print >> sys.stderr, "ERROR: %s"%str(e)
        sys.exit(1)


if __name__ == '__main__':
    main()

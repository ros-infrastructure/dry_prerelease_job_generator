#!/usr/bin/env python

"""
This script checks for differences between two rosdistro files. It only compares the information, not the actual structure.
It only compares common points of difference (e.g. stacks lists, versions).
"""
import roslib; roslib.load_manifest('release')
NAME="distro_diff.py"

import sys
import os
import os.path
import traceback

from rosdistro import Distro, DistroException

import release

def blog_post(released):
    print ', '.join(["%s %s"%(stack, version) for stack, version in released])
    print ""

    for stack, version in released:
        stack_safe = stack.replace('_', '\_')
        print " * [%(stack_safe)s](http://ros.org/wiki/%(stack)s) [%(version)s](http://ros.org/wiki/%(stack)s/ChangeList)"%locals()

    print ','.join([stack for stack, _ in released])

def main():
    released = []
    try:
        from optparse import OptionParser
        parser = OptionParser(usage="usage: %prog <distro-file> <distro-file>", prog=NAME)
        parser.add_option("--blog", 
                          dest="blog_post", default=False,
                          action="store_true",
                          help="create data for blog post")
        options, args = parser.parse_args()
        if len(args) != 2:
            parser.error("You must specify two distro files")

        d1, d2 = [Distro(x) for x in args[:2]]

        # Compare
        # - release name
        # - _rules (per stack)
        # - stack versions

        if d1.release_name != d2.release_name:
            print "release"
            print "< %s"%(d1.release_name)
            print "> %s"%(d2.release_name)
            
        d1s = set(d1.stacks.keys())
        d2s = set(d2.stacks.keys())
        if d1s ^ d2s:
            print "stacks"
            if d1s - d2s:
                print "< %s"%(', '.join(d1s-d2s))
            if d2s - d1s:
                print "> %s"%(', '.join(d2s-d1s))

        # for every stack in from, copy to the new distro
        for stack_name, stack1 in d1.stacks.iteritems():
            stack2 = d2.stacks.get(stack_name, None)
            if stack2 is None:
                continue

            if stack1.version != stack2.version:
                print stack_name
                print "< %s"%(stack1.version)
                print "> %s"%(stack2.version)
                released.append((stack2.name, stack2.version))

            if stack1.distro_svn != stack2.distro_svn or \
                    stack1.release_svn != stack2.release_svn or \
                    stack1.dev_svn != stack2.dev_svn:
                print "[%s]: rules differ"%(stack_name)

        for variant_name, v1 in d1.variants.iteritems():
            v2 = d2.variants.get(variant_name, None)
            if v2 is None:
                continue
            
            v1s = set(v1.stack_names)
            v2s = set(v2.stack_names)
            if v1s ^ v2s:
                print "variant[%s]"%(variant_name)
                if v1s - v2s:
                    print "< %s"%(', '.join(v1s-v2s))
                if v2s - v1s:
                    print "> %s"%(', '.join(v2s-v1s))
            

        if options.blog_post:
            print '='*80
            print ''
            blog_post(released)
    except Exception, e:
        traceback.print_exc()
        print >> sys.stderr, "ERROR: %s"%str(e)
        sys.exit(1)

if __name__ == '__main__':
    main()

#! /usr/bin/env python
import roslib
roslib.load_manifest('rosdeb')
from rosdeb.repo import *
import sys
import os
from optparse import OptionParser


def main(argv, stdout, environ):

  parser = OptionParser()

  (options, args) = parser.parse_args()

  if (len(args) != 5):
    parser.error("diff_repos.py <distro> <platform> <arch> <REPO1> <REPO2>")

  distro,platform,arch,repo0,repo1 = args

  P0 = load_Packages(repo0, platform, arch)
  P1 = load_Packages(repo1, platform, arch)

  P0m = {}
  P1m = {}

  for p in P0:
    if 'ros-'+distro in p[0]:
      P0m[p[0]] = p[1].split('-')[0]

  for p in P1:
    if 'ros-'+distro in p[0]:
      P1m[p[0]] = p[1].split('-')[0]

  for (p,v) in P1m.iteritems():
    if p in P0m:
        if P0m[p] != v:
            print '%s: %s -> %s'%(p, P0m[p], v)
    else:
        print '%s: new'%p


if __name__ == "__main__":
  main(sys.argv, sys.stdout, os.environ)

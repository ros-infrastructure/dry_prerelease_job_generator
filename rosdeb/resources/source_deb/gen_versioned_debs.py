#! /usr/bin/env python

"""
usage: %prog [args]
"""

import os, sys, string
from optparse import OptionParser
import subprocess
import roslib

def main(argv, stdout, environ):

  parser = OptionParser(__doc__.strip())

  (options, args) = parser.parse_args()

  if (len(args) != 2):
    parser.error("Usage: <distro> <stack>")
    
  distro,stack = args

  deps = []
  
  for stk in roslib.rospack.rosstack_depends_1(stack):
    version = None
    debname = "ros-%s-%s"%(distro, stk.replace('_','-'))
    cmd = subprocess.Popen(['dpkg', '-s', debname], stdout=subprocess.PIPE)
    o,e = cmd.communicate()
    if cmd.returncode != 0:
      raise "Could not find dependency version number"
    for l in o.splitlines():
      if l.startswith('Version:'):
        version = l.split()[1].strip()
    if version:
      deps.append("%s (= %s)"%(debname,version))
    else:
      raise "Could not find dependency version number"

  print "rosstack:Depends="+", ".join(deps)


if __name__ == "__main__":
  main(sys.argv, sys.stdout, os.environ)

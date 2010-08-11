#! /usr/bin/env python

"""
usage: %prog [args]
"""

import os, sys, string
from optparse import OptionParser
import subprocess

def main(argv, stdout, environ):

  parser = OptionParser(__doc__.strip())
  parser.add_option("-t","--test",action="store_true", dest="test",default=False,
                    help="A testing flag")
  parser.add_option("--path",action="store",dest="path",default=".")
#  parser.add_option("-v","--var",action="store",type="string", dest="var",default="blah")

  (options, args) = parser.parse_args()

  if (len(args) < 2):
    print >> sys.stderr, 'Need to pass rpath token to replace'
    sys.exit(1)
    
  old_rpath = args[0]
  new_rpath = args[1]

  if len(old_rpath) < len(new_rpath):
    print >> sys.stderr, "New rpath must be shorter than old rpath"
    sys.exit(1)

  print 'Replacing: %s'%old_rpath
  print '     with: %s'%new_rpath

  for root, dirs, files in os.walk(options.path):
    for f in files:

      r = subprocess.Popen(['chrpath', os.path.join(root,f)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      (o,e) = r.communicate()

      if (r.returncode == 0):

        rp = o.split('RPATH=')[1].strip()

        if old_rpath in rp:
          print 'Updating: %s'%(os.path.join(root,f))
          newrp = rp.replace(old_rpath, new_rpath)
          subprocess.check_call(['chrpath', os.path.join(root,f), '-r', newrp])
      
  


if __name__ == "__main__":
  main(sys.argv, sys.stdout, os.environ)

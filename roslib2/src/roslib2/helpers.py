import os
import urlparse
import urllib2
import yaml
import subprocess
import sys

def conditional_abspath(uri):
  """
  @param uri: The uri to check
  @return: abspath(uri) if local path otherwise pass through uri
  """
  u = urlparse.urlparse(uri)
  if u.scheme == '': # maybe it's a local file?
    return os.path.abspath(uri)
  else:
    return uri

def is_path_stack(path):
  """
  
  @return: True if the path provided is the root of a stack.
  """
  stack_path = os.path.join(path,'stack.xml')
  if os.path.isfile(stack_path):
    return True
  return False

def is_path_ros(path):
  """
  warning: exits with code 1 if stack document is invalid
  @param path: path of directory to check
  @type  path: str
  @return: True if path points to the ROS stack
  @rtype: bool
  """
  stack_path = os.path.join(path,'stack.xml')
  if os.path.isfile(stack_path):
    return 'ros' == os.path.basename(path)
  return False


def get_yaml_from_uri(uri):

  # now that we've got a config uri and a path, let's move out.
  u = urlparse.urlparse(uri)
  f = 0
  if u.scheme == '': # maybe it's a local file?
    try:
      f = open(uri, 'r')
    except IOError, e:
      print >> sys.stderr, "ahhhh error opening file: %s" % e
      return None
  else:
    try:
      f = urllib2.urlopen(uri)
    except IOError, e:
      print >> sys.stderr, "ahhhhh got an error from the interwebs: %s" % e
  if not f:
    print >> sys.stderr, "couldn't load config uri %s" % uri
    return None
  try:
    y = yaml.load(f);
  except yaml.YAMLError, e:
    print >> sys.stderr, "ahhhhhhhh, yaml parse error: %s" % e # long ahh
    return None
  return y
  
### TODO remove BASH usage
def get_ros_root_from_file(file):
  out = subprocess.Popen("source %s && echo $ROS_ROOT" % file, stdout=subprocess.PIPE, env=None, shell=True, executable="/bin/bash").communicate()[0].strip() # oh yeah
  print out
  return out

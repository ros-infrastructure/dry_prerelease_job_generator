import os
import urlparse


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



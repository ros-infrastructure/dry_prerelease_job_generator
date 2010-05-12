
from distutils.core import setup

setup(name='rosinstall',
      version='0.04.4',
      packages=['rosinstall', 'rosinstall.vcs'],
      package_dir = {'':'src'},
      scripts = ["scripts/rosinstall"],
      author = "Tully Foote", 
      author_email = "tfoote@willowgarage.com",
      url = "http://www.ros.org/wiki/rosinstall",
      download_url = "http://pypi.python.org/packages/source/r/roslib2/roslib2-0.01.tar.gz", 
      keywords = ["ROS"],
      classifiers = [
        "Programming Language :: Python", 
        "License :: OSI Approved :: BSD License" ],
      long_description = """\
The installer for ROS
"""
      )

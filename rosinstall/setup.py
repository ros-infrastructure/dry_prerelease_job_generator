
from distutils.core import setup

setup(name='rosinstall',
      version='0.01',
      packages=['rosinstall'],
      package_dir = {'':'src'},
      scripts = ["scripts/rosinstall"],
      requires = ['roslib2'],
      author = "Tully Foote", 
      author_email = "tfoote@willowgarage.com",
      url = "http://www.ros.org/wiki/rosinstall",
      download_url = "http://code.ros.org/rosinstall-0.1.tar.gz", 
      keywords = ["ROS"],
      classifiers = [
        "Programming Language :: Python", 
        "License :: OSI Approved :: BSD" ],
      long_description = """\
The installer for ROS
"""
      )

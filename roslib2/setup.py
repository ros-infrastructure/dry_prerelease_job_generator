
from distutils.core import setup

setup(name='roslib2',
      version='0.01',
      packages=['roslib2','roslib2.vcs'],
      package_dir = {'':'src'},
      author = "Tully Foote", 
      author_email = "tfoote@willowgarage.com",
      url = "http://www.ros.org/wiki/rosinstall",
      download_url = "http://pypi.python.org/packages/source/r/roslib2/roslib2-0.01.tar.gz", 
      keywords = ["ROS"],
      classifiers = [
        "Programming Language :: Python", 
        "License :: OSI Approved :: BSD License" ],
      long_description = """\
The helpers for rosinstall
"""
      )

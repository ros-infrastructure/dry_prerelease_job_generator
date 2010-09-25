
from distutils.core import setup

setup(name='ros-prerelease',
      version='0.1.0',
      scripts = ["ros-prerelease.py", "ros_prerelease_jobs_common.py", "ros_prerelease_hudson.py"],
      author = "Wim Meeussen", 
      author_email = "wim@willowgarage.com",
      url = "http://www.ros.org/wiki/ros-prerelease",
      download_url = "http://pypi.python.org/packages/source/r/ros-prerelease/ros-prerelease-0.1.0.tar.gz", 
      keywords = ["ROS"],
      classifiers = [
        "Programming Language :: Python", 
        "License :: OSI Approved :: BSD License" ],
      long_description = """\
The prerelease build scheduler
"""
      )

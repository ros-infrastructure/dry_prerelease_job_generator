
import subprocess

from distutils.core import setup

po = subprocess.Popen('scripts/version.py')
(stdout, stderr) = po.communicate()

setup(name='rosinstall',
      version= stdout,
      packages=['rosinstall', 'rosinstall.vcs'],
      package_dir = {'':'src'},
      scripts = ["scripts/rosinstall", "scripts/roslocate"],
      author = "Tully Foote", 
      author_email = "tfoote@willowgarage.com",
      url = "http://www.ros.org/wiki/rosinstall",
      download_url = "http://pr.willowgarage.com/downloads/rosinstall/", 
      keywords = ["ROS"],
      classifiers = [
        "Programming Language :: Python", 
        "License :: OSI Approved :: BSD License" ],
      long_description = """\
The installer for ROS
"""
      )

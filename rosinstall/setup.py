
import subprocess

from distutils.core import setup

po = subprocess.Popen('scripts/version.py', stdout=subprocess.PIPE)
(stout, sterr) = po.communicate()
print "version is %s asdf"%stout
stout = stout.strip()

setup(name='rosinstall',
      version= stout,
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
      description = "The installer for ROS", 
      long_description = """\
The installer for ROS
""",
      license = "BSD"
      )

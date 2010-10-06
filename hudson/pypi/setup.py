import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "hudson_remote_interface",
    version = "0.0.1",
    author = "Ken Conley Maintained by Tully Foote",
    author_email = "tfoote@willowgarage.com",
    description = ("A remote interface for using Hudson Continuous Integration"),
    license = "BSD",
    keywords = "hudson remote interface",
    url = "http://packages.python.org/hudson_remote_interface",
    packages=['hudson'],
    #scripts=['hudson.py'],
    #long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)

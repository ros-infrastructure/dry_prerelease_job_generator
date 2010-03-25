#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
import roslib; roslib.load_manifest('test_rosinstall')

import os
import stat
import struct
import sys
import unittest
import subprocess
import tempfile
import urllib
import shutil

import rostest


class RosinstallCommandlineTest(unittest.TestCase):

    def setUp(self):
        self.rosinstall_tempfile = tempfile.NamedTemporaryFile(mode='a+b')
        self.rosinstall_fn = "/tmp/test_rosinstall_temp_version"
        urllib.urlretrieve("https://code.ros.org/svn/ros/installers/trunk/rosinstall/rosinstall2", self.rosinstall_fn)
        os.chmod(self.rosinstall_fn, stat.S_IRWXU)
        self.directories = {}


    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])
        os.remove(self.rosinstall_fn)

    def test_Rosinstall_executable(self):
        self.assertEqual(0,subprocess.call([self.rosinstall_fn, "-h"]))

    def test_Rosinstall_ros(self):
        directory = tempfile.mkdtemp()
        self.directories["ros"] = directory
        self.assertEqual(0,subprocess.call([self.rosinstall_fn, directory, "http://www.ros.org/rosinstalls/boxturtle_ros.rosinstall"]))
        shutil.rmtree(directory)
        self.directories.pop("ros")

class RosinstallCommandlineOverlays(unittest.TestCase):

    def setUp(self):
        self.rosinstall_tempfile = tempfile.NamedTemporaryFile(mode='a+b')
        self.rosinstall_fn = "/tmp/test_rosinstall_temp_version"
        urllib.urlretrieve("https://code.ros.org/svn/ros/installers/trunk/rosinstall/rosinstall", self.rosinstall_fn)
        os.chmod(self.rosinstall_fn, stat.S_IRWXU)
        self.directories = {}
        self.base = tempfile.mkdtemp()
        self.assertEqual(0,subprocess.call([self.rosinstall_fn, self.base, "http://www.ros.org/rosinstalls/boxturtle_base.rosinstall"]))


    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])
        shutil.rmtree(self.base)
        os.remove(self.rosinstall_fn)

    def test_Rosinstall_ros_tutorial_as_overlay(self):
        directory = tempfile.mkdtemp()
        self.directories["tutorials"] = directory
        self.assertEqual(0,subprocess.call(["bash", "-c", "source %s && %s %s -o http://www.ros.org/rosinstalls/boxturtle_tutorials.rosinstall"%(os.path.join(self.base,"setup.sh"), self.rosinstall_fn, directory)]))

        shutil.rmtree(directory)
        self.directories.pop("tutorials")

    def test_Rosinstall_ros_tutorial_as_setup_file(self):
        directory = tempfile.mkdtemp()
        self.directories["tutorials2"] = directory
        self.assertEqual(0,subprocess.call([self.rosinstall_fn, directory, "-s", os.path.join(self.base,"setup.sh"), "http://www.ros.org/rosinstalls/boxturtle_tutorials.rosinstall"]))


        shutil.rmtree(directory)
        self.directories.pop("tutorials2")

if __name__ == '__main__':
  rostest.unitrun('test_rosinstall', 'test_commandline', RosinstallCommandlineTest, coverage_packages=['rosinstall'])  
  rostest.unitrun('test_rosinstall', 'test_commandline_overlay', RosinstallCommandlineOverlays, coverage_packages=['rosinstall'])  


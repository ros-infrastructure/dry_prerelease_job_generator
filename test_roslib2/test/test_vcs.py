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
import roslib; roslib.load_manifest('test_roslib2')

import os
import stat
import struct
import sys
import unittest
import subprocess
import tempfile
import urllib
import shutil
import roslib
import rostest
from roslib2.vcs import svn, bzr, git, hg

class SVNClientTest(unittest.TestCase):

    def setUp(self):
        self.directories = {}
        directory = tempfile.mkdtemp()
        name = "setUp"
        self.directories[name] = directory
        self.readonly_url = "https://code.ros.org/svn/ros/stacks/ros/trunk"
        self.readonly_version = "-r8800"
        self.readonly_path = os.path.join(directory, "readonly")
        svnc = svn.SVNClient(self.readonly_path)
        self.assertTrue(svnc.checkout(self.readonly_url, self.readonly_version))

    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])

    def test_get_url_by_reading(self):
        svnc = svn.SVNClient(self.readonly_path)
        self.assertTrue(svnc.path_exists())
        self.assertTrue(svnc.detect_presence())
        self.assertEqual(svnc.get_url(), self.readonly_url)
        #self.assertEqual(svnc.get_version(), self.readonly_version)


    def test_get_type_name(self):
        local_path = "/tmp/dummy"
        svnc = svn.SVNClient(local_path)
        self.assertEqual(svnc.get_vcs_type_name(), 'svn')

    def test_checkout(self):
        directory = tempfile.mkdtemp()
        self.directories["checkout_test"] = directory
        local_path = os.path.join(directory, "ros")
        url = "https://code.ros.org/svn/ros/stacks/ros/trunk"
        svnc = svn.SVNClient(local_path)
        self.assertFalse(svnc.path_exists())
        self.assertFalse(svnc.detect_presence())
        self.assertFalse(svnc.detect_presence())
        self.assertTrue(svnc.checkout(url))
        self.assertTrue(svnc.path_exists())
        self.assertTrue(svnc.detect_presence())
        self.assertEqual(svnc.get_path(), local_path)
        self.assertEqual(svnc.get_url(), url)

        #self.assertEqual(svnc.get_version(), '-r*')
        

        shutil.rmtree(directory)
        self.directories.pop("checkout_test")

    def test_checkout_specific_version_and_update(self):
        directory = tempfile.mkdtemp()
        subdir = "checkout_specific_version_test"
        self.directories[subdir] = directory
        local_path = os.path.join(directory, "ros")
        url = "https://code.ros.org/svn/ros/stacks/ros/trunk"
        version = "-r8800"
        svnc = svn.SVNClient(local_path)
        self.assertFalse(svnc.path_exists())
        self.assertFalse(svnc.detect_presence())
        self.assertFalse(svnc.detect_presence())
        self.assertTrue(svnc.checkout(url, version))
        self.assertTrue(svnc.path_exists())
        self.assertTrue(svnc.detect_presence())
        self.assertEqual(svnc.get_path(), local_path)
        self.assertEqual(svnc.get_url(), url)
        #self.assertEqual(svnc.get_version(), version)
        
        new_version = '-r8801'
        self.assertTrue(svnc.update(new_version))
        #self.assertEqual(svnc.get_version(), new_version)
        
        shutil.rmtree(directory)
        self.directories.pop(subdir)


class BZRClientTest(unittest.TestCase):

    def setUp(self):
        self.directories = {}
        directory = tempfile.mkdtemp()
        name = "setUp"
        self.directories[name] = directory
        self.readonly_url = "http://bazaar.launchpad.net/~tully.foote/ffm/trunk/"
        self.readonly_version = "-r24"
        self.readonly_path = os.path.join(directory, "readonly")
        bzrc = bzr.BZRClient(self.readonly_path)
        self.assertTrue(bzrc.checkout(self.readonly_url, self.readonly_version))

    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])

    def test_get_url_by_reading(self):
        bzrc = bzr.BZRClient(self.readonly_path)
        self.assertTrue(bzrc.path_exists())
        self.assertTrue(bzrc.detect_presence())
        self.assertEqual(bzrc.get_url(), self.readonly_url)
        #self.assertEqual(bzrc.get_version(), self.readonly_version)


    def test_get_type_name(self):
        local_path = "/tmp/dummy"
        bzrc = bzr.BZRClient(local_path)
        self.assertEqual(bzrc.get_vcs_type_name(), 'bzr')

    def test_checkout(self):
        directory = tempfile.mkdtemp()
        self.directories["checkout_test"] = directory
        local_path = os.path.join(directory, "ros")
        url = "http://bazaar.launchpad.net/~tully.foote/ffm/trunk/"
        bzrc = bzr.BZRClient(local_path)
        self.assertFalse(bzrc.path_exists())
        self.assertFalse(bzrc.detect_presence())
        self.assertFalse(bzrc.detect_presence())
        self.assertTrue(bzrc.checkout(url))
        self.assertTrue(bzrc.path_exists())
        self.assertTrue(bzrc.detect_presence())
        self.assertEqual(bzrc.get_path(), local_path)
        self.assertEqual(bzrc.get_url(), url)

        #self.assertEqual(bzrc.get_version(), '-r*')
        

        shutil.rmtree(directory)
        self.directories.pop("checkout_test")

    def test_checkout_specific_version_and_update(self):
        directory = tempfile.mkdtemp()
        subdir = "checkout_specific_version_test"
        self.directories[subdir] = directory
        local_path = os.path.join(directory, "ros")
        url = "http://bazaar.launchpad.net/~tully.foote/ffm/trunk/"
        version = "-r20"
        bzrc = bzr.BZRClient(local_path)
        self.assertFalse(bzrc.path_exists())
        self.assertFalse(bzrc.detect_presence())
        self.assertFalse(bzrc.detect_presence())
        self.assertTrue(bzrc.checkout(url, version))
        self.assertTrue(bzrc.path_exists())
        self.assertTrue(bzrc.detect_presence())
        self.assertEqual(bzrc.get_path(), local_path)
        self.assertEqual(bzrc.get_url(), url)
        #self.assertEqual(bzrc.get_version(), version)
        
        new_version = '-r21'
        self.assertTrue(bzrc.update(new_version))
        #self.assertEqual(bzrc.get_version(), new_version)
        
        shutil.rmtree(directory)
        self.directories.pop(subdir)


class GITClientTest(unittest.TestCase):

    def setUp(self):
        self.directories = {}
        directory = tempfile.mkdtemp()
        name = "setUp"
        self.directories[name] = directory
        self.readonly_url = "http://github.com/ipa320/care-o-bot.git"
        self.readonly_version = "d68b7ead0614228a2a352330aad17b617cac4c84"
        self.readonly_path = os.path.join(directory, "readonly")
        gitc = git.GITClient(self.readonly_path)
        self.assertTrue(gitc.checkout(self.readonly_url, self.readonly_version))

    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])

    def test_get_url_by_reading(self):
        gitc = git.GITClient(self.readonly_path)
        self.assertTrue(gitc.path_exists())
        self.assertTrue(gitc.detect_presence())
        self.assertEqual(gitc.get_url(), self.readonly_url)
        self.assertEqual(gitc.get_version(), self.readonly_version)


    def test_get_type_name(self):
        local_path = "/tmp/dummy"
        gitc = git.GITClient(local_path)
        self.assertEqual(gitc.get_vcs_type_name(), 'git')

    def test_checkout(self):
        directory = tempfile.mkdtemp()
        self.directories["checkout_test"] = directory
        local_path = os.path.join(directory, "ros")
        url = "http://github.com/ipa320/care-o-bot.git"
        gitc = git.GITClient(local_path)
        self.assertFalse(gitc.path_exists())
        self.assertFalse(gitc.detect_presence())
        self.assertFalse(gitc.detect_presence())
        self.assertTrue(gitc.checkout(url))
        self.assertTrue(gitc.path_exists())
        self.assertTrue(gitc.detect_presence())
        self.assertEqual(gitc.get_path(), local_path)
        self.assertEqual(gitc.get_url(), url)

        #self.assertEqual(gitc.get_version(), '-r*')
        

        shutil.rmtree(directory)
        self.directories.pop("checkout_test")

    def test_checkout_specific_version_and_update(self):
        directory = tempfile.mkdtemp()
        subdir = "checkout_specific_version_test"
        self.directories[subdir] = directory
        local_path = os.path.join(directory, "ros")
        url = "http://github.com/ipa320/care-o-bot.git"
        version = "d68b7ead0614228a2a352330aad17b617cac4c84"
        gitc = git.GITClient(local_path)
        self.assertFalse(gitc.path_exists())
        self.assertFalse(gitc.detect_presence())
        self.assertFalse(gitc.detect_presence())
        self.assertTrue(gitc.checkout(url, version))
        self.assertTrue(gitc.path_exists())
        self.assertTrue(gitc.detect_presence())
        self.assertEqual(gitc.get_path(), local_path)
        self.assertEqual(gitc.get_url(), url)
        self.assertEqual(gitc.get_version(), version)
        
        new_version = '1fd87b781c64de366c6a6d4be8cdc76fbee5541e'
        self.assertTrue(gitc.update(new_version))
        self.assertEqual(gitc.get_version(), new_version)
        
        shutil.rmtree(directory)
        self.directories.pop(subdir)


class HGClientTest(unittest.TestCase):

    def setUp(self):
        self.directories = {}
        directory = tempfile.mkdtemp()
        name = "setUp"
        self.directories[name] = directory
        self.readonly_url = "http://hg.addictivecode.org/wget/mainline"
        self.readonly_version = "013c8e2f5997"
        self.readonly_path = os.path.join(directory, "readonly")
        hgc = hg.HGClient(self.readonly_path)
        self.assertTrue(hgc.checkout(self.readonly_url, self.readonly_version))

    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])

    def test_get_url_by_reading(self):
        hgc = hg.HGClient(self.readonly_path)
        self.assertTrue(hgc.path_exists())
        self.assertTrue(hgc.detect_presence())
        self.assertEqual(hgc.get_url(), self.readonly_url)
        self.assertEqual(hgc.get_version(), self.readonly_version)


    def test_get_type_name(self):
        local_path = "/tmp/dummy"
        hgc = hg.HGClient(local_path)
        self.assertEqual(hgc.get_vcs_type_name(), 'hg')

    def test_checkout(self):
        directory = tempfile.mkdtemp()
        self.directories["checkout_test"] = directory
        local_path = os.path.join(directory, "ros")
        url = "http://hg.addictivecode.org/wget/mainline"
        hgc = hg.HGClient(local_path)
        self.assertFalse(hgc.path_exists())
        self.assertFalse(hgc.detect_presence())
        self.assertFalse(hgc.detect_presence())
        self.assertTrue(hgc.checkout(url))
        self.assertTrue(hgc.path_exists())
        self.assertTrue(hgc.detect_presence())
        self.assertEqual(hgc.get_path(), local_path)
        self.assertEqual(hgc.get_url(), url)

        #self.assertEqual(hgc.get_version(), )
        

        shutil.rmtree(directory)
        self.directories.pop("checkout_test")

    def test_checkout_specific_version_and_update(self):
        directory = tempfile.mkdtemp()
        subdir = "checkout_specific_version_test"
        self.directories[subdir] = directory
        local_path = os.path.join(directory, "ros")
        url = "http://hg.addictivecode.org/wget/mainline"
        version = "013c8e2f5997"
        hgc = hg.HGClient(local_path)
        self.assertFalse(hgc.path_exists())
        self.assertFalse(hgc.detect_presence())
        self.assertFalse(hgc.detect_presence())
        self.assertTrue(hgc.checkout(url, version))
        self.assertTrue(hgc.path_exists())
        self.assertTrue(hgc.detect_presence())
        self.assertEqual(hgc.get_path(), local_path)
        self.assertEqual(hgc.get_url(), url)
        self.assertEqual(hgc.get_version(), version)
        
        new_version = '38a0105c05ea'
        self.assertTrue(hgc.update(new_version))
        self.assertEqual(hgc.get_version(), new_version)
        
        shutil.rmtree(directory)
        self.directories.pop(subdir)


if __name__ == '__main__':
    rostest.unitrun('test_roslib2', 'test_vcs', GITClientTest, coverage_packages=['roslib2'])  
    rostest.unitrun('test_roslib2', 'test_vcs', BZRClientTest, coverage_packages=['roslib2'])  
    rostest.unitrun('test_roslib2', 'test_vcs', SVNClientTest, coverage_packages=['roslib2'])  
    rostest.unitrun('test_roslib2', 'test_vcs', HGClientTest,  coverage_packages=['roslib2'])  

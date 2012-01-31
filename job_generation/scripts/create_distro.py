#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2011, Willow Garage, Inc.
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
#
# Revision $Id: hudson.py 12523 2010-12-21 01:03:35Z tfoote $
# $Author: tfoote $

import os
import sys

import roslib.packages
import rosdeb.targets
import jenkins

if not len(sys.argv) == 4:
    print "Usage: create_distro <distro> <username> <password>"
    sys.exit(1)

_, distro, username, password = sys.argv

h = jenkins.Jenkins('http://build.willowgarage.com', username, password)

d = os.path.join(roslib.packages.get_pkg_dir('job_generation'), 'scripts')

with open(os.path.join(d, 'debbuild-build-debs.xml'), 'r') as f:
    config_xml = f.read()

os_repl = 'lucid'
arch_repl = 'amd64'

if not distro in rosdeb.targets.os_platform:
    raise Exception("Please update rosdeb.target.os_platform with key [%s]"%(distro))
platforms = rosdeb.targets.os_platform[distro]
for osp in platforms:
    for arch in ['i386', 'amd64']:
        job_xml = config_xml.replace(os_repl, osp).replace(arch_repl, arch)
        job = 'debbuild-build-debs-%s-%s-%s'%(distro, osp, arch)
        print "creating", job
        h.create_job(job, job_xml)

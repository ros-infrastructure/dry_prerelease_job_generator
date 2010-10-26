#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
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
# Revision $Id$

"""
Update Hudson jobs based on current target configuration
"""

import roslib; roslib.load_manifest('rosdeb')
import sys
import os
from rosdeb.targets import os_platform
import hudson

SERVER = 'http://build.willowgarage.com'

def usage():
    print "Usage: update_hudson.py <release> <hudson-user> <hudson-pass>"
    sys.exit(os.EX_USAGE)
    
BUILD_DEBS_STUB_JOB = 'debbuild-build-debs'
BUILD_DEBS_PATTERN  = 'debbuild-build-debs-%(release_name)s-%(platform)s-%(arch)s'

def update_jobs(h, release_name):
    targets = os_platform[release_name]
    for platform in targets:
        for arch in ['amd64', 'i386']:
            job_name = BUILD_DEBS_PATTERN%locals()
            if h.job_exists(job_name):
                print "Job [%s-%s] exists"%(platform, arch)
            else:
                print "Creating [%s-%s] %s"%(platform, arch, job_name)
                h.copy_job(BUILD_DEBS_STUB_JOB, job_name)
                
    
def update_main():
    if len(sys.argv) != 4:
        usage()
    release_name = sys.argv[1]
    if release_name not in os_platform:
        print >> sys.stderr, "Unknown release: %s"%(release_name)
        sys.exit(1)

    username, password = sys.argv[2:]
    
    h = hudson.Hudson(SERVER, username, password)

    update_jobs(h, release_name)
    

if __name__ == "__main__":
    update_main()

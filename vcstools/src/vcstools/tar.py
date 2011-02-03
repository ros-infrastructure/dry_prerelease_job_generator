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
"""
tar vcs support.

New in ROS C-Turtle.
"""

import subprocess
import os
import vcs_base
import yaml
import urllib
import tempfile
import sys
import shutil

class TARClient(vcs_base.VCSClientBase):
    def __init__(self, path):
        """
        Raise LookupError if tar not detected
        """
        vcs_base.VCSClientBase.__init__(self, path)
        self.metadata_path = os.path.join(self._path, ".tar")
        with open(os.devnull, 'w') as fnull:
            try:
                subprocess.call("tar --help".split(), stdout=fnull, stderr=fnull)
            except:
                raise LookupError("tar not installed, cannnot create an tar vcs client")
 
    def get_url(self):
        """
        @return: TAR URL of the directory path (output of tar info command), or None if it cannot be determined
        """
        if self.detect_presence():
            with open(self.metadata_path, 'r') as metadata_file:
                metadata = yaml.load(metadata_file.read())
                if 'url' in metadata:
                    return metadata['url']
                
        return None

    def detect_presence(self):
        return self.path_exists() and os.path.exists(self.metadata_path)

    def __removed_exists(self, url):
        """
        @return: True if url exists in repo
        """
        cmd = ['tar', 'info', url]
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        return bool(output[0])

    def checkout(self, url, version=''):
        if self.path_exists():
            print >>sys.stderr, "Error: cannot checkout into existing directory"
            return False
        
        
        try:
            (filename, headers) = urllib.urlretrieve(url)
            #print "filename", filename
            tempdir = tempfile.mkdtemp()
            cmd = "tar -xf %s -C %s"%(filename, tempdir)
            #print "extract command", cmd
            if subprocess.call(cmd, shell=True) == 0:
                subdir = os.path.join(tempdir, version)
                if not os.path.isdir(subdir):
                    print >> sys.stderr, "%s is not a subdirectory"%subdir
                    return False
                #print "moving"
                try:
                    #os.makedirs(os.path.dirname(self._path))
                    shutil.move(subdir, self._path)
                #except shutil.Error, ex:
                except Exception, ex:
                    print "%s failed to move %s to %s"%(ex, subdir, self._path)
                #print "dumping yaml"
                metadata = yaml.dump({'url': url, 'version':version})
                #print metadata
                with open(self.metadata_path, 'w') as md:
                    md.write(metadata)

                return True
            else:
                print "failed to extract"
                os.shutil.rmtree(filename)
                return False
        except:
            print >>sys.stderr, "Tarball download unpack failed"
            return False
        return False

    def update(self, version=''):
        if not self.detect_presence():
            return False

        if version != self.get_version():
            print >> sys.stderr, "Tarball Client does not support updating with different version."
            return False

        return True

        
    def get_vcs_type_name(self):
        return 'tar'


    def get_version(self):
        if self.detect_presence():
            with open(self.metadata_path, 'r') as metadata_file:
                metadata = yaml.load(metadata_file.read())
                if 'version' in metadata:
                    return metadata['version']
                
        return None



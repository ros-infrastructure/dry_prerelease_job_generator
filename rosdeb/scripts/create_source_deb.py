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

"""
Create source debs from tarballs stored in the release repo
"""

import roslib; roslib.load_manifest('rosdeb')

import os
import sys
import subprocess
import shutil
import tempfile

import rosdeb
from rosdeb.rosutil import checkout_svn_to_tmp

NAME = 'create_source_deb.py' 
TARBALL_URL = "https://code.ros.org/svn/release/download/stacks/%(stack_name)s/%(base_name)s/%(f_name)s"
SERVER = 'http://build.willowgarage.com/'

def download_tarball(stack_name, stack_version, staging_dir):
    import urllib
    base_name = "%s-%s"%(stack_name, stack_version)
    for ext in ['tar.bz2', 'yaml']:
        f_name = "%s-%s.%s"%(stack_name, stack_version, ext)
        dest = os.path.join(staging_dir, f_name)
        url = TARBALL_URL%locals()
        urllib.urlretrieve(url, dest)

def copy_tarball_to_dir(tarball_file, staging_dir, stack_name, stack_version):
    raise Exception("not implemented")

    old_dir = os.path.abspath(os.path.dirname(tarball_file))
    new_dir = os.path.abspath(staging_dir)

    if not tarball_file.endswith('.tar.bz2'):
        raise Exception("tarball must be .tar.bz2")
    
    f_name = "%s-%s.tar.bz2"%(stack_name, stack_version)
    dest = os.path.join(staging_dir, f_name)
    if old_dir == new_dir:
        if os.path.basename(tarball_file) != f_name:
            # rename
            print "renaming\n  %s\n\t=>\n  %s"%(tarball_file, dest)
            os.rename(tarball_file, dest)
    else:
        import shutil
        print "copying\n  %s\n\t=>\n  %s"%(tarball_file, dest)
        shutil.copyfile(tarball_file, dest)
    
def upload_files(files, stack_name, stack_version):
    base_name = "%s-%s"%(stack_name, stack_version)
    f_name = '' #set f_name to None to get directory
    tmp_dir = checkout_svn_to_tmp(base_name, TARBALL_URL%locals())
    subdir = os.path.join(tmp_dir, base_name)
    try:
        # copy files to subdir
        names = [os.path.basename(f) for f in files]
        for f, base in zip(files, names):
            to_path = os.path.join(subdir, base)
            print "copying %s to %s"%(f, to_path)
            assert os.path.exists(f)
            shutil.copyfile(f, to_path)

            # svn add file
            subprocess.check_call(['svn', 'add', base], cwd=subdir)
        # commit the new files
        subprocess.check_call(['svn', 'ci', '-m', "source deb assets for %s-%s"%(stack_name, stack_version)]+names, cwd=subdir)

    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
    
def _source_deb_main(distro_name, stack_name, stack_version, os_platform, staging_dir):
    if os_platform not in rosdeb.platforms():
        print >> sys.stderr, "[%s] is not a known platform.\nSupported platforms are: %s"%(os_platform, ' '.join(rosdeb.platforms()))
        sys.exit(1)
    
    if not os.path.exists(staging_dir):
        print "creating staging dir: %s"%(staging_dir)
        os.makedirs(staging_dir)

    download_tarball(stack_name, stack_version, staging_dir)

    # CREATE THE SOURCE DEB
    files = rosdeb.make_source_deb(distro_name, stack_name, stack_version, os_platform, staging_dir)

    upload_files(files, stack_name, stack_version)

    
def trigger_hudson_build_debs(name, distro_name, os_platform):
    import hudson
    h = hudson.Hudson(SERVER)
    parameters = {
        'DISTRO_NAME': distro_name,
        'STACK_NAME': name,
        'OS_PLATFORM': os_platform,
        }
    for arch in ['i386', 'amd64']:
        parameters['ARCH'] = arch
        h.build_job('debbuild-sourcedeb', parameters=parameters, token='RELEASE_SOURCE_DEB')

EMAIL_FROM_ADDR = 'ROS debian build system <noreply@willowgarage.com>'
def send_mail(smtp_server, from_addr, to_addrs, subject, text):
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(text)

    msg['From'] = from_addr
    msg['To'] = to_addrs
    msg['Subject'] = subject

    s = smtplib.SMTP(smtp_server)
    print 'Sending mail to %s'%(to_addrs)
    s.sendmail(msg['From'], [msg['To']], msg.as_string())
    s.quit()

def source_deb_main():

    # COLLECT ARGS
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog <distro> <stack> <version> <os-platform>", prog=NAME)
    # disabling for now, will be worth implementing soon enough
    #parser.add_option("-f", "--file",
    #                  dest="file", default=None,
    #                  help="use local .tar.bz2 instead of downloading", metavar="TARBALL")
    parser.add_option("-d", "--dir",
                      dest="staging_dir", default=None,
                      help="directory to use for staging source debs", metavar="STAGING_DIR")
    parser.add_option("--hudson",
                      dest="hudson", action='store_true', default=False,
                      help="execute Hudson-style, which builds all platforms")
    parser.add_option("--smtp",
                      dest="smtp", default=None,
                      help="SMTP server to use for failure emails")

    (options, args) = parser.parse_args()

    if len(args) < 3:
        parser.error('invalid args')
        
    distro_name    = args[0]
    stack_name     = args[1]
    stack_version  = args[2]

    if options.hudson:

        if len(args) != 3:
            parser.error('please specify distro name, stack name, and stack version')
        if options.staging_dir:
            parser.error("cannot override directory in Hudson mode")

        errors = []
        success = []

        for os_platform in ['lucid', 'karmic', 'jaunty']:
            staging_dir = os.path.join(tempfile.gettempdir(), "rosdeb-%s"%(os_platform))
            if os.path.exists(staging_dir):
                shutil.rmtree(staging_dir)
            os.mkdir(staging_dir)
            try:
                _source_deb_main(distro_name, stack_name, stack_version, os_platform, staging_dir)
                success.append(os_platform)
            except Exception, e:
                errors.append((os_platform, e))
                
        for os_platform in success:
            print "triggering build-debs for %s, %s, %s"%(stack_name, distro_name, os_platform)
            trigger_hudson_build_debs(stack_name, distro_name, os_platform)

        # Handle build failures:
        #  - print out failed OS platforms
        #  - send failure e-mail
        if errors:

            # create and print error message
            error_msgs = '='*80 + '\nERRORS\n' + '='*80 + '\n'
            
            error_msgs += 'Stack [%s-%s] in distro [%s] failed to build on the following OS platforms:\n%s\n\n'%(stack_name, stack_version, distro_name, [x for x, y in errors])
            
            for os_platform, e in errors:
                error_msgs += '[%s]: %s\n'%(os_platform, str(e))
                
            error_msgs += '='*80 + '\n'
            
            print >> sys.stderr, error_msgs

            # load the control data
            import yaml
            control_file = os.path.join(staging_dir, "%s-%s.yaml"%(stack_name, stack_version))
            with open(control_file) as f:
                control = yaml.load(f)

            # Send e-mail for failed platforms if smtp server name is provided
            if options.smtp and 'contact' in control:
                to_addr = control_file['contact']
                email_msg = error_msgs
                if successes:
                    email_msg = 'Stack [%s-%s] in distro [%s] successed on the following OS platforms:\n%s\n\n'%(stack_name, stack_version, distro_name, successes) + email_msg
                subject = 'debian build [%s-%s] failed'%(stack_name, stack_version)
                send_email(options.smtp, EMAIL_FROM_ADDR, to_addr, subject, email_msg)

            # Exit with error code to signal build failure
            sys.exit(2)
            
    else:
        if len(args) != 4:
            parser.error('please specify distro name, stack name, stack version, and platform (e.g. lucid)')
        os_platform    = args[3]
        staging_dir = options.staging_dir or os.getcwd()
        _source_deb_main(distro_name, stack_name, stack_version, os_platform, staging_dir)
        
if __name__ == '__main__':
    source_deb_main()


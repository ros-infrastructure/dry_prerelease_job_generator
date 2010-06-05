#! /usr/bin/env python

"""
usage: %prog ubuntu_release arch path distro_name distro_uri

apt-get install debootstrap

"""

import os, sys, string, time
import subprocess
import yaml

from optparse import OptionParser

import urllib2

def build(distro, arch, path, ros_distro_uri):

  release_file = False

  try:
    if os.path.isfile(ros_distro_uri):
      with open(ros_distro_uri) as f:
        y = yaml.load(f.read())
        release_file = True
    else:
      y = yaml.load(urllib2.urlopen(ros_distro_uri))
    release_name = y['release']
  except Exception, e:
    print >> sys.stderr, "Could not open URI: %s"%ros_distro_uri
    sys.exit(1)

  subprocess.check_call(['rm', '-rf', path])
      
  try:

    os.makedirs(path, 0755)
    os.makedirs(os.path.join(path,'tmp'), 0755)

    checkrepo_path = os.path.join(path,'tmp/checkrepo.py')
    roslib_path = os.path.join(path,'tmp/roslib')
 
    ret = subprocess.call(['rosrun', 'rosdeb', 'checkrepo.py', ros_distro_uri, 'http://code.ros.org/packages/ros/ubuntu/dists/%s/main/binary-%s/Packages'%(distro,arch)])
    if ret == 0:
      print "Release already up to date"
      sys.exit(0)
  
    cmd = ['sudo', 'debootstrap', '--arch', arch, distro, path, 'http://aptproxy.willowgarage.com/archive.ubuntu.com/ubuntu/']
    print cmd
    subprocess.check_call(cmd)
  
    subprocess.check_call(['sudo', 'cp', '/etc/resolv.conf', os.path.join(path, 'etc')])
    subprocess.check_call(['sudo', 'cp', '/etc/hosts', os.path.join(path, 'etc')])

    # Move sources.list to apt-proxy
    sources=os.path.join(path, 'etc', 'apt', 'sources.list')
    subprocess.check_call(['sudo', 'chown', '%d'%os.getuid(), sources])
    f = open(sources, "a+")
    f.write("deb http://aptproxy/archive.ubuntu.com/ubuntu %s main restricted universe multiverse\n" % distro)
    f.close()

    #disable start-stop-daemon
    startstop=os.path.join(path,'sbin/start-stop-daemon')
    subprocess.check_call(['sudo', 'chown', '%d'%os.getuid(), startstop])
    f = open(startstop,'w')
    f.write("#!/bin/sh\n")
    f.write("exit 0\n")
    f.close()

    #disable start-stop-daemon
    invokerc=os.path.join(path,'usr/sbin/invoke-rc.d')
    subprocess.check_call(['sudo', 'chown', '%d'%os.getuid(), invokerc])
    f = open(invokerc,'w')
    f.write("#!/bin/sh\n")
    f.write("exit 0\n")
    f.close()

    chrootcmd = ['sudo', 'chroot', path]

    try:
      subprocess.check_call(chrootcmd + ['mount', '-t', 'proc', 'proc', '/proc'])
      subprocess.check_call(chrootcmd + ['mount', '-t', 'sysfs', 'sysfs', '/sys'])

      subprocess.check_call(chrootcmd + ['locale-gen', 'en_US.UTF-8'])

      subprocess.check_call(chrootcmd + ['apt-get', 'update'])

      subprocess.check_call(chrootcmd + ['apt-get', '-y', '--force-yes', 'install', 'build-essential', 'python-yaml', 'cmake', 'subversion', 'wget', 'lsb-release', 'fakeroot', 'sudo', 'debhelper', 'cdbs', 'ca-certificates', 'debconf-utils'])


      # Fix the sudoers file
      sudoers_path = os.path.join(path, 'etc/sudoers')
      subprocess.check_call(['sudo', 'chown', '0.0', sudoers_path])

      subprocess.Popen(chrootcmd + ['debconf-set-selections'], stdin=subprocess.PIPE).communicate("""
hddtemp hddtemp/port string 7634
hddtemp hddtemp/interface string 127.0.0.1
hddtemp hddtemp/daemon boolean false
hddtemp hddtemp/syslog string 0
hddtemp hddtemp/SUID_bit boolean false
sun-java6-bin shared/accepted-sun-dlj-v1-1 boolean true
sun-java6-jdk shared/accepted-sun-dlj-v1-1 boolean true
sun-java6-jre shared/accepted-sun-dlj-v1-1 boolean true
""");

      subprocess.check_call(chrootcmd + ['wget', '--no-check-certificate', 'http://ros.org/rosinstall', '-O', '/tmp/rosinstall'])
      subprocess.check_call(chrootcmd + ['chmod', '755', '/tmp/rosinstall'])
      subprocess.check_call(chrootcmd + ['/tmp/rosinstall', '--rosdep-yes', '/tmp/ros-release', 'http://www.ros.org/rosinstalls/ros-release.rosinstall'])

      if release_file:
        subprocess.check_call(['sudo', 'cp', ros_distro_uri, os.path.join(path, 'tmp')])
        ros_distro_uri = os.path.join('/tmp', os.path.split(ros_distro_uri)[-1])

      ros_path='/opt/ros/'+release_name

      if arch in ['i386','i686']:
        setarch = ['setarch', arch]
      else:
        setarch = []

      bash = ['bash', '-c']
      setupandrun = "source /tmp/ros-release/setup.sh; export JAVA_HOME=/usr/lib/jvm/java-6-sun/; rosrun rosdeb build_release "

      subprocess.check_call(chrootcmd + setarch + bash + [setupandrun + "checkout %s -r -w %s"%(ros_distro_uri, ros_path)])
      subprocess.check_call(chrootcmd + setarch + bash + [setupandrun + "rosdep -w %s -y"%ros_path])
      subprocess.check_call(chrootcmd + setarch + bash + [setupandrun + "build -w %s"%ros_path])
      subprocess.check_call(chrootcmd + setarch + bash + [setupandrun + "package %s -w %s"%(ros_distro_uri, ros_path)])

    finally:
      subprocess.check_call(chrootcmd + ['umount', '-a'])
      subprocess.check_call(chrootcmd + ['umount', '/proc'])
      subprocess.check_call(chrootcmd + ['umount', '/sys'])
  finally:
    subprocess.check_call(['sudo', 'chown', '-R', '%d'%os.getuid(), path])

def push(distro, arch, path, ros_distro_uri):

#    landing_path_base="/var/packages/incoming/dists-"+time.strftime("%Y%m%d")
#    landing_path=landing_path_base+'/'+distro+'/released/binary-'+arch
#    subprocess.check_call(['ssh', '-p', '2222', 'rosbuild@pub5', 'mkdir -p '+landing_path])
#    subprocess.check_call(['ssh', '-p', '2222', 'rosbuild@pub5', '/home/rosbuild/build_repository.py %s %s'%(landing_path_base, distro)])

  landing_path = os.path.join("/var/packages/ros/ubuntu/queue",distro)

  # Clear stale packages in the incoming queue
  subprocess.check_call(['ssh', '-p', '22', 'rosbuild@pub5', 'rm -f %s/*.deb'%landing_path])
  subprocess.check_call(['ssh', '-p', '22', 'rosbuild@pub5', 'rm -f %s/*.changes'%landing_path])

  # Upload .changes and .debs
  subprocess.check_call(['sh', '-c', 'scp -P 22 '+path+'/packager-workspace/*.changes rosbuild@pub5:'+landing_path])
  subprocess.check_call(['sh', '-c', 'scp -P 22 '+path+'/packager-workspace/*.deb rosbuild@pub5:'+landing_path])

  # Pull new files into the repo
  subprocess.check_call(['ssh', '-p', '22', 'rosbuild@pub5', 'reprepro -V -b /var/packages/ros/ubuntu --keepunreferencedfiles processincoming %s'%distro])



def main(argv, stdout, environ):
  parser = OptionParser(usage=__doc__)
  parser.add_option("--push", action="store_true", dest="push", help="Push to server")
  parser.add_option("--push-only", action="store_true", dest="push_only", help="Push an already built tree")
  (options, args) = parser.parse_args()

  if len(args) != 4:
    parser.error("Need 4 arguments: distro, arch, path, ros_distro_uri")

  distro = args[0]
  arch = args[1]
  path = args[2]
  ros_distro_uri = args[3]

  subprocess.check_call(['sudo', 'apt-get', 'install', '-y', '--force-yes', 'debootstrap'])

  if not options.push_only:
    build(distro, arch, path, ros_distro_uri)

  if options.push or options.push_only:
    push(distro, arch, path, ros_distro_uri)


if __name__ == "__main__":
  main(sys.argv, sys.stdout, os.environ)

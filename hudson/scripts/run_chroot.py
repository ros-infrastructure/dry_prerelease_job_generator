#!/usr/bin/env python

import subprocess
import os, sys
import time
import shutil
import tempfile
import optparse
import traceback
import urllib

ROSBUILD_SSH_URI = 'https://home.willowgarage.com/wgwiki/Servers/hudson?action=AttachFile&do=get&target=rosbuild-ssh.tar'

def execute_chroot(cmd, path, user='root'):
    if user == 'root':
        full_cmd = ["sudo", "chroot", path]
        full_cmd.extend(cmd)
    else:
        full_cmd = ['sudo', 'chroot', path, 'su', user, '-c', '%s'%" ".join(cmd)]
    print "Executing", full_cmd
    subprocess.check_call(full_cmd)
    



class ChrootInstance:
    def __init__(self, distro, arch, path, host_workspace, clear_chroot = True):
        #logging
        self.profile = []
        self.chroot_path = path
        self.host_workspace = host_workspace
        self.mount_path = "/tmp/ros"
        self.ccache_dir = "/tmp/ccache"
        self.host_ccache_dir = "~/.ccache"
        self.ccache_remote_dir = os.path.join(self.chroot_path, self.ccache_dir[1:])
        self.ws_remote_path = os.path.join(self.chroot_path, self.mount_path[1:])
        self.failure = False
        self.arch = arch
        self.distro = distro
        self.clear_chroot = clear_chroot
        self.workspace_successfully_copied = False


    def clean(self):
        self.unmount_proc_sys()

        # clear chroot if it exists
        print "Removing tree %s"%self.chroot_path
        #shutil.rmtree(self.chroot_path, True)
        cmd = ["sudo", "rm", "-rf", self.chroot_path]
        print "executing", cmd
        subprocess.check_call(cmd)

    def unmount_proc_sys(self):
        self.execute(['umount', '-f', '/proc'], True)
        self.execute(['umount', '-f', '/sys'], True)
        #self.execute(['umount', '-af'], True)

    def mount_proc_sys(self):
        #hack since we mount it in 2 places and umount is safe
        self.unmount_proc_sys()

        self.execute(['mount', '-t', 'proc', 'proc', '/proc'])
        self.execute(['mount', '-t', 'sysfs', 'sysfs', '/sys'])

    def bootstrap(self):
        cmd = ['sudo', 'apt-get', 'install', 'debootstrap']
        print cmd
        subprocess.check_call(cmd)
        
        cmd = ['sudo', 'debootstrap', '--arch', self.arch, self.distro, self.chroot_path, 'http://aptproxy.willowgarage.com/us.archive.ubuntu.com/ubuntu/']
        print cmd
        subprocess.check_call(cmd)
        print "Finished debootstrap"


        # replicate host settings
        cmd = ['sudo', 'cp', '/etc/resolv.conf', os.path.join(self.chroot_path, 'etc')]
        print "Runing cmd", cmd
        subprocess.check_call(cmd)
        cmd = ['sudo', 'cp', '/etc/hosts', os.path.join(self.chroot_path, 'etc')]
        print "Runing cmd", cmd
        subprocess.check_call(cmd)

        # Move sources.list to apt-proxy
        sources=os.path.join(self.chroot_path, 'etc', 'apt', 'sources.list.d', 'aptproxy.list')

        with tempfile.NamedTemporaryFile() as tf:
            print "Setting sources to aptproxy.willowgarage.com", sources
            tf.write("deb http://aptproxy.willowgarage.com/us.archive.ubuntu.com/ubuntu %s main restricted universe multiverse\n" % self.distro)
            tf.write("deb http://aptproxy.willowgarage.com/us.archive.ubuntu.com/ubuntu %s-updates main restricted universe multiverse\n" % self.distro)
            tf.write("deb http://aptproxy.willowgarage.com/us.archive.ubuntu.com/ubuntu %s-security main restricted universe multiverse\n" % self.distro)
            # This extra source is to pull in the very latest
            # nvidia-current package from our mirror.  It's only guaranteed
            # to be available for Lucid, but we only need it for Lucid.
            if self.distro == 'lucid':
                tf.write("deb http://wgs1.willowgarage.com/wg-packages/ %s-wg main\n" % self.distro)

            tf.flush()
            cmd = ['sudo', 'cp', tf.name, sources]
            print "Runing cmd", cmd
            subprocess.check_call(cmd)

        if self.distro == 'lucid':
            self.execute("sudo apt-get update".split())
            self.execute("sudo apt-get install wget".split())
            self.execute("wget http://wgs1.willowgarage.com/wg-packages/wg.key".split())
            self.execute("sudo apt-key add wg.key".split())
            self.execute("sudo apt-get update".split())

        #disable start-stop-daemon and invokerc

        with tempfile.NamedTemporaryFile() as tf:
            tf.write("#!/bin/sh\n")
            tf.write("exit 0\n")
            tf.flush()
            
            startstop=os.path.join(self.chroot_path,'sbin/start-stop-daemon')
            print "disabling start-stop", startstop
            subprocess.check_call(['sudo', 'cp', tf.name, startstop])
            
            invokerc=os.path.join(self.chroot_path,'usr/sbin/invoke-rc.d')
            print "disabling start-stop", invokerc
            subprocess.check_call(['sudo', 'cp', tf.name, invokerc])


        self.mount_proc_sys()

        self.execute(['locale-gen', 'en_US.UTF-8'])

        self.execute(['apt-get', 'update'])

          #subprocess.check_call(chrootcmd + ['apt-get', '-y', '--force-yes', 'install', 'build-essential', 'python-yaml', 'cmake', 'subversion', 'wget', 'lsb-release', 'fakeroot', 'sudo', 'debhelper', 'cdbs', 'ca-certificates', 'debconf-utils'])


          # Fix the sudoers file
        sudoers_path = os.path.join(self.chroot_path, 'etc/sudoers')
        subprocess.check_call(['sudo', 'chown', '0.0', sudoers_path])

        print "debconf executing"
        chrootcmd = ['sudo', 'chroot', self.chroot_path]
        subprocess.Popen(chrootcmd + ['debconf-set-selections'], stdin=subprocess.PIPE).communicate("""
  hddtemp hddtemp/port string 7634
  hddtemp hddtemp/interface string 127.0.0.1
  hddtemp hddtemp/daemon boolean false
  hddtemp hddtemp/syslog string 0
  hddtemp hddtemp/SUID_bit boolean false
  sun-java6-bin shared/accepted-sun-dlj-v1-1 boolean true
  sun-java6-jdk shared/accepted-sun-dlj-v1-1 boolean true
  sun-java6-jre shared/accepted-sun-dlj-v1-1 boolean true
  grub-pc grub2/linux_cmdline string
  grub-pc grub-pc/install_devices_empty boolean true
  """);
        print "debconf complete"


        # If we're on lucid, pull in the nvidia drivers, in case we're
        # going to run Gazebo-based tests, which need the GPU.
        if self.distro == 'lucid':
            # The --force-yes is necessary to accept the nvidia-current
            # package without a valid GPG signature.
            self.execute(['apt-get', 'install', '-y', '--force-yes', 'nvidia-current'])
            self.execute(['mknod', '/dev/nvidia0', 'c', '195', '0'])
            self.execute(['mknod', '/dev/nvidiactl', 'c', '195', '255'])
            self.execute(['chmod', '666', '/dev/nvidia0', '/dev/nvidiactl'])

        cmd = ("sudo tee -a %s"%sudoers_path).split()
        print "making rosbuild have no passwd", cmd
        tempf = tempfile.TemporaryFile()
        tempf.write("rosbuild ALL = NOPASSWD: ALL\n")
        tempf.seek(0)
        subprocess.check_call(cmd, stdin = tempf)


        #fix sudo permissions
        self.execute(['chown', '-R', 'root:root', '/usr/bin/sudo'])
        self.execute(['chmod', '4755', '-R', '/usr/bin/sudo'])


        cmd = "useradd rosbuild -m --groups sudo".split()
        print self.execute(cmd)

        self.setup_ssh_client()

    def setup_ssh_client(self):
        print 'Setting up ssh client'
        # Pull in ssh, and drop a private key that will allow the slave to
        # upload results of the build.
        self.execute(['apt-get', 'install', '-y', '--force-yes', 'openssh-client'])
        # Pull down a tarball of rosbuild's .ssh directory
        tardestdir = os.path.join(self.chroot_path, 'home', 'rosbuild',)
        #tardestname = os.path.join(tardestdir, 'rosbuild-ssh.tar')
        #if not os.path.exists(tardestname):
        local_tmp_dir = tempfile.mkdtemp()
        local_tmp = os.path.join(local_tmp_dir, "rosbuild_ssh.tar.gz")
        urllib.urlretrieve(ROSBUILD_SSH_URI, local_tmp)
            
        if not os.path.exists(tardestdir):
            os.makedirs(tardestdir)
        subprocess.check_call(['sudo', 'tar', 'xf', local_tmp], cwd=tardestdir)
        #subprocess.check_call(['sudo', 'rm', '-rf', local_tmp_dir])
        shutil.rmtree(local_tmp_dir)

        #self.execute(['tar', 'xf', os.path.join('home', 'rosbuild', 'rosbuild-ssh.tar')], cwd=os.path.join('home', 'rosbuild'))
        self.execute(['chown', '-R', 'rosbuild:rosbuild', '/home/rosbuild'])

    def replecate_workspace(self):
        print "replecating host workspace"
        # setup workspace
        print "clearing destination"
        subprocess.check_call(["sudo", "rm", "-rf", self.ws_remote_path]);

        print "Copying ", self.host_workspace, self.ws_remote_path
        subprocess.check_call(["sudo", "cp", "-a", self.host_workspace, self.ws_remote_path]);
        self.execute(['chown', '-R', 'rosbuild:rosbuild', self.mount_path])
        self.workspace_successfully_copied = True
        print "Done replecating workspace"

    def write_back_workspace(self):
        print "Writing back resultant workspace"
        if not self.workspace_successfully_copied:
            print "skipping copy back due to no successful initial copy"
            return
        subprocess.check_call(['sudo', 'chown', '-R', '%d'%os.getuid(), self.ws_remote_path])
        subprocess.check_call(["sudo", 'rm', "-rf", self.host_workspace]);
        subprocess.check_call(["cp", "-a", self.ws_remote_path, self.host_workspace]);
        print "done writing back"


    def manual_init(self):
        

        print "Starting"
        if self.clear_chroot and os.path.isdir(self.chroot_path):
            print"Cleaning first" 
            self.clean()
            self.bootstrap()
        elif not os.path.isdir(self.chroot_path):
            self.bootstrap() # bootstrap if cleaned or uninitialized
        else:
            self.execute(['dpkg', '--configure', '-a']) # clean up in case dpkg was previously interrupted

        # Even if we're reusing the chroot, we re-mount /proc and /sys.
        self.mount_proc_sys()

        # We setup ~rosbuild/.ssh every time.  It
        # should only be done during the bootstrap step, but it was added
        # after a great many chroot were already bootstrapped, are being 
        # reused.  Also, the server key sometimes changes and so the
        # contents of ~rosbuild/.ssh need to be updated.
        self.setup_ssh_client()

        self.replecate_workspace()

        
#        if not os.path.isdir(self.host_ccache_dir):
#            os.makedirs(self.host_ccache_dir)
#        if not os.path.isdir(self.ccache_remote_dir):
#            os.makedirs(self.ccache_remote_dir)
#        print "Mounting", self.host_ccache_dir, self.ccache_remote_dir
#        subprocess.check_call(['sudo', 'mount', '--bind', self.host_ccache_dir, self.ccache_remote_dir])


    

    def __enter__(self):
        return self
    def __exit__(self, mtype, value, tb):
        if tb:
            print "Caught exception shutting down"
            traceback.print_exception(mtype, value, tb, file=sys.stdout)
            
        self.shutdown()

    def print_profile(self):
        print "chroot Profile:"
        total_time = 0
        for line in self.profile:
            print " %.1f: %s"%(line[0], line[1])
            total_time += line[0]
        print "Total Time: %f"%(total_time)



    def shutdown(self):
        print "Shutting down"
        self.unmount_proc_sys()
        self.write_back_workspace()

    def execute(self, cmd, robust = False, user='root'):
        start_time = time.time()
        if robust:
            try:
                execute_chroot(cmd, self.chroot_path, user)
            except subprocess.CalledProcessError, ex:
                pass
        else:
            execute_chroot(cmd, self.chroot_path, user)
        net_time = time.time() - start_time
        self.profile.append((net_time, "executed: %s"%cmd))

def run_chroot(options, path, workspace):
    with ChrootInstance(options.distro, options.arch, path, workspace, clear_chroot = not options.persist) as chrti:

        chrti.manual_init()

        cmd = "apt-get update".split()
        chrti.execute(cmd)

        cmd = "apt-get install -y --force-yes build-essential python-yaml cmake subversion wget python-setuptools".split()
        chrti.execute(cmd)

        if options.script:
            remote_script_name = os.path.join(chrti.mount_path, os.path.basename(options.script))
            cmd = ["sudo", "cp", options.script, chrti.ws_remote_path]
            print "Executing", cmd
            subprocess.check_call(cmd);
            cmd = ("chown rosbuild:rosbuild %s"%remote_script_name).split()
            chrti.execute(cmd)
            cmd = ("chmod +x %s"%remote_script_name).split()
            chrti.execute(cmd)
            cmd = [remote_script_name]
            chrti.execute(cmd, user="rosbuild")
            
        else:
            cmd = ("wget http://code.ros.org/svn/ros/installers/trunk/hudson/hudson_helper --no-check-certificate -O %s/hudson_helper"%(chrti.mount_path)).split()
            chrti.execute(cmd, user='rosbuild')


            cmd = ("chmod +x %s/hudson_helper"%chrti.mount_path).split()
            chrti.execute(cmd, user='rosbuild')


            cmd = ("chown rosbuild:rosbuild %s"%chrti.mount_path).split() # if 
            print chrti.execute(cmd)

            #cmd = ["su", "rosbuild", "-c", "export JOB_NAME=ros-boxturtle-amazon && export BUILD_NUMBER=1 && export HUDSON_URL=http://build.willowgarage.com && export WORKSPACE=/tmp/ros && cd %s && %s/hudson_helper --dir-test ros build"%(chrti.mount_path, chrti.mount_path)]
            if options.arch in ['i386', 'i686']:
              setarch = 'setarch %s'%(options.arch)
            else:
              setarch = ''

            cmd = ["bash", "-c", "export PATH=/usr/lib/ccache:$PATH && export CCACHE_DIR=%s &&export JOB_NAME=%s && export BUILD_NUMBER=%s && export HUDSON_URL=%s && export WORKSPACE=/tmp/ros && cd %s && %s %s/hudson_helper %s"%(chrti.ccache_dir, os.getenv('JOB_NAME'), os.getenv('BUILD_NUMBER'), os.getenv('HUDSON_URL'), chrti.mount_path, setarch, chrti.mount_path, options.hudson_args)]
            chrti.execute(cmd, user='rosbuild')

        print chrti.print_profile()


        
class TempRamFS:
    def __init__(self, path, size_str):
        self.path = path
        self.size= size_str
        
    def __enter__(self):
        
        cmd = ['sudo', 'mkdir', '-p', self.path]
        subprocess.check_call(cmd)
        cmd = ['sudo', 'mount', '-t', 'tmpfs', '-o', 'size=%s,mode=0755'%self.size, 'tmpfs', self.path]
        subprocess.check_call(cmd)
        return self

    def __exit__(self, mtype, value, tb):
        if tb:
            print "Caught exception, closing out ramdisk"
            traceback.print_exception(mtype, value, tb, file=sys.stdout)
            
        cmd = ['sudo', 'umount', '-f', self.path]
        subprocess.check_call(cmd)



# Valid options
valid_archs = ['i386', 'i686', 'amd64']
valid_distros = ['hardy', 'jaunty', 'karmic', 'lucid']


workspace = os.getenv("WORKSPACE")
if not workspace:
    print "you must export WORKSPACE"
    sys.exit(1)





parser = optparse.OptionParser()
parser.add_option("--hudson", type="string", dest="hudson_args", 
                  help="args to pass through to hudson_helper") 
parser.add_option("--arch", type="string", dest="arch",
                  help="What architecture %s"%valid_archs)
parser.add_option("--distro", type="string", dest="distro",
                  help="What distro %s "%valid_distros)
parser.add_option("--persist-chroot", action="store_true", dest="persist", default=False,
                  help="do not clear the chroot before running")
parser.add_option("--chroot-dir", action="store", dest="chroot_dir", default="/home/rosbuild/chroot",
                  type="string", help="prefix for ros_release")
parser.add_option("--ramdisk-size", action="store", dest="ramdisk_size", default="15000M",
                  type="string", help="Ramdisk size string, default '15000M'")
parser.add_option("--ramdisk", action="store_true", dest="ramdisk", default=False,
                  help="Run chroot in a ramdisk")
parser.add_option("--script", action="store", dest="script",
                  type="string", help="Script filename to execute on the remote machine")

(options, args) = parser.parse_args()

if not options.script and not options.hudson_args:
    parser.error("hudson_helper needs args")
if options.distro not in valid_distros:
    parser.error("%s is not a valid distro: %s"%(options.distro, valid_distros))
if options.arch not in valid_archs:
    parser.error("%s is not a valid arch: %s"%(options.arch, valid_archs))


path = os.path.join(options.chroot_dir, os.getenv("JOB_NAME"))
print "chroot path", path    
print "parameters"
print "hudson_args", options.hudson_args
print "distro", options.distro
print "arch", options.arch
print "workspace", workspace

if options.ramdisk:
    with TempRamFS(options.chroot_dir, options.ramdisk_size):
        cmd = ['mount']
        subprocess.check_call(cmd)
        run_chroot(options, path, workspace)

    cmd = ['mount']
    subprocess.check_call(cmd)

else:
    run_chroot(options, path, workspace)


sys.exit(0)
#!/usr/bin/python

import roslib; roslib.load_manifest("job_generation")
from rosdeb import targets
import os
import optparse
import rosdistro
import hudson
import urllib
import time
import subprocess
import yaml

BOOTSTRAP_SCRIPT = """
cat &gt; $WORKSPACE/script.sh &lt;&lt;DELIM
#!/usr/bin/env bash
set -o errexit
echo "_________________________________BEGIN SCRIPT______________________________________"
sudo apt-get install bzr --yes
sudo apt-get install ros-ROSDISTRO-ros --yes
source /opt/ros/ROSDISTRO/setup.sh

export INSTALL_DIR=/tmp/install_dir
export WORKSPACE=/tmp/ros
export ROS_TEST_RESULTS_DIR=/tmp/ros/test_results
export JOB_NAME=$JOB_NAME
export BUILD_NUMBER=$BUILD_NUMBER
export HUDSON_URL=$HUDSON_URL
export ROS_PACKAGE_PATH=\$INSTALL_DIR/ros_release:/opt/ros/ROSDISTRO/stacks

mkdir -p \$INSTALL_DIR
cd \$INSTALL_DIR

wget  --no-check-certificate http://code.ros.org/svn/ros/installers/trunk/hudson/hudson_helper 
chmod +x hudson_helper
svn co https://code.ros.org/svn/ros/stacks/ros_release/trunk ros_release
"""

SHUTDOWN_SCRIPT = """
echo "_________________________________END SCRIPT_______________________________________"
DELIM

set -o errexit

rm -rf $WORKSPACE/test_results
rm -rf $WORKSPACE/test_output

wget  --no-check-certificate https://code.ros.org/svn/ros/stacks/ros_release/trunk/hudson/scripts/run_chroot.py -O $WORKSPACE/run_chroot.py
chmod +x $WORKSPACE/run_chroot.py
cd $WORKSPACE &amp;&amp; $WORKSPACE/run_chroot.py --distro=UBUNTUDISTRO --arch=ARCH  --ramdisk --hdd-scratch=/home/rosbuild/install_dir --script=$WORKSPACE/script.sh --ssh-key-file=/home/rosbuild/rosbuild-ssh.tar
"""


# the supported Ubuntu distro's for each ros distro
ARCHES = ['amd64', 'i386']

# ubuntu distro mapping to ros distro
UBUNTU_DISTRO_MAP = targets.os_platform

# Path to hudson server
SERVER = 'http://build.willowgarage.com'

# config path
CONFIG_PATH = 'http://wgs24.willowgarage.com/hudson-html/hds.xml'


EMAIL_TRIGGER="""
        <hudson.plugins.emailext.plugins.trigger.WHENTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>SEND_DEVEL</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.WHENTrigger> 
"""


hudson_scm_managers = {'svn':"""
  <scm class="hudson.scm.SubversionSCM"> 
    <locations> 
      <hudson.scm.SubversionSCM_-ModuleLocation> 
        <remote>STACKURI</remote> 
        <local>STACKNAME</local> 
      </hudson.scm.SubversionSCM_-ModuleLocation> 
    </locations> 
    <useUpdate>false</useUpdate> 
    <doRevert>false</doRevert> 
    <excludedRegions></excludedRegions> 
    <includedRegions></includedRegions> 
    <excludedUsers></excludedUsers> 
    <excludedRevprop></excludedRevprop> 
    <excludedCommitMessages></excludedCommitMessages> 
  </scm> 
""",
                       'hg':"""
  <scm class="hudson.plugins.mercurial.MercurialSCM">
    <source>STACKURI</source>
    <modules></modules>
    <subdir>STACKNAME</subdir>
    <clean>false</clean>
    <forest>false</forest>
    <branch>STACKBRANCH</branch>
  </scm>
""",
                       'git':"""

  <scm class="hudson.plugins.git.GitSCM">
    <configVersion>1</configVersion>
    <remoteRepositories>
      <org.spearce.jgit.transport.RemoteConfig>
        <string>origin</string>
        <int>5</int>

        <string>fetch</string>
        <string>+refs/heads/*:refs/remotes/origin/*</string>
        <string>receivepack</string>
        <string>git-upload-pack</string>
        <string>uploadpack</string>
        <string>git-upload-pack</string>

        <string>url</string>
        <string>STACKURI</string>
        <string>tagopt</string>
        <string></string>
      </org.spearce.jgit.transport.RemoteConfig>
    </remoteRepositories>
    <branches>

      <hudson.plugins.git.BranchSpec>
        <name>STACKBRANCH</name>
      </hudson.plugins.git.BranchSpec>
    </branches>
    <localBranch></localBranch>
    <mergeOptions/>
    <recursiveSubmodules>false</recursiveSubmodules>
    <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>

    <authorOrCommitter>Hudson</authorOrCommitter>
    <clean>false</clean>
    <wipeOutWorkspace>false</wipeOutWorkspace>
    <buildChooser class="hudson.plugins.git.util.DefaultBuildChooser"/>
    <gitTool>Default</gitTool>
    <submoduleCfg class="list"/>
    <relativeTargetDir>STACKNAME</relativeTargetDir>

    <excludedRegions></excludedRegions>
    <excludedUsers></excludedUsers>
  </scm>
"""
}

def stack_to_deb(stack, rosdistro):
    return '-'.join(['ros', rosdistro, str(stack).replace('_','-')])

def stacks_to_debs(stack_list, rosdistro):
    if not stack_list or len(stack_list) == 0:
        return ''
    return ' '.join([stack_to_deb(s, rosdistro) for s in stack_list])


def get_tar(stack):
    name = '%s-%s'%(stack.name, stack.version)
    return 'https://code.ros.org/svn/release/download/stacks/%s/%s/%s.tar.bz2'%(stack.name, name, name)


def stack_to_rosinstall(stack, branch):
    vcs = stack.vcs_config
    if not branch in ['devel', 'release', 'distro', 'release-tar']:
        print 'Unsupported branch type %s for stack %s'%(branch, stack.name)
        return ''

    if branch == 'release-tar':
        return "- tar: {uri: '%s', version: '%s-%s', local-name: '%s'}\n"%(get_tar(stack), stack.name, stack.version, stack.name)

    if not vcs.type in ['svn', 'hg', 'git', 'bzr']:
        print 'Unsupported vcs type %s for stack %s'%(vcs.type, stack.name)
        return ''
        
    if vcs.type in ['svn', 'bzr']:
        if branch == 'devel':
            return "- %s: {uri: '%s', local-name: '%s'}\n"%(vcs.type, vcs.anon_dev, stack.name)
        elif branch == 'distro':
            return "- %s: {uri: '%s', local-name: '%s'}\n"%(vcs.type, vcs.anon_distro_tag, stack.name)            

        elif branch == 'release':
            return "- %s: {uri: '%s', local-name: '%s'}\n"%(vcs.type, vcs.anon_release_tag, stack.name)  

    elif vcs.type in ['hg', 'git']:
        if branch == 'devel':
            return "- %s: {uri: '%s', version: '%s', local-name: '%s'}\n"%(vcs.type, vcs.anon_repo_uri, vcs.dev_branch, stack.name)
        elif branch == 'distro':
            return "- %s: {uri: '%s', version: '%s', local-name: '%s'}\n"%(vcs.type, vcs.anon_repo_uri, vcs.distro_tag, stack.name)
        elif branch == 'release':
            return "- %s: {uri: '%s', version: '%s', local-name: '%s'}\n"%(vcs.type, vcs.anon_repo_uri, vcs.release_tag, stack.name)



def stacks_to_rosinstall(stack_list, stack_map, branch):
    res = ''
    for s in stack_list:
        if s in stack_map:
            res += stack_to_rosinstall(stack_map[s], branch)
        else:
            print 'Stack "%s" is not in stack list. Not adding this stack to rosinstall file'%s
    return res

    

def get_depends_one(stack):
    name = '%s-%s'%(stack.name, stack.version)
    url = urllib.urlopen('https://code.ros.org/svn/release/download/stacks/%s/%s/%s.yaml'%(stack.name, name, name))
    conf = url.read()
    if '404 Not Found' in conf:
        print 'Could not get dependencies of stack %s'%stack.name
        return []
    depends = yaml.load(conf)['depends']
    if depends:
        return depends
    else:
        print 'Stack %s does not have any dependencies'%stack.name
        return []

def get_depends_all(distro_obj, stack_name, depends_all):
    if not stack_name in depends_all:
        depends_all.append(stack_name)
        for d in get_depends_one(distro_obj.stacks[stack_name]):
            get_depends_all(distro_obj, d, depends_all)


def get_environment():
    env = {}
    env['WORKSPACE'] = os.environ['WORKSPACE']
    env['INSTALL_DIR'] = os.environ['INSTALL_DIR']
    env['HOME'] = '/home/rosbuild'#os.environ['INSTALL_DIR']
    env['JOB_NAME'] = os.environ['JOB_NAME']
    env['BUILD_NUMBER'] = os.environ['BUILD_NUMBER']
    env['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR']
    env['PWD'] = os.environ['WORKSPACE']
    return env


def get_options(required, optional):
    parser = optparse.OptionParser()
    ops = required + optional
    if 'rosdistro' in ops:
        parser.add_option('--rosdistro', dest = 'rosdistro', default=None, action='store',
                          help='Ros distro name')
    if 'stack' in ops:
        parser.add_option('--stack', dest = 'stack', default=None, action='append',
                          help='Stack name')
    if 'email' in ops:
        parser.add_option('--email', dest = 'email', default=None, action='store',
                          help='Email address to send results to')
    if 'repeat' in ops:
        parser.add_option('--repeat', dest = 'repeat', default=0, action='store',
                          help='How many times to repeat the test')
    if 'source-only' in ops:
        parser.add_option('--source-only', dest = 'source_only', default=False, action='store_true',
                          help="Build everything from source, don't use Debian packages")
    if 'delete' in ops:
        parser.add_option('--delete', dest = 'delete', default=False, action='store_true',
                          help='Delete jobs from Hudson')    
    if 'wait' in ops:
        parser.add_option('--wait', dest = 'wait', default=False, action='store_true',
                          help='Wait for running jobs to finish to reconfigure them')    
    if 'rosinstall' in ops:
        parser.add_option('--rosinstall', dest = 'rosinstall', default=None, action='store',
                          help="Specify the rosinstall file that refers to unreleased code.")
    if 'overlay' in ops:
        parser.add_option('--overlay', dest = 'overlay', default=None, action='store',
                          help='Create overlay file')
    if 'variant' in ops:
        parser.add_option('--variant', dest = 'variant', default=None, action='store',
                          help="Specify the variant to create a rosinstall for")
    if 'database' in ops:
        parser.add_option('--database', dest = 'database', default=None, action='store',
                          help="Specify database file")

    print "Do the parsing"
    (options, args) = parser.parse_args()
    

    # make repeat an int
    if 'repeat' in ops:
        options.repeat = int(options.repeat)

    # check if required arguments are there
    for r in required:
        if not eval('options.%s'%r):
            print 'You need to specify "--%s"'%r
            return (None, args)

    # postprocessing
    if 'email' in ops and options.email and not '@' in options.email:
        options.email = options.email + '@willowgarage.com'        


    # check if rosdistro exists
    print "Check if rosdistro exists"
    if 'rosdistro' in ops and (not options.rosdistro or not options.rosdistro in UBUNTU_DISTRO_MAP.keys()):
        print 'You provided an invalid "--rosdistro %s" argument. Options are %s'%(options.rosdistro, UBUNTU_DISTRO_MAP.keys())
        return (None, args)

    # check if stacks exist
    print "Check if stack exists"
    if 'stack' in ops and options.stack:
        distro_obj = rosdistro.Distro(get_rosdistro_file(options.rosdistro))
        for s in options.stack:
            if not s in distro_obj.stacks:
                print 'Stack "%s" does not exist in the %s disro file.'%(s, options.rosdistro)
                print 'You need to add this stack to the rosdistro file'
                return (None, args)

    # check if variant exists
    print "Check if variant exists"
    if 'variant' in ops and options.variant:
        distro_obj = rosdistro.Distro(get_rosdistro_file(options.rosdistro))
        if not options.variant in distro_obj.variants:
                print 'Variant "%s" does not exist in the %s disro file.'%(options.variant, options.rosdistro)
                return (None, args)

    return (options, args)


def schedule_jobs(jobs, wait=False, delete=False, start=False, hudson_obj=None):
    # create hudson instance
    if not hudson_obj:
        info = urllib.urlopen(CONFIG_PATH).read().split(',')
        hudson_obj = hudson.Hudson(SERVER, info[0], info[1])

    finished = False
    while not finished:
        jobs_todo = {}
        for job_name in jobs:
            exists = hudson_obj.job_exists(job_name)

            # job is already running
            if exists and hudson_obj.job_is_running(job_name):
                jobs_todo[job_name] = jobs[job_name]
                print "Not reconfiguring running job %s because it is still running"%job_name


            # delete old job
            elif delete:
                if exists:
                    hudson_obj.delete_job(job_name)
                    print " - Deleting job %s"%job_name

            # reconfigure job
            elif exists:
                hudson_obj.reconfig_job(job_name, jobs[job_name])
                if start:
                    hudson_obj.build_job(job_name)
                print " - %s"%job_name

            # create job
            elif not exists:
                hudson_obj.create_job(job_name, jobs[job_name])
                if start:
                    hudson_obj.build_job(job_name)
                print " - %s"%job_name

        if wait and len(jobs_todo) > 0:
            jobs = jobs_todo
            jobs_todo = {}
            time.sleep(10.0)
        else:
            finished = True



def get_rosdistro_file(rosdistro):
    return 'https://code.ros.org/svn/release/trunk/distros/%s.rosdistro'%rosdistro



def get_email_triggers(when, send_devel=True):
    triggers = ''
    for w in when:
        trigger = EMAIL_TRIGGER
        trigger = trigger.replace('WHEN', w)
        if send_devel:
            trigger = trigger.replace('SEND_DEVEL', 'true')
        else:
            trigger = trigger.replace('SEND_DEVEL', 'false')
        triggers += trigger
    return triggers


def get_job_name(jobtype, rosdistro, stack_name, ubuntu, arch):
    if len(stack_name) > 50:
        stack_name = stack_name[0:46]+'_...'
    return "_".join([jobtype, rosdistro, stack_name, ubuntu, arch])


def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def write_file(filename, msg):
    ensure_dir(filename)
    with open(filename, 'w') as f:
        f.write(msg)
    

def call(command, env, message='', ignore_fail=False):
    res = ''
    err = ''
    try:
        print message+'\nExecuting command "%s"'%command
        helper = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        res, err = helper.communicate()
        print str(res)
        print str(err)
        if helper.returncode != 0:
            raise Exception
        return res
    except Exception:
        if not ignore_fail:
            message += "\n=========================================\n"
            message += "Failed to execute '%s'"%command
            message += "\n=========================================\n"
            message += str(res)
            message += "\n=========================================\n"
            message += str(err)
            message += "\n=========================================\n"
            message += "ROS_PACKAGE_PATH = %s\n"%env['ROS_PACKAGE_PATH']
            message += "ROS_ROOT = %s\n"%env['ROS_ROOT']
            message += "PYTHONPATH = %s\n"%env['PYTHONPATH']
            message += "\n=========================================\n"
            write_file(env['WORKSPACE']+'/build_output/buildfailures.txt', message)
            write_file(env['WORKSPACE']+'/test_output/testfailures.txt', '')
            write_file(env['WORKSPACE']+'/build_output/buildfailures-with-context.txt', '')
            raise Exception

        

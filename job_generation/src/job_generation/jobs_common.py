#!/usr/bin/python

import os
import optparse
import rosdistro

BOOTSTRAP_SCRIPT = """
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

ROSDISTRO_FOLDER_MAP = {'unstable': 'https://code.ros.org/svn/release/trunk/distros',
                        'cturtle': 'https://code.ros.org/svn/release/trunk/distros',
                        'boxturtle': 'http://www.ros.org/distros'}

ROSDISTRO_MAP = {'unstable': 'https://code.ros.org/svn/release/trunk/distros/unstable.rosdistro',
                 'cturtle': 'https://code.ros.org/svn/release/trunk/distros//cturtle.rosdistro',
                 'boxturtle': 'http://www.ros.org/distros/boxturtle.rosdistro'}

# the supported Ubuntu distro's for each ros distro
ARCHES = ['amd64', 'i386']

# ubuntu distro mapping to ros distro
UBUNTU_DISTRO_MAP = {'unstable': ['lucid', 'maverick'],
                     'cturtle':  ['lucid', 'karmic', 'jaunty', 'maverick'],
                     'boxturtle':['hardy','karmic', 'jaunty']}

# path to hudson server
SERVER = 'http://build.willowgarage.com'

# config path
CONFIG_PATH = 'http://wgs24.willowgarage.com/hudson-html/hds.xml'


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

def stack_to_rosinstall(stack, branch):
    vcs = stack.vcs_config
    if not branch in ['devel', 'release', 'distro']:
        print 'Unsupported branch type %s for stack %s'%(branch, stack.name)
        return ''
    if not vcs.type in ['svn', 'hg', 'git']:
        print 'Unsupported vcs type %s for stack %s'%(vcs.type, stack.name)
        return ''
        
    if vcs.type == 'svn':
        if branch == 'devel':
            return "- svn: {uri: '%s', local-name: '%s'}\n"%(vcs.anon_dev, stack.name)
        elif branch == 'distro':
            return "- svn: {uri: '%s', local-name: '%s'}\n"%(vcs.anon_distro_tag, stack.name)            

        elif branch == 'release':
            return "- svn: {uri: '%s', local-name: '%s'}\n"%(vcs.anon_release_tag, stack.name)  

    elif vcs.type == 'hg' or vcs.type =='git':
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
    
def get_environment():
    env = {}
    env['WORKSPACE'] = os.environ['WORKSPACE']
    env['INSTALL_DIR'] = os.environ['INSTALL_DIR']
    env['HOME'] = os.environ['INSTALL_DIR']
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
    if 'delete' in ops:
        parser.add_option('--delete', dest = 'delete', default=False, action='store_true',
                          help='Delete jobs from Hudson')    
    if 'wait' in ops:
        parser.add_option('--wait', dest = 'wait', default=False, action='store_true',
                          help='Wait for running jobs to finish to reconfigure them')    
    if 'start' in ops:
        parser.add_option('--start', dest = 'start', default=False, action='store_true',
                          help='Start jobs')    
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

    (options, args) = parser.parse_args()
    

    # check if required arguments are there
    for r in required:
        if not eval('options.%s'%r):
            print 'You need to specify "--%s"'%r
            return None

    # postprocessing
    if 'email' in ops and options.email and not '@' in options.email:
        options.email = options.email + '@willowgarage.com'        


    # check if rosdistro exists
    if 'rosdistro' in ops and (not options.rosdistro or not options.rosdistro in UBUNTU_DISTRO_MAP.keys()):
        print 'You profided an invalid "--rosdistro %s" argument. Options are %s'%(options.rosdistro, UBUNTU_DISTRO_MAP.keys())
        return None

    # check if stacks exist
    if 'stack' in ops and options.stack:
        distro_obj = rosdistro.Distro(ROSDISTRO_MAP[options.rosdistro])
        for s in options.stack:
            if not s in distro_obj.stacks:
                print 'Stack "%s" does not exist in the %s disro file.'%(s, options.rosdistro)
                print 'You need to add this stack to the rosdistro file'
                return None

    # check if variant exists
    if 'variant' in ops and options.variant:
        distro_obj = rosdistro.Distro(ROSDISTRO_MAP[options.rosdistro])
        if not options.variant in distro_obj.variants:
                print 'Variant "%s" does not exist in the %s disro file.'%(options.variant, options.rosdistro)
                return None

    return options

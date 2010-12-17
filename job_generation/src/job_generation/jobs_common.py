#!/usr/bin/python

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
    

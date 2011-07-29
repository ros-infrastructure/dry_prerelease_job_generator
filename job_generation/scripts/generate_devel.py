#!/usr/bin/python

# template to create develop hudscon configuration file
HUDSON_DEVEL_CONFIG = """<?xml version='1.0' encoding='UTF-8'?>
<project> 
  <description>Build of STACKNAME development branch for ROSDISTRO on UBUNTUDISTRO, ARCH</description> 
 <logRotator> 
    <daysToKeep>21</daysToKeep> 
    <numToKeep>-1</numToKeep> 
  </logRotator> 
  <keepDependencies>false</keepDependencies> 
  <properties> 
    <hudson.plugins.trac.TracProjectProperty> 
      <tracWebsite>http://code.ros.org/trac/ros/</tracWebsite> 
    </hudson.plugins.trac.TracProjectProperty> 
  </properties> 
  HUDSON_VCS
  <assignedNode>NODE</assignedNode>
  <canRoam>false</canRoam> 
  <disabled>false</disabled> 
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding> 
  <triggers class="vector"> 
    <hudson.triggers.SCMTrigger> 
      <spec>TIME_TRIGGER</spec> 
    </hudson.triggers.SCMTrigger> 
  </triggers> 
  <concurrentBuild>false</concurrentBuild> 
  <builders> 
    <hudson.tasks.Shell> 
      <command>
BOOTSTRAP_SCRIPT
rosrun job_generation run_auto_stack_devel.py --stack STACKNAME --rosdistro ROSDISTRO --repeat 0 SOURCE_ONLY
SHUTDOWN_SCRIPT
     </command> 
    </hudson.tasks.Shell> 
  </builders> 
  <publishers> 
    <hudson.tasks.BuildTrigger> 
      <childProjects>JOB_CHILDREN</childProjects> 
      <threshold> 
        <name>SUCCESS</name> 
        <ordinal>0</ordinal> 
        <color>BLUE</color> 
      </threshold> 
    </hudson.tasks.BuildTrigger> 
    <hudson.tasks.junit.JUnitResultArchiver> 
      <testResults>test_results/**/_hudson/*.xml</testResults> 
    </hudson.tasks.junit.JUnitResultArchiver> 
    <hudson.plugins.emailext.ExtendedEmailPublisher> 
      <recipientList>EMAIL</recipientList> 
      <configuredTriggers> 
        EMAIL_TRIGGERS
      </configuredTriggers> 
      <defaultSubject>$DEFAULT_SUBJECT</defaultSubject> 
      <defaultContent>$DEFAULT_CONTENT&#xd;
&#xd;
&lt;% &#xd;
def ws = build.getParent().getWorkspace()&#xd;
def computer = build.getExecutor().getOwner()&#xd;
def build_failures = hudson.util.RemotingDiagnostics.executeGroovy(&quot;new File(\&quot;${ws}/build_output/buildfailures.txt\&quot;).text&quot;,computer.getChannel())&#xd;
println &quot;${build_failures}&quot;&#xd;
def test_failures = hudson.util.RemotingDiagnostics.executeGroovy(&quot;new File(\&quot;${ws}/test_output/testfailures.txt\&quot;).text&quot;,computer.getChannel())&#xd;
println &quot;${test_failures}&quot;&#xd;
def build_failures_context = hudson.util.RemotingDiagnostics.executeGroovy(&quot;new File(\&quot;${ws}/build_output/buildfailures-with-context.txt\&quot;).text&quot;,computer.getChannel())&#xd;
println &quot;${build_failures_context}&quot;&#xd;
%&gt;</defaultContent> 
      <defaultContentTypeHTML>false</defaultContentTypeHTML> 
      <defaultContentIsScript>true</defaultContentIsScript> 
    </hudson.plugins.emailext.ExtendedEmailPublisher> 
  </publishers> 
  <buildWrappers/> 
</project>
"""


import roslib; roslib.load_manifest("job_generation")
import rosdistro
from job_generation.jobs_common import *


def devel_job_name(rosdistro, stack_name, ubuntu, arch):
    return get_job_name('devel', rosdistro, stack_name, ubuntu, arch)


def create_devel_configs(os, rosdistro, stack):
    dist_arch = []
    if os == 'ubuntu':
        for ubuntudistro in UBUNTU_DISTRO_MAP[rosdistro]:
            for arch in ARCHES:
                dist_arch.append((ubuntudistro, arch))
        bootstrap_script = BOOTSTRAP_SCRIPT
        shutdown_script = SHUTDOWN_SCRIPT
        source_only = ''
        node = 'devel'
    elif os == 'osx':
        dist_arch.append(('osx', 'amd64'))
        bootstrap_script = BOOTSTRAP_SCRIPT_OSX
        shutdown_script = SHUTDOWN_SCRIPT_OSX
        source_only = '--source-only'
        node = 'osx10_5_vnc'

    # create gold distro
    gold_children = [devel_job_name(rosdistro, stack.name, u, a) for (u, a) in dist_arch]
    gold_job = gold_children[0]
    gold_children.remove(gold_job)

    # create hudson config files for each ubuntu distro
    configs = {}
    for (osdistro, arch) in dist_arch:
        name = devel_job_name(rosdistro, stack.name, osdistro, arch)

        # create VCS block
        if stack.vcs_config.type in hudson_scm_managers:
            hudson_vcs = hudson_scm_managers[stack.vcs_config.type]
        else:
            raise NotImplementedError("vcs type %s not implemented as hudson scm manager"%stack.vcs_config.type)


        if stack.vcs_config.type in ['svn']:
            hudson_vcs = hudson_vcs.replace('STACKNAME', stack.name)
            hudson_vcs = hudson_vcs.replace('STACKURI', stack.vcs_config.anon_dev)
        elif stack.vcs_config.type in ['git', 'hg', 'bzr']:
            hudson_vcs = hudson_vcs.replace('STACKBRANCH', stack.vcs_config.dev_branch)
            hudson_vcs = hudson_vcs.replace('STACKURI', stack.vcs_config.anon_repo_uri)
            hudson_vcs = hudson_vcs.replace('STACKNAME', stack.name)
        else:
            print "UNSUPPORTED VCS TYPE"
            raise

        # check if this is the 'gold' job
        time_trigger = ''
        job_children = ''
        if name == gold_job:
            time_trigger = '*/5 * * * *'
            job_children = ', '.join(gold_children)

        hudson_config = HUDSON_DEVEL_CONFIG
        hudson_config = hudson_config.replace('SOURCE_ONLY', source_only)
        hudson_config = hudson_config.replace('BOOTSTRAP_SCRIPT', bootstrap_script)
        hudson_config = hudson_config.replace('SHUTDOWN_SCRIPT', shutdown_script)
        hudson_config = hudson_config.replace('EMAIL_TRIGGERS', get_email_triggers(['Unstable', 'Failure', 'Fixed']))
        hudson_config = hudson_config.replace('UBUNTUDISTRO', osdistro)
        hudson_config = hudson_config.replace('ARCH', arch)
        hudson_config = hudson_config.replace('ROSDISTRO', rosdistro)
        hudson_config = hudson_config.replace('STACKNAME', stack.name)   
        hudson_config = hudson_config.replace('HUDSON_VCS', hudson_vcs)
        hudson_config = hudson_config.replace('TIME_TRIGGER', time_trigger)
        hudson_config = hudson_config.replace('JOB_CHILDREN', job_children)
        hudson_config = hudson_config.replace('EMAIL', 'wim+devel@willowgarage.com')
        hudson_config = hudson_config.replace('NODE', node)
        configs[name] = hudson_config
    return configs

    
    

def main():
    (options, args) = get_options(['rosdistro'], ['delete', 'wait', 'stack', 'os'])
    if not options:
        return -1

    # generate hudson config files
    distro_obj = rosdistro.Distro(get_rosdistro_file(options.rosdistro))
    if options.stack:
        stack_list = options.stack
        for s in stack_list:
            if not s in distro_obj.released_stacks:
                if s in distro_obj.stacks:
                    print "Stack %s is in rosdistro file, but it is not yet released (version is set to 'null'"%s
                else:
                    print "Stack %s is not in rosdistro file"%s
                return
    else:
        stack_list = distro_obj.released_stacks
    devel_configs = {}
    for stack_name in stack_list:
        devel_configs.update(create_devel_configs(options.os, distro_obj.release_name, distro_obj.stacks[stack_name]))

    # schedule jobs
    schedule_jobs(devel_configs, options.wait, options.delete)


if __name__ == '__main__':
    main()





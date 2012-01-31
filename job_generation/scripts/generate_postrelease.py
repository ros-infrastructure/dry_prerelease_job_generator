#!/usr/bin/python
import random

# template to create post-release hudscon configuration file
HUDSON_POST_RELEASE_CONFIG = """<?xml version='1.0' encoding='UTF-8'?>
<project> 
  <description>Build of STACKNAME post-release for ROSDISTRO on UBUNTUDISTRO, ARCH</description> 
 <logRotator> 
    <daysToKeep>180</daysToKeep> 
    <numToKeep>-1</numToKeep> 
  </logRotator> 
  <keepDependencies>false</keepDependencies> 
  <properties> 
    <hudson.plugins.trac.TracProjectProperty> 
      <tracWebsite>http://code.ros.org/trac/ros/</tracWebsite> 
    </hudson.plugins.trac.TracProjectProperty> 
  </properties> 
  HUDSON_VCS
  <assignedNode>released</assignedNode>
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
run_auto_stack_postrelease.py --stack STACKNAME --rosdistro ROSDISTRO
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

import time
from job_generation.jobs_common import *
import urllib
import optparse 

def post_release_job_name(distro_name, stack_name, ubuntu, arch):
    return get_job_name('released', distro_name, stack_name, ubuntu, arch)


def create_post_release_configs(distro_name, stack):
    stack_name = stack.name
    
    # create gold distro
    gold_job = post_release_job_name(distro_name, stack_name, UBUNTU_DISTRO_MAP[distro_name][0], ARCHES[0])
    gold_children = [post_release_job_name(distro_name, stack_name, u, a)
                     for a in ARCHES for u in UBUNTU_DISTRO_MAP[distro_name]]
    gold_children.remove(gold_job)

    # create hudson config files for each ubuntu distro
    configs = {}
    for ubuntudistro in UBUNTU_DISTRO_MAP[distro_name]:
        for arch in ARCHES:
            name = post_release_job_name(distro_name, stack_name, ubuntudistro, arch)

            # create VCS block
            if stack.vcs_config.type in hudson_scm_managers:
                hudson_vcs = hudson_scm_managers[stack.vcs_config.type]
            else:
                raise NotImplementedError("vcs type %s not implemented as hudson scm manager"%stack.vcs_config.type)

            # this code is essentially the same as generate_devel and should be merged
            vcs_config = stack.vcs_config
            if vcs_config.type in ['svn']:
                # TODO: should probably use 'release' branch instead
                #url, version = vcs_config.get_branch('release', anonymous=True)
                url, version = vcs_config.get_branch('distro', anonymous=True)
                hudson_vcs = hudson_vcs.replace('STACKNAME', stack_name)
                hudson_vcs = hudson_vcs.replace('STACKURI', url)
            elif stack.vcs_config.type in ['git', 'hg', 'bzr']:
                url, version = vcs_config.get_branch('devel', anonymous=True)
                hudson_vcs = hudson_vcs.replace('STACKBRANCH', version)
                hudson_vcs = hudson_vcs.replace('STACKURI', url)
                hudson_vcs = hudson_vcs.replace('STACKNAME', stack_name)
            else:
                print "UNSUPPORTED VCS TYPE"
                raise

            # check if this is the 'gold' job
            time_trigger = ''
            job_children = ''
            if name == gold_job:
                # random time between 0:00 and 4:50
                time_trigger = '%d %d * * *'%(int(50*random.random()), int(4*random.random()))
                job_children = ', '.join(gold_children)
            hudson_config = HUDSON_POST_RELEASE_CONFIG
            hudson_config = hudson_config.replace('BOOTSTRAP_SCRIPT', BOOTSTRAP_SCRIPT)
            hudson_config = hudson_config.replace('SHUTDOWN_SCRIPT', SHUTDOWN_SCRIPT)
            hudson_config = hudson_config.replace('EMAIL_TRIGGERS', get_email_triggers(['Unstable', 'Failure', 'Fixed']))
            hudson_config = hudson_config.replace('UBUNTUDISTRO', ubuntudistro)
            hudson_config = hudson_config.replace('ARCH', arch)
            hudson_config = hudson_config.replace('ROSDISTRO', distro_name)
            hudson_config = hudson_config.replace('STACKNAME', stack_name)   
            hudson_config = hudson_config.replace('HUDSON_VCS', hudson_vcs)
            hudson_config = hudson_config.replace('TIME_TRIGGER', time_trigger)
            hudson_config = hudson_config.replace('JOB_CHILDREN', job_children)
            hudson_config = hudson_config.replace('EMAIL', 'wim+released@willowgarage.com')
            configs[name] = hudson_config
    return configs

    
    

def main():
    (options, args) = get_options(['rosdistro'], ['delete', 'wait', 'stack'])
    if not options:
        return -1
    distro_name = options.distro_name

    # Parse distro file
    distro_obj = rospkg.distro.load_distro(rospkg.distro.distro_uri(distro_name))
    print 'Operating on ROS distro %s'%distro_obj.release_name

    # generate hudson config files
    post_release_configs = {}
    if options.stack:
        stack_list = options.stack
    else:
        stack_list = distro_obj.released_stacks
    for stack_name in stack_list:
        post_release_configs.update(create_post_release_configs(distro_obj.release_name, distro_obj.released_stacks[stack_name]))

    # schedule jobs
    schedule_jobs(post_release_configs, options.wait, options.delete)


if __name__ == '__main__':
    main()





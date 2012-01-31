#!/usr/bin/python


HUDSON_SVN_ITEM = """
   <hudson.scm.SubversionSCM_-ModuleLocation> 
     <remote>STACKURI</remote> 
     <local>STACKNAME</local> 
   </hudson.scm.SubversionSCM_-ModuleLocation> 
"""

HUDSON_SVN = """
  <scm class="hudson.scm.SubversionSCM"> 
    <locations> 
      HUDSON_SVN_ITEMS
    </locations> 
    <useUpdate>false</useUpdate> 
    <doRevert>false</doRevert> 
    <excludedRegions></excludedRegions> 
    <includedRegions></includedRegions> 
    <excludedUsers></excludedUsers> 
    <excludedRevprop></excludedRevprop> 
    <excludedCommitMessages></excludedCommitMessages> 
  </scm> 
"""

# template to create unreleased hudson configuration file
HUDSON_UNRELEASED_CONFIG = """<?xml version='1.0' encoding='UTF-8'?>
<project> 
  <description>Unreleased build of NAME for ROSDISTRO on UBUNTUDISTRO, ARCH</description> 
 <logRotator> 
    <daysToKeep>5</daysToKeep> 
    <numToKeep>-1</numToKeep> 
  </logRotator> 
  <keepDependencies>false</keepDependencies> 
  <properties> 
    <hudson.plugins.trac.TracProjectProperty> 
      <tracWebsite>http://code.ros.org/trac/ros/</tracWebsite> 
    </hudson.plugins.trac.TracProjectProperty> 
  </properties> 
  HUDSON_VCS
  <assignedNode>unreleased</assignedNode>
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
run_auto_stack_unreleased.py --rosdistro ROSDISTRO
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
      <testResults>test_results/_hudson/*.xml</testResults> 
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

from job_generation.jobs_common import *
import yaml

def unreleased_job_name(distro_name, rosinstall, ubuntu, arch):
    return get_job_name('unreleased', distro_name, rosinstall.split('/')[-1].split('.')[0], ubuntu, arch)


def rosinstall_to_vcs(rosinstall):
    with open(rosinstall) as f:
        rosinstall = yaml.load(f.read())
        items = ''
        for r in rosinstall:
            item = HUDSON_SVN_ITEM
            item = item.replace('STACKNAME', r['svn']['local-name'])
            item = item.replace('STACKURI', r['svn']['uri'])
            items += item
        return HUDSON_SVN.replace('HUDSON_SVN_ITEMS', items)



def create_unreleased_configs(distro_name, rosinstall):
    # create gold distro
    gold_job = unreleased_job_name(distro_name, rosinstall, UBUNTU_DISTRO_MAP[distro_name][0], ARCHES[0])
    gold_children = [unreleased_job_name(distro_name, rosinstall, u, a)
                     for a in ARCHES for u in UBUNTU_DISTRO_MAP[distro_name]]
    gold_children.remove(gold_job)

    # create hudson config files for each ubuntu distro
    configs = {}
    for ubuntudistro in UBUNTU_DISTRO_MAP[distro_name]:
        for arch in ARCHES:
            name = unreleased_job_name(distro_name, rosinstall, ubuntudistro, arch)

            # check if this is the 'gold' job
            time_trigger = ''
            job_children = ''
            if name == gold_job:
                time_trigger = '*/5 * * * *'
                job_children = ', '.join(gold_children)

            hudson_config = HUDSON_UNRELEASED_CONFIG
            hudson_config = hudson_config.replace('BOOTSTRAP_SCRIPT', BOOTSTRAP_SCRIPT)
            hudson_config = hudson_config.replace('SHUTDOWN_SCRIPT', SHUTDOWN_SCRIPT)
            hudson_config = hudson_config.replace('EMAIL_TRIGGERS', get_email_triggers(['Unstable', 'Failure', 'StillFailing', 'Fixed', 'StillUnstable']))
            hudson_config = hudson_config.replace('UBUNTUDISTRO', ubuntudistro)
            hudson_config = hudson_config.replace('ARCH', arch)
            hudson_config = hudson_config.replace('ROSDISTRO', distro_name)
            hudson_config = hudson_config.replace('HUDSON_VCS', rosinstall_to_vcs(rosinstall))
            hudson_config = hudson_config.replace('TIME_TRIGGER', time_trigger)
            hudson_config = hudson_config.replace('JOB_CHILDREN', job_children)
            hudson_config = hudson_config.replace('EMAIL', 'wim+unreleased@willowgarage.com')
            configs[name] = hudson_config
    return configs
    
    

def main():
    (options, args) = get_options(['rosdistro', 'rosinstall'], ['delete', 'wait'])
    if not options:
        return -1

    # send unreleased tests to Hudson
    print 'Creating unreleased Hudson jobs:'
    unreleased_configs = create_unreleased_configs(options.rosdistro, options.rosinstall)
    schedule_jobs(unreleased_configs, options.wait, options.delete)


if __name__ == '__main__':
    main()





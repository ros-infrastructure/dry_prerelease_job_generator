#!/usr/bin/python

import traceback

# template to create pre-release hudson configuration file
HUDSON_PRERELEASE_CONFIG = """<?xml version='1.0' encoding='UTF-8'?>
<project> 
  <description>Pre-release build of STACKNAME for ROSDISTRO on UBUNTUDISTRO, ARCH</description> 
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
  <scm/>
  <assignedNode>prerelease</assignedNode>
  <canRoam>false</canRoam> 
  <disabled>false</disabled> 
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding> 
  <triggers class="vector"/> 
  <concurrentBuild>false</concurrentBuild> 
  <builders> 
    <hudson.tasks.Shell> 
      <command>
BOOTSTRAP_SCRIPT
run_auto_stack_prerelease.py STACKARGS --rosdistro ROSDISTRO --repeat REPEAT SOURCE_ONLY
SHUTDOWN_SCRIPT
     </command> 
    </hudson.tasks.Shell> 
  </builders> 
  <publishers> 
    <hudson.tasks.junit.JUnitResultArchiver> 
      <testResults>test_results/**/_hudson/*.xml</testResults> 
      <keepLongStdio>false</keepLongStdio> 
      <testDataPublishers/> 
    </hudson.tasks.junit.JUnitResultArchiver> 
    <hudson.plugins.emailext.ExtendedEmailPublisher> 
      <recipientList>EMAIL,rosrelease-prerelease@kforge.ros.org</recipientList> 
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
import jenkins
import urllib
import optparse 

def prerelease_job_name(distro_name, stack_list, ubuntu, arch):
    return get_job_name('prerelease', distro_name, '_'.join(stack_list), ubuntu, arch)


def create_prerelease_configs(distro_name, stack_list, email, repeat, source_only, arches=None, ubuntudistros=None):
    stack_list.sort()

    if not arches:
        arches = ARCHES
    if not ubuntudistros:
        ubuntudistros = UBUNTU_DISTRO_MAP[distro_name]

    # create hudson config files for each ubuntu distro
    configs = {}
    for ubuntudistro in ubuntudistros:
        for arch in arches:
            name = prerelease_job_name(distro_name, stack_list, ubuntudistro, arch)
            hudson_config = HUDSON_PRERELEASE_CONFIG
            hudson_config = hudson_config.replace('BOOTSTRAP_SCRIPT', BOOTSTRAP_SCRIPT)
            hudson_config = hudson_config.replace('SHUTDOWN_SCRIPT', SHUTDOWN_SCRIPT)
            hudson_config = hudson_config.replace('EMAIL_TRIGGERS', get_email_triggers(['Unstable', 'Failure', 'StillFailing', 'Fixed', 'StillUnstable', 'Success'], False))
            hudson_config = hudson_config.replace('UBUNTUDISTRO', ubuntudistro)
            hudson_config = hudson_config.replace('ARCH', arch)
            hudson_config = hudson_config.replace('ROSDISTRO', distro_name)
            hudson_config = hudson_config.replace('STACKNAME', '---'.join(stack_list))
            hudson_config = hudson_config.replace('STACKARGS', ' '.join(['--stack %s'%s for s in stack_list]))
            hudson_config = hudson_config.replace('EMAIL', email)
            hudson_config = hudson_config.replace('REPEAT', str(repeat))
            if source_only:
                hudson_config = hudson_config.replace('SOURCE_ONLY', '--source-only')
            else:
                hudson_config = hudson_config.replace('SOURCE_ONLY', '')                
            configs[name] = hudson_config
    return configs
    
    

def main():
    (options, args) = get_options(['stack', 'rosdistro', 'email'], ['repeat', 'source-only', 'arch', 'ubuntu', 'delete'])
    if not options:
        return -1

    try:
        # create hudson instance
        if len(args) == 2:
            hudson_instance = jenkins.Jenkins(SERVER, args[0], args[1])
        else:
            info = urllib.urlopen(CONFIG_PATH).read().split(',')
            hudson_instance = jenkins.Jenkins(SERVER, info[0], info[1])
        prerelease_configs = create_prerelease_configs(options.rosdistro, options.stack, options.email, options.repeat, options.source_only, options.arch, options.ubuntu)

        # check if jobs are not already running
        for job_name in prerelease_configs:
            exists = hudson_instance.job_exists(job_name)
            if exists and job_is_running(hudson_instance, job_name):
                print 'Cannot create job %s because a job with the same name is already running.'%job_name
                print 'Please try again when this job finished running.'
                return 

        # send prerelease tests to Hudson
        print 'Creating pre-release Hudson jobs:'
        schedule_jobs(prerelease_configs, start=True, hudson_obj=hudson_instance, delete=options.delete)
        if options.delete:
            print 'Jobs have been deleted. You can now start new jobs'
        else:
            print 'You will receive %d emails on %s, one for each job'%(len(prerelease_configs), options.email)
            print 'You can follow the progress of these jobs on <%s/view/pre-release>'%(SERVER)

    # catch all exceptions
    except Exception, e:
        traceback.print_exc() 
        print 'ERROR: Failed to communicate with Hudson server. Try again later.'


if __name__ == '__main__':
    main()





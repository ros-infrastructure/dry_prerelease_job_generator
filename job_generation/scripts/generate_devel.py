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
  <assignedNode>devel</assignedNode>
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
      <command>cat &gt; $WORKSPACE/script.sh &lt;&lt;DELIM
#!/usr/bin/env bash
set -o errexit
echo "_________________________________BEGIN SCRIPT______________________________________"
BOOTSTRAP_SCRIPT
rosrun job_generation run_auto_stack_devel.py --stack STACKNAME --rosdistro ROSDISTRO --repeat 0
echo "_________________________________END SCRIPT_______________________________________"
DELIM

set -o errexit

rm -rf $WORKSPACE/test_results
rm -rf $WORKSPACE/test_output

wget https://code.ros.org/svn/ros/stacks/ros_release/trunk/hudson/scripts/run_chroot.py --no-check-certificate -O $WORKSPACE/run_chroot.py
chmod +x $WORKSPACE/run_chroot.py
cd $WORKSPACE &amp;&amp; $WORKSPACE/run_chroot.py --distro=UBUNTUDISTRO --arch=ARCH  --ramdisk --ssh-key-file=/home/rosbuild/rosbuild-ssh.tar --script=$WORKSPACE/script.sh
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
        <hudson.plugins.emailext.plugins.trigger.UnstableTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.UnstableTrigger> 
        <hudson.plugins.emailext.plugins.trigger.FailureTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.FailureTrigger> 
        <hudson.plugins.emailext.plugins.trigger.StillFailingTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.StillFailingTrigger> 
        <hudson.plugins.emailext.plugins.trigger.FixedTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 

          </email> 
        </hudson.plugins.emailext.plugins.trigger.FixedTrigger> 
        <hudson.plugins.emailext.plugins.trigger.StillUnstableTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.StillUnstableTrigger> 
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
import time
from job_generation.jobs_common import *
import hudson
import urllib
import optparse 


def devel_job_name(rosdistro, stack_name, ubuntu, arch):
    return "_".join(['devel', rosdistro, stack_name, ubuntu, arch])


def create_devel_configs(rosdistro, stack):
    # create gold distro
    gold_job = devel_job_name(rosdistro, stack.name, UBUNTU_DISTRO_MAP[rosdistro][0], ARCHES[0])
    gold_children = [devel_job_name(rosdistro, stack.name, u, a)
                     for a in ARCHES for u in UBUNTU_DISTRO_MAP[rosdistro]]
    gold_children.remove(gold_job)

    # create hudson config files for each ubuntu distro
    configs = {}
    for ubuntudistro in UBUNTU_DISTRO_MAP[rosdistro]:
        for arch in ARCHES:
            name = devel_job_name(rosdistro, stack.name, ubuntudistro, arch)

            # create VCS block
            if stack.vcs_config.type in hudson_scm_managers:
                hudson_vcs = hudson_scm_managers[stack.vcs_config.type]
            else:
                raise NotImplementedError("vcs type %s not implemented as hudson scm manager"%stack.vcs_config.type)

            
            if stack.vcs_config.type == 'svn':
                hudson_vcs = hudson_vcs.replace('STACKNAME', stack.name)
                hudson_vcs = hudson_vcs.replace('STACKURI', stack.vcs_config.anon_dev)
            else: #dvcs
                hudson_vcs = hudson_vcs.replace('STACKBRANCH', stack.vcs_config.dev_branch)
                hudson_vcs = hudson_vcs.replace('STACKURI', stack.vcs_config.anon_repo_uri)
                hudson_vcs = hudson_vcs.replace('STACKNAME', stack.name)

            # check if this is the 'gold' job
            time_trigger = ''
            job_children = ''
            if name == gold_job:
                time_trigger = '*/5 * * * *'
                job_children = ', '.join(gold_children)

            hudson_config = HUDSON_DEVEL_CONFIG
            hudson_config = hudson_config.replace('BOOTSTRAP_SCRIPT', BOOTSTRAP_SCRIPT)
            hudson_config = hudson_config.replace('UBUNTUDISTRO', ubuntudistro)
            hudson_config = hudson_config.replace('ARCH', arch)
            hudson_config = hudson_config.replace('ROSDISTRO', rosdistro)
            hudson_config = hudson_config.replace('STACKNAME', stack.name)   
            hudson_config = hudson_config.replace('HUDSON_VCS', hudson_vcs)
            hudson_config = hudson_config.replace('TIME_TRIGGER', time_trigger)
            hudson_config = hudson_config.replace('JOB_CHILDREN', job_children)
            hudson_config = hudson_config.replace('EMAIL', 'wim+devel@willowgarage.com')
            configs[name] = hudson_config
    return configs

    
    

def main():
    (options, args) = get_options(['rosdistro'], ['delete', 'wait', 'stack'])
    if not options:
        return -1


    # Parse distro file
    distro_obj = rosdistro.Distro(ROSDISTRO_MAP[options.rosdistro])
    print 'Operating on ROS distro %s'%distro_obj.release_name


    # create hudson instance
    info = urllib.urlopen(CONFIG_PATH).read().split(',')
    hudson_instance = hudson.Hudson(SERVER, info[0], info[1])


    # generate hudson config files
    devel_configs = {}
    if options.stack:
        stack_list = options.stack
    else:
        stack_list = distro_obj.stacks
    for stack_name in stack_list:
        devel_configs.update(create_devel_configs(distro_obj.release_name, distro_obj.stacks[stack_name]))



    # send devel tests to Hudson
    finished = False
    while not finished:
        devel_configs_todo = {}
        for job_name in devel_configs:
            exists = hudson_instance.job_exists(job_name)
            if exists and hudson_instance.job_is_running(job_name):
                print "Not reconfiguring running job %s because it is still running"%job_name
                devel_configs_todo[job_name] = devel_configs[job_name]
                continue

            # delete old job
            if options.delete:
                if exists:
                    hudson_instance.delete_job(job_name)
                    print "Deleting job %s"%job_name

            # reconfigure job
            elif exists:
                hudson_instance.reconfig_job(job_name, devel_configs[job_name])
                print "Reconfigure job %s"%job_name

            # create job
            elif not exists:
                hudson_instance.create_job(job_name, devel_configs[job_name])
                print "Creating new job %s"%job_name

        if options.wait and len(devel_configs_todo) > 0:
            devel_configs = devel_configs_todo
            devel_configs_todo = {}
            time.sleep(10.0)
        else:
            finished = True


if __name__ == '__main__':
    main()





#!/usr/bin/python

# template to create develop hudscon configuration file
HUDSON_RELEASED_CONFIG = """<?xml version='1.0' encoding='UTF-8'?>
<project> 
  <description>Build of ROSDISTRO released code for on UBUNTUDISTRO, ARCH</description> 
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
  <scm class="hudson.scm.SubversionSCM"> 
    <locations> 
      <hudson.scm.SubversionSCM_-ModuleLocation> 
        <remote>ROSDISTROURI</remote> 
        <local>ROSDISTRO</local> 
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
  <assignedNode>hudson-devel</assignedNode>
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

wget -m -nd http://code.ros.org/svn/ros/installers/trunk/hudson/hudson_helper 
chmod +x hudson_helper
svn co https://code.ros.org/svn/ros/stacks/ros_release/trunk ros_release
./ros_release/job_generation/src/job_generation/run_auto_stack_released.py --rosdistro ROSDISTRO
echo "_________________________________END SCRIPT_______________________________________"
DELIM

set -o errexit

rm -rf $WORKSPACE/test_results
rm -rf $WORKSPACE/test_output

wget https://code.ros.org/svn/ros/stacks/ros_release/trunk/hudson/scripts/run_chroot.py --no-check-certificate -O $WORKSPACE/run_chroot.py
chmod +x $WORKSPACE/run_chroot.py
cd $WORKSPACE &amp;&amp; $WORKSPACE/run_chroot.py --distro=UBUNTUDISTRO --arch=ARCH  --ramdisk --script=$WORKSPACE/script.sh
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
from roslib2 import distro
from jobs_common import *
import hudson
import sys
import re
import urllib
import optparse 


def released_job_name(rosdistro, ubuntu, arch):
    return "_".join(['released', rosdistro, ubuntu, arch])



def create_released_configs(rosdistro, stack_map):
    # create gold distro
    gold_job = released_job_name(rosdistro, UBUNTU_DISTRO_MAP[rosdistro][0], ARCHES[0])
    gold_children = [released_job_name(rosdistro, u, a)
                     for a in ARCHES for u in UBUNTU_DISTRO_MAP[rosdistro]]
    gold_children.remove(gold_job)

    # create hudson config files for each ubuntu distro
    configs = {}
    for ubuntudistro in UBUNTU_DISTRO_MAP[rosdistro]:
        for arch in ARCHES:
            name = released_job_name(rosdistro, ubuntudistro, arch)

            # check if this is the 'gold' job
            time_trigger = ''
            job_children = ''
            if name == gold_job:
                time_trigger = '*/5 * * * *'
                job_children = ', '.join(gold_children)

            hudson_config = HUDSON_RELEASED_CONFIG
            hudson_config = hudson_config.replace('UBUNTUDISTRO', ubuntudistro)
            hudson_config = hudson_config.replace('ARCH', arch)
            hudson_config = hudson_config.replace('ROSDISTROURI', ROSDISTRO_FOLDER_MAP[rosdistro])
            hudson_config = hudson_config.replace('ROSDISTRO', rosdistro)
            hudson_config = hudson_config.replace('TIME_TRIGGER', time_trigger)
            hudson_config = hudson_config.replace('JOB_CHILDREN', job_children)
            hudson_config = hudson_config.replace('EMAIL', 'wim+hudson_auto_stack@willowgarage.com')
            configs[name] = hudson_config
    return configs

    
    

def main():
    parser = optparse.OptionParser()
    parser.add_option('--delete', dest = 'delete', default=False, action='store_true',
                      help='Delete jobs from Hudson')    
    parser.add_option('--rosdistro', dest = 'rosdistro', action='store', default='cturtle',
                      help="Specify the ros distro to operate on (defaults to cturtle)")
    (options, args) = parser.parse_args()

    # Parse distro file
    distro_obj = distro.Distro(ROSDISTRO_MAP[options.rosdistro])
    print 'Operating on ROS distro %s'%distro_obj.release_name

    # parse username and password
    if len(args) == 2:
        username = args[0]
        password = args[1]
    else:
        url = urllib.urlopen('http://wgs24.willowgarage.com/hudson-html/hds.xml')
        info = url.read().split(',')
        username = info[0]
        password = info[1]

    # generate hudson config files
    released_configs = create_released_configs(distro_obj.release_name, distro_obj.stacks)
    hudson_instance = hudson.Hudson(SERVER, username, password)


    # send devel tests to Hudson
    for job_name in released_configs:
        print job_name
        exists = hudson_instance.job_exists(job_name)
        
        # delete old job
        if options.delete:
            if exists:
                hudson_instance.delete_job(job_name)
                print "Deleting job %s"%job_name

        # reconfigure job
        elif exists:
            hudson_instance.reconfig_job(job_name, released_configs[job_name])
            print "Reconfigure job %s"%job_name

        # create job
        elif not exists:
            hudson_instance.create_job(job_name, released_configs[job_name])
            print "Creating new job %s"%job_name

if __name__ == '__main__':
    main()





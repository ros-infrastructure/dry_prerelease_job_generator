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

# template to create gazebo hudson configuration file
HUDSON_GAZEBO_CONFIG = """<?xml version='1.0' encoding='UTF-8'?>
<project> 
  <description>Gazebo build of NAME for ROSDISTRO on UBUNTUDISTRO, ARCH</description> 
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
  <assignedNode>gazebo</assignedNode>
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
run_auto_stack_gazebo.py --rosdistro ROSDISTRO
echo "_________________________________END SCRIPT_______________________________________"
DELIM

set -o errexit

rm -rf $WORKSPACE/test_results
rm -rf $WORKSPACE/test_output

wget  --no-check-certificate https://code.ros.org/svn/ros/stacks/ros_release/trunk/hudson/scripts/run_chroot.py -O $WORKSPACE/run_chroot.py
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

from job_generation.jobs_common import *
import jenkins
import urllib
import optparse 
import yaml

def gazebo_job_name(distro_name, rosinstall, ubuntudistro, arch):
    return "_".join(['gazebo', distro_name, rosinstall.split('/')[-1].split('.')[0], ubuntudistro, arch])


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



def create_gazebo_configs(distro_name, rosinstall):
    # create gold distro
    gold_job = gazebo_job_name(distro_name, rosinstall, UBUNTU_DISTRO_MAP[distro_name][0], ARCHES[0])
    gold_children = [gazebo_job_name(distro_name, rosinstall, u, a)
                     for a in ARCHES for u in UBUNTU_DISTRO_MAP[distro_name]]
    gold_children.remove(gold_job)

    # create hudson config files for each ubuntu distro
    configs = {}
    for ubuntudistro in UBUNTU_DISTRO_MAP[distro_name]:
        for arch in ARCHES:
            name = gazebo_job_name(distro_name, rosinstall, ubuntudistro, arch)

            # check if this is the 'gold' job
            time_trigger = ''
            job_children = ''
            if name == gold_job:
                time_trigger = '*/5 * * * *'
                job_children = ', '.join(gold_children)

            hudson_config = HUDSON_GAZEBO_CONFIG
            hudson_config = hudson_config.replace('BOOTSTRAP_SCRIPT', BOOTSTRAP_SCRIPT)
            hudson_config = hudson_config.replace('UBUNTUDISTRO', ubuntudistro)
            hudson_config = hudson_config.replace('ARCH', arch)
            hudson_config = hudson_config.replace('ROSDISTRO', distro_name)
            hudson_config = hudson_config.replace('HUDSON_VCS', rosinstall_to_vcs(rosinstall))
            hudson_config = hudson_config.replace('TIME_TRIGGER', time_trigger)
            hudson_config = hudson_config.replace('JOB_CHILDREN', job_children)
            hudson_config = hudson_config.replace('EMAIL', 'wim+gazebo@willowgarage.com')
            configs[name] = hudson_config
    return configs
    
    

def main():
    parser = optparse.OptionParser()
    parser.add_option('--delete', dest = 'delete', default=False, action='store_true',
                      help='Delete jobs from Hudson')    
    parser.add_option('--rosinstall', dest = 'rosinstall', action='store',
                      help="Specify the rosinstall file that refers to gazebo code.")
    parser.add_option('--rosdistro', dest = 'distro_name', action='store',
                      help="Specify the ros distro to operate on (defaults to cturtle)")
    (options, args) = parser.parse_args()
    if not options.distro_name:
        print 'Please provide the ros distro you want to test: --rosdistro cturtle'
        return
    if not options.distro_name in UBUNTU_DISTRO_MAP.keys():
        print 'You profided an invalid "--rosdistro %s" argument. Options are %s'%(options.distro_name, UBUNTU_DISTRO_MAP.keys())
        return
    if not options.rosinstall:
        print 'Please provide the rosinstall of gazebo code to test: --rosinstall foo.rosinstall'
        return
        

    # hudson instance
    info = urllib.urlopen(CONFIG_PATH).read().split(',')
    hudson_instance = jenkins.Jenkins(SERVER, info[0], info[1])

    # send gazebo tests to Hudson
    print 'Creating gazebo Hudson jobs:'
    gazebo_configs = create_gazebo_configs(options.distro_name, options.rosinstall)

    for job_name in gazebo_configs:
        exists = hudson_instance.job_exists(job_name)

        # delete job
        if options.delete and exists:
            print "Deleting job %s"%job_name
            hudson_instance.delete_job(job_name)

        # reconfigure job
        elif exists:
            print "  - %s"%job_name
            hudson_instance.reconfig_job(job_name, gazebo_configs[job_name])

        # create job
        elif not exists:
            print "  - %s"%job_name
            hudson_instance.create_job(job_name, gazebo_configs[job_name])



if __name__ == '__main__':
    main()





#!/usr/bin/python



# template to create openni hudson configuration file
HUDSON_OPENNI_CONFIG = """<?xml version='1.0' encoding='UTF-8'?>
<project> 
  <description>Openni build of NAME on UBUNTUDISTRO, ARCH</description> 
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

cd /tmp/  # not /tmp/ros to avoid 
hg clone https://kforge.ros.org/openni/drivers 

cd drivers

#./run_chroot.py --arch=ARCH --distro=UBUNTUDISTRO --workspace . --script local_script.bash --ramdisk
./local_script.bash

#move output into workspace
cp -r UBUNTUDISTRO /tmp/ros
cp add_debs.py /tmp/ros

echo "_________________________________END SCRIPT_______________________________________"
DELIM

set -o errexit

rm -rf $WORKSPACE/test_results
rm -rf $WORKSPACE/test_output

wget  --no-check-certificate https://code.ros.org/svn/ros/stacks/ros_release/trunk/hudson/scripts/run_chroot.py -O $WORKSPACE/run_chroot.py
chmod +x $WORKSPACE/run_chroot.py
cd $WORKSPACE &amp;&amp; $WORKSPACE/run_chroot.py --distro=UBUNTUDISTRO --arch=ARCH  --ramdisk --script=$WORKSPACE/script.sh --ssh-key-file=/home/rosbuild/rosbuild-ssh.tar


echo "copying debians to server"

scp -r $WORKSPACE/UBUNTUDISTRO rosbuild@pub8:/tmp/
scp $WORKSPACE/add_debs.py rosbuild@pub8:/tmp

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
      <defaultContent>$DEFAULT_CONTENT</defaultContent> 
      <defaultContentTypeHTML>false</defaultContentTypeHTML> 
      <defaultContentIsScript>true</defaultContentIsScript> 
    </hudson.plugins.emailext.ExtendedEmailPublisher> 
  </publishers> 
  <buildWrappers/> 
</project>
"""

import roslib; roslib.load_manifest("job_generation")
from job_generation.jobs_common import *
import jenkins
import urllib
import optparse 
import yaml


def openni_job_name(ubuntudistro, arch):
    return "_".join(['openni_driver_debs', ubuntudistro, arch])


def create_openni_configs():
    # create gold distro
    gold_job = openni_job_name(UBUNTU_DISTRO_MAP['diamondback'][0], ARCHES[0])
    # distros for diamondback and unstable
    distros = set(UBUNTU_DISTRO_MAP['diamondback'])
    distros.update(UBUNTU_DISTRO_MAP['unstable'])

    gold_children = [openni_job_name(u, a)
                     for a in ARCHES for u in distros]
    gold_children.remove(gold_job)

    # create hudson config files for each ubuntu distro
    configs = {}
    for ubuntudistro in distros:
        for arch in ARCHES:
            name = openni_job_name(ubuntudistro, arch)

            # check if this is the 'gold' job
            time_trigger = ''
            job_children = ''
            if name == gold_job:
                time_trigger = '*/5 * * * *'
                job_children = ', '.join(gold_children)

            hudson_config = HUDSON_OPENNI_CONFIG
            hudson_config = hudson_config.replace('UBUNTUDISTRO', ubuntudistro)
            hudson_config = hudson_config.replace('ARCH', arch)
            hudson_config = hudson_config.replace('TIME_TRIGGER', time_trigger)
            hudson_config = hudson_config.replace('JOB_CHILDREN', job_children)
            hudson_config = hudson_config.replace('EMAIL', 'tfoote+openni_debs@willowgarage.com')
            configs[name] = hudson_config
    return configs
    
    


def main():
    parser = optparse.OptionParser()
    parser.add_option('--delete', dest = 'delete', default=False, action='store_true',
                      help='Delete jobs from Hudson')    
    (options, args) = parser.parse_args()
        

    # hudson instance
    info = urllib.urlopen(CONFIG_PATH).read().split(',')
    hudson_instance = jenkins.Jenkins(SERVER, info[0], info[1])

    # send openni tests to Hudson
    print 'Creating openni Hudson jobs:'
    openni_configs = create_openni_configs()

    for job_name in openni_configs:
        exists = hudson_instance.job_exists(job_name)

        # delete job
        if options.delete and exists:
            print "Deleting job %s"%job_name
            hudson_instance.delete_job(job_name)

        # reconfigure job
        elif exists:
            print "  - %s"%job_name
            hudson_instance.reconfig_job(job_name, openni_configs[job_name])

        # create job
        elif not exists:
            print "  - %s"%job_name
            hudson_instance.create_job(job_name, openni_configs[job_name])



if __name__ == '__main__':
    main()





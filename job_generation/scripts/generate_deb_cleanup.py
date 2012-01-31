#!/usr/bin/python



# template to create aptcachecleanup hudson configuration file
HUDSON_APTCACHECLEANUP_CONFIG = """<?xml version='1.0' encoding='UTF-8'?>
<project> 
  <description>aptcache cleanup for MACHINEID</description> 
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
  <assignedNode>MACHINEID</assignedNode>
  <canRoam>false</canRoam> 
  <disabled>false</disabled> 
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding> 
  <triggers class="vector"> 
    <hudson.triggers.TimerTrigger> 
      <spec>TIME_TRIGGER</spec> 
    </hudson.triggers.TimerTrigger> 
  </triggers> 
  <concurrentBuild>false</concurrentBuild> 
  <builders> 
    <hudson.tasks.Shell> 
      <command>cat &gt; $WORKSPACE/script.py &lt;&lt;DELIM
#!/usr/bin/env python

import os
import shutil

def get_dir_size(start_path):
    if not os.path.isdir(path):
        return 0
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)

    return total_size

distros = ['jaunty', 'karmic', 'lucid', 'maverick', 'natty']
arches = ['i386', 'amd64']

for d in distros:
    for a in arches:
        path = os.path.join('/home/rosbuild/aptcache', '%s-%s'%(d,a))
        gigs = get_dir_size(path)/1024/1024/1024.0
        print path, gigs
        if gigs > 5.0: # if more than 5 gigs used clear it
            print "deleting %s"%path
            shutil.rmtree(path) # destroy whole tree 
            os.makedirs(path) #restore empty directory after deleting it


DELIM

set -o errexit

python $WORKSPACE/script.py
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

from job_generation.jobs_common import *
import jenkins
import urllib
import optparse 
import yaml

MACHINEIDS = ['bf1', 'bf2', 'bf3', 'bf4-wgsf6', 'bf5-wgsf7']

def aptcachecleanup_job_name(machineid):
    return "-".join(['debbuild-aptcachecleanup', machineid])


def create_aptcachecleanup_configs():

    # create hudson config files for each ubuntu distro
    configs = {}
    for machine in MACHINEIDS:
            name = aptcachecleanup_job_name(machine)

            time_trigger = '1 2 * * *' #0201 every night
            job_children = ''

            hudson_config = HUDSON_APTCACHECLEANUP_CONFIG
            hudson_config = hudson_config.replace('TIME_TRIGGER', time_trigger)
            hudson_config = hudson_config.replace('JOB_CHILDREN', job_children)
            hudson_config = hudson_config.replace('MACHINEID', machine)
            hudson_config = hudson_config.replace('EMAIL', 'tfoote+aptcachecleanup_debs@willowgarage.com')
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

    # send aptcachecleanup tests to Hudson
    print 'Creating aptcachecleanup Hudson jobs:'
    aptcachecleanup_configs = create_aptcachecleanup_configs()

    for job_name in aptcachecleanup_configs:
        exists = hudson_instance.job_exists(job_name)

        # delete job
        if options.delete and exists:
            print "Deleting job %s"%job_name
            hudson_instance.delete_job(job_name)

        # reconfigure job
        elif exists:
            print "  - %s"%job_name
            hudson_instance.reconfig_job(job_name, aptcachecleanup_configs[job_name])

        # create job
        elif not exists:
            print "  - %s"%job_name
            hudson_instance.create_job(job_name, aptcachecleanup_configs[job_name])



if __name__ == '__main__':
    main()





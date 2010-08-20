#!/usr/bin/python



# template to create develop hudscon configuration file
HUDSON_DEVEL_CONFIG = """<?xml version='1.0' encoding='UTF-8'?>
<project> 
  <description>Build of STACKNAME development branch for ROSDISTRO on UBUNTUDISTRO</description> 
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
  <assignedNode>label-build-farm-chroot</assignedNode>
  <canRoam>false</canRoam> 
  <disabled>false</disabled> 
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding> 
  <triggers class="vector"/> 
  <concurrentBuild>false</concurrentBuild> 
  <builders> 
    <hudson.tasks.Shell> 
      <command>
#!/bin/bash
set -o errexit
wget http://code.ros.org/svn/ros/installers/trunk/hudson/hudson_helper
if [ ! -f /etc/apt/sources.list.d/ros-latest.list ]; then
  sudo sh -c 'echo "deb http://code.ros.org/packages/ros/ubuntu UBUNTUDISTRO main" > /etc/apt/sources.list.d/ros-latest.list'
  wget http://code.ros.org/packages/ros.key -O - | sudo apt-key add -
fi
sudo apt-get update
yes | sudo apt-get install ros-ROSDISTRO-STACKPACKAGENAME 
export ROS_PACKAGE_PATH=/opt/ros/ROSDISTRO/stacks
export ROS_ROOT=/opt/ros/ROSDISTRO/ros
export ROS_TEST_RESULTS_DIR=`pwd`/test-results/
chmod +x hudson_helper
./hudson_helper --dir-test STACKNAME build
DELIM


wget http://code.ros.org/svn/ros/installers/trunk/hudson/run_chroot.py --no-check-certificate -O $WORKSPACE/run_chroot.py
chmod +x $WORKSPACE/run_chroot.py
cd $WORKSPACE &amp;&amp; $WORKSPACE/run_chroot.py --distro=UBUNTUDISTRO --arch=amd64  --persist-chroot --script=$WORKSPACE/script.sh
     </command> 
    </hudson.tasks.Shell> 
  </builders> 
  <publishers/>
  <buildWrappers/> 
</project>
"""


# template to create pre-release hudson configuration file
HUDSON_PRERELEASE_CONFIG = """
# install all debians
sudo apt-get install ros-ROSDISTRO-pr2all

# overlay with stacks that depend on the stack we are testing
rosinstall /opt/ros/ROSDISTRO /tmp/ros/ROSDISTRO_STACKNAME_depends-on.rosinstall'

# the development uri of this stack
STACKURI

# the ubuntu distro
UBUNTUDISTRO
"""

# template to create rosinstall file
ROSINSTALL_CONFIG = """
- svn:
    uri: STACKURI
    local-name: STACKNAME
"""

# the supported Ubuntu distro's for each ros distro
UBUNTU_DISTROS = {'cturtle':['lucid', 'karmic'],
                  'boxturtle':['hardy','karmic']}


SERVER      = 'http://build.willowgarage.com/'

import roslib; roslib.load_manifest("hudson")
from roslib import distro
from roslib import rospack
import hudson
import sys



def create_devel_configs(distro_name, stack_name, stack_map):
    # create hudson config files for each ubuntu distro
    configs = {}
    for ubuntu in UBUNTU_DISTROS[distro_name]:
        name = "stack_devel_"+ubuntu+'_'+distro_name+'_'+stack_name
        hudson_config = HUDSON_DEVEL_CONFIG
        hudson_config = hudson_config.replace('UBUNTUDISTRO', ubuntu)
        hudson_config = hudson_config.replace('ROSDISTRO', distro_name)
        hudson_config = hudson_config.replace('STACKNAME', stack_name)   
        hudson_config = hudson_config.replace('STACKPACKAGENAME', stack_name.replace('_','-'))   
        hudson_config = hudson_config.replace('STACKURI', stack_map[stack_name].dev_svn)    
        configs[name] = hudson_config
    return configs


def create_prerelease_configs(distro_name, stack_name, stack_map):
    # create rosinstall file with all stacks that depend on this stack
    rosinstall = ""+distro_name+"_"+stack_name+"_depends-on.rosinstall"
    rosinstall_config_total = ""
    for s in rospack.rosstack_depends_on(stack_name):
        if s in stack_map:
            rosinstall_config = ROSINSTALL_CONFIG
            rosinstall_config = rosinstall_config.replace('STACKURI', stack_map[s].distro_svn)
            rosinstall_config = rosinstall_config.replace('STACKNAME', s)
            rosinstall_config_total += rosinstall_config
    f = open(rosinstall, "w")
    f.write(rosinstall_config_total)
    f.close()


    # create hudson config files for each ubuntu distro
    for ubuntu in UBUNTU_DISTROS[distro_name]:
        hudson = 'stack_prerelease_'+ubuntu+'_'+distro_name+'_'+stack_name+'.xml'
        hudson_config = HUDSON_PRERELEASE_CONFIG
        hudson_config = hudson_config.replace('UBUNTUDISTRO', ubuntu)
        hudson_config = hudson_config.replace('ROSDISTRO', distro_name)
        hudson_config = hudson_config.replace('STACKNAME', stack_name)      
        hudson_config = hudson_config.replace('STACKURI', stack_map[stack_name].dev_svn)
        f = open(hudson, "w")
        f.write(hudson_config)
        f.close()
    
def main():
    distro_file = 'http://www.ros.org/distros/cturtle.rosdistro'
    if len(sys.argv) == 4:
        distro_file = sys.argv[3]
        
    username = password = None
    if len(sys.argv) == 3:
        username = sys.argv[1]
        password = sys.argv[2]

    # generate hudson config files
    distro_obj = distro.Distro(distro_file)
    devel_configs = {}
    for stack_name in distro_obj.stacks:
        devel_configs.update(create_devel_configs(distro_obj.release_name, stack_name, distro_obj.stacks))
        #create_prerelease_configs(distro_obj.release_name, stack_name, distro_obj.stacks)

    # send tests to Hudson
    print "Username %s,  Password %s"%(username, password)
    hudson_instance = hudson.Hudson(SERVER, username, password)
    for job_name in devel_configs:
        if job_name.find('geometry') != -1:
            print devel_configs[job_name]
            if hudson_instance.job_exists(job_name):
                hudson_instance.delete_job(job_name)
                print "Deleting job %s"%job_name
            print "Creating new job %s"%job_name
            hudson_instance.create_job(job_name, devel_configs[job_name])
            return


if __name__ == '__main__':
    main()





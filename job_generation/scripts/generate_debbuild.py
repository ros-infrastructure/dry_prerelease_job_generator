#!/usr/bin/python

HUDSON_DEBBUILD_CONFIG = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <actions/>
  <description>Trigger for building source debs</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>STACK_NAME</name>
          <description>ROS stack name</description>
          <defaultValue>ALL</defaultValue>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <scm class="hudson.scm.SubversionSCM">
    <locations>
      <hudson.scm.SubversionSCM_-ModuleLocation>
        <remote>https://code.ros.org/svn/release/trunk</remote>
        <local>release</local>
      </hudson.scm.SubversionSCM_-ModuleLocation>
      <hudson.scm.SubversionSCM_-ModuleLocation>
        <remote>https://code.ros.org/svn/ros/stacks/ros_release/trunk</remote>
        <local>ros_release</local>
      </hudson.scm.SubversionSCM_-ModuleLocation>
    </locations>
    <useUpdate>true</useUpdate>
    <doRevert>false</doRevert>
    <excludedRegions/>
    <includedRegions/>
    <excludedUsers/>
    <excludedRevprop/>
    <excludedCommitMessages/>
  </scm>
  <assignedNode>hudson-devel</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <authToken>RELEASE_BUILD_DEBS</authToken>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>echo %(distro_name)s
echo $STACK_NAME
echo %(osdistro)s
echo %(arch)s

sudo apt-get install pbuilder git-core -y qemu-kvm-extras-static

cat &gt; $WORKSPACE/build.bash &lt;&lt; DELIM
source /opt/ros/cturtle/setup.sh
export ROS_PACKAGE_PATH=$WORKSPACE/ros_release:$WORKSPACE/release:$ROS_PACKAGE_PATH

rosrun rosdeb build_debs.py %(distro_name)s $STACK_NAME %(osdistro)s %(arch)s --force --besteffort
DELIM

bash $WORKSPACE/build.bash</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers>
    <hudson.tasks.BuildTrigger>
      <childProjects>debbuild-status</childProjects>
      <threshold>
        <name>SUCCESS</name>
        <ordinal>0</ordinal>
        <color>BLUE</color>
      </threshold>
    </hudson.tasks.BuildTrigger>
    <hudson.tasks.Mailer>
      <recipients/>
      <dontNotifyEveryUnstableBuild>true</dontNotifyEveryUnstableBuild>
      <sendToIndividuals>false</sendToIndividuals>
    </hudson.tasks.Mailer>
  </publishers>
  <buildWrappers/>
</project>

"""

from job_generation.jobs_common import *
import optparse

def debbuild_job_name(distro_name, ubuntu, arch):
    return "-".join(["debbuild-build-debs", distro_name, ubuntu, arch])

def create_debbuild_configs(osdistro, distro_name, arch):
    # create hudson config files for each ubuntu distro
    configs = {}
    name = debbuild_job_name(distro_name, osdistro, arch)
    
    hudson_config = HUDSON_DEBBUILD_CONFIG
    
    configs[name] = hudson_config%{'osdistro':osdistro, 'rosdistro':distro_name, 'arch':arch}
    return configs

usage_str = "usage: %prog --rosdistro ROSDISTRO [--architecture ARCH ] [--os OS_CODENAME] [--delete] [--nowait]"

def main():
    parser = optparse.OptionParser(usage=usage_str)
    parser.add_option('--rosdistro', action='store', dest='distro_name', help='which distro to use')
    parser.add_option('--architecture', action='append', dest='arch', help='Architecture to target')
    parser.add_option('--codename', action='append', dest='codename', help='Codename to target')
    parser.add_option('--wait', action='store_true', dest='wait', default=False, help='Wait for running jobs to finish, instead of skipping')
    parser.add_option('--delete', action='store_true', dest='delete', default=False, help='Delete the specified job')

    (options, args) = parser.parse_args()
    if not options.distro_name:
        parser.parse_error("--rosdistro required")
    if options.distro_name:
        distro_name_list = [options.distro_name]

    os_list = ['lucid', 'maverick', 'natty']
    arch_list = ['i386', 'amd64', 'armel']

    if options.codename:
        os_list = options.codename
    if options.arch:
        arch_list = options.arch
    
    print os_list, arch_list, distro_name_list

    debbuild_configs = {}
    for distro_name in distro_name_list:
        for arch in arch_list:
            for o in os_list:
                debbuild_configs.update(create_debbuild_configs(o, distro_name, arch))
                
    # schedule jobs
    print "Scheduling updates"
    schedule_jobs(debbuild_configs, options.wait, options.delete)


if __name__ == '__main__':
    main()





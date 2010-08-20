#!/usr/bin/env python

import roslib; roslib.load_manifest("hudson")
import sys
import hudson

SERVER     = 'http://build.willowgarage.com/'
#SERVER     = 'http://localhost:8080/'

JOB_INFO    = 'job/%(name)s/api/python?depth=0'
Q_INFO      = 'queue/api/python?depth=0'
CREATE_JOB  = 'createItem?name=%(name)s' #also post config.xml
DELETE_JOB  = 'job/%(name)s/doDelete'
DISABLE_JOB = 'job/%(name)s/disable'
COPY_JOB    = 'createItem?name=%(to_name)s&mode=copy&from=%(from_name)s'
BUILD_JOB   = 'job/%(name)s/build'
BUILD_WITH_PARAMS_JOB = 'job/%(name)s/buildWithParameters'

#for testing only
EMPTY_CONFIG_XML = """<?xml version='1.0' encoding='UTF-8'?>
<project>
  <description>A test build </description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>"""

    
def main():
    if len(sys.argv) == 4:
        username = sys.argv[1]
        password = sys.argv[2]
    elif len(sys.argv) == 1:
        username = password = None
    else:
        if len(sys.argv) != 4:
            print "Usage: job_generator.py [username] [password] stack"
            sys.exit(1)

    hudson_instance = hudson.Hudson(SERVER, username, password)
    job_name = sys.argv[3]+"_auto_trunk_test"
    

    if hudson_instance.job_exists(job_name):
        hudson_instance.delete_job(job_name)
    hudson_instance.create_job(job_name, EMPTY_CONFIG_XML)
    #else:
    #    hudson_instance.build_job('api-test', {'param1': 'test value 1', 'param2': 'http://ros.org/wiki/distros/cturtle.rosdistro'})
    
if __name__ == '__main__':
    main()


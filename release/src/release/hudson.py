#!/usr/bin/env python
import sys
import urllib2
import base64
import traceback

#SERVER     = 'http://build.willowgarage.com/'
SERVER     = 'http://localhost:8080/'

JOB_INFO   = SERVER + 'job/%(name)s/api/python?depth=0'
Q_INFO     = SERVER + 'queue/api/python?depth=0'
CREATE_JOB  = SERVER + 'createItem?name=%(name)s' #also post config.xml
DELETE_JOB  = SERVER + 'job/%(name)s/doDelete'
DISABLE_JOB = SERVER + 'job/%(name)s/disable'
COPY_JOB   = SERVER + 'createItem?name=%(to_name)s&mode=copy&from=%(from_name)s'

XML = """<?xml version='1.0' encoding='UTF-8'?>
<project>
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

class HudsonException(Exception): pass

def get_job_info(name):
    try:
        return eval(urllib2.urlopen(JOB_INFO%locals()).read())
    except:
        raise HudsonException("job[%s] does not exist"%name)
        
def debug_job_info(job_name):
    for k, v in get_job_info(job_name).iteritems():
        print k, v

def hudson_open(req, auth=None):
    try:
        if auth:
            req.add_header('Authorization', auth)
        return urllib2.urlopen(req).read()
    except urllib2.HTTPError, e:
        if e.code in [401, 403, 500]:
            raise HudsonException("authentication failed [%s]"%(e.code))
        # right now I'm getting 302 infinites on a successful delete
    
def get_queue_info():
    """
    @return: list of job dictionaries
    """
    return eval(urllib2.urlopen(Q_INFO).read())['items']

def copy_job(from_name, to_name, auth):
    get_job_info(from_name)
    hudson_open(urllib2.Request(COPY_JOB%locals(), ''), auth)
    if not job_exists(to_name):
        raise HudsonException("create[%s] failed"%(to_name))

def delete_job(name, auth):
    get_job_info(name)
    hudson_open(urllib2.Request(DELETE_JOB%locals(), ''), auth)
    if job_exists(name):
        raise HudsonException("delete[%s] failed"%(name))
    
def job_exists(name):
    try:
        get_job_info(name)
        return True
    except:
        return False
    
def create_job(name, auth):
    if job_exists(name):
        raise HudsonException("job[%s] already exists"%name)

    url = CREATE_JOB%locals()
    config_xml = XML

    headers = {'Content-Type': 'text/xml'}
    hudson_open(urllib2.Request(url, config_xml, headers), auth)
    if not job_exists(name):
        raise HudsonException("create[%s] failed"%(name))
    
def auth_headers(username, password):
    return 'Basic ' + base64.encodestring("%s:%s" % (username, password))[:-1]

def main():
    if len(sys.argv) == 3:
        username = sys.argv[1]
        password = sys.argv[2]
        auth = auth_headers(username, password)
    elif len(sys.argv) == 1:
        auth = None
    else:
        if len(sys.argv) != 3:
            print "Usage: hudson.py [username] [password]"
            sys.exit(1)
    
    if 0:
        create_job('empty', auth)
        copy_job('empty', 'empty_copy', auth)

    if 1:
        delete_job('empty', auth)
        delete_job('empty_copy', auth)
    
if __name__ == '__main__':
    main()


#!/usr/bin/env python
import sys
import urllib2
import urllib
import base64
import traceback

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

def auth_headers(username, password):
    """
    Simple implementation of HTTP Basic Authentication. Returns the 'Authentication' header value.
    """
    return 'Basic ' + base64.encodestring("%s:%s" % (username, password))[:-1]

class Hudson(object):
    
    def __init__(self, url, username, password):
        if url[-1] == '/':
            self.server = url
        else:
            self.server = url + '/'            
        self.auth = auth_headers(username, password)
        
    def get_job_info(self, name):
        try:
            return eval(urllib2.urlopen(self.server + JOB_INFO%locals()).read())
        except:
            raise HudsonException("job[%s] does not exist"%name)
        
    def debug_job_info(self, job_name):
        for k, v in self.get_job_info(job_name).iteritems():
            print k, v

    def hudson_open(self, req):
        try:
            if self.auth:
                req.add_header('Authorization', self.auth)
            return urllib2.urlopen(req).read()
        except urllib2.HTTPError, e:
            if e.code in [401, 403, 500]:
                raise HudsonException("authentication failed [%s]"%(e.code))
            # right now I'm getting 302 infinites on a successful delete
    
    def get_queue_info(self):
        """
        @return: list of job dictionaries
        """
        return eval(urllib2.urlopen(self.server + Q_INFO).read())['items']

    def copy_job(self, from_name, to_name):
        self.get_job_info(from_name)
        self.hudson_open(urllib2.Request(self.server + COPY_JOB%locals(), ''))
        if not self.job_exists(to_name):
            raise HudsonException("create[%s] failed"%(to_name))

    def delete_job(self, name):
        self.get_job_info(name)
        self.hudson_open(urllib2.Request(self.server + DELETE_JOB%locals(), ''))
        if self.job_exists(name):
            raise HudsonException("delete[%s] failed"%(name))
    
    def job_exists(self, name):
        try:
            self.get_job_info(name)
            return True
        except:
            return False

    def create_job(self, name, config_xml):
        """
        @param config_xml: config file text
        @type  config_xml: str
        """
        if self.job_exists(name):
            raise HudsonException("job[%s] already exists"%(name))

        headers = {'Content-Type': 'text/xml'}
        self.hudson_open(urllib2.Request(self.server + CREATE_JOB%locals(), config_xml, headers))
        if not self.job_exists(name):
            raise HudsonException("create[%s] failed"%(name))
    
    def build_job(self, name, parameters=None, token=None):
        """
        @param parameters: parameters for job, or None.
        @type  parameters: dict
        """
        if parameters:
            if token:
                parameters['token'] = token
            if not self.job_exists(name):
                raise HudsonException("no such job[%s]"%(name))
            url = self.server + BUILD_WITH_PARAMS_JOB%locals() + '?' + urllib.urlencode(parameters)
            # apparently we can also send JSON, but the Hudson docs on this are *very* inconsistent
            return self.hudson_open(urllib2.Request(url, ''))        
        else:
            if not self.job_exists(name):
                raise HudsonException("no such job[%s]"%(name))
            if token:
                req = urllib2.Request(self.server + BUILD_JOB%locals() + '?' + urllib.urlencode({'token': token}), '')
            else:
                req = urllib2.Request(self.server + BUILD_JOB%locals(), '')
            return self.hudson_open(req)
    
def main():
    if len(sys.argv) == 3:
        username = sys.argv[1]
        password = sys.argv[2]
    elif len(sys.argv) == 1:
        username = password = None
    else:
        if len(sys.argv) != 3:
            print "Usage: hudson.py [username] [password]"
            sys.exit(1)

    hudson = Hudson(SERVER, username, password)
    if 1:
        if 1:
            hudson.create_job('empty', EMPTY_CONFIG_XML)
            hudson.copy_job('empty', 'empty_copy')

        if 1:
            hudson.delete_job('empty')
            hudson.delete_job('empty_copy')
    else:
        hudson.build_job('api-test', {'param1': 'test value 1', 'param2': 'http://ros.org/wiki/distros/cturtle.rosdistro'})
    
if __name__ == '__main__':
    main()


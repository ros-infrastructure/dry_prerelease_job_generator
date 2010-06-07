#!/usr/bin/env python

# source code refers to 'stacks', but this can work with apps as well
from __future__ import with_statement
NAME="create_release.py"

import sys
import os
from subprocess import Popen, PIPE, call, check_call

import roslib.stacks
from roslib.scriptutil import ask_and_call

try:
    import yaml
except ImportError:
    print >> sys.stderr, "python-yaml not installed, cannot proceed"
    sys.exit(1)
    
class ReleaseException(Exception): pass

def load_sys_args():
    """
    @return: name, version, distro_file, distro_name
    @rtype: (str, str, str, str)
    """
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog <stack> <version> <release-file>", prog=NAME)
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error("""You must specify: 
 * stack name (e.g. common_msgs)
 * version (e.g. 1.0.1)
 * release file (e.g. latest.rosdistro)""")
    name, version, distro_file = args
    if not os.path.isfile(distro_file):
        parser.error("[%s] does not appear to be a valid file"%distro_file)
    return name, version, distro_file

def get_version(name, source_url):
    source_url = source_url + '/CMakeLists.txt'
    print "Reading version number from %s"%source_url

    import re
    import urllib2
    f = urllib2.urlopen(source_url)
    text = f.read()
    f.close()
    
    for l in text.split('\n'):
        if l.strip().startswith('rosbuild_make_distribution'):
            x_re = re.compile(r'[()]')
            lsplit = x_re.split(l.strip())
            if len(lsplit) < 2:
                raise ReleaseException("couldn't find version number in CMakeLists.txt:\n\n%s"%l)
            return lsplit[1]

def load_and_validate_properties():
    """
    @return: name, version, distro_file, source_dir, distro, release_props
    @rtype: (str, str, str, str, str, dict)
    """
    name, version, distro_file = load_sys_args()
    # for now, we only work with stacks
    try:
        source_dir = roslib.stacks.get_stack_dir(name)
    except:
        raise ReleaseException("cannot locate stack [%s]"%name)

    check_svn_status(source_dir)
    
    release_props = load_release_props(name, distro_file, source_dir)
    print_bold("Release Properties")
    for k, v in release_props.iteritems():
        print " * %s: %s"%(k, v)
    release = release_props['release']
    # figure out what we're releasing against
    print "Release target is [%s]"%release


    # brittle test to make sure that user got the args correct
    if not '.' in version:
        raise ReleaseException("hmm, [%s] doesn't look like a version number to me"%version)

    source_url = expand_uri(release_props['dev-svn'], name, version, release)
    cmake_version = get_version(name, source_url)
    if cmake_version != version:
        raise ReleaseException("version number in CMakeLists.txt appears to be incorrect:\n\n%s"%cmake_version)
    
    return name, version, distro_file, source_dir, release_props    

def load_release_props(name, distro_file, stack_dir):
    print "Loading uri rules from %s"%distro_file
    if not os.path.isfile(distro_file):
        raise ReleaseException("Cannot find [%s].\nPlease consult documentation on how to create this file"%p)
    with open(distro_file) as f:
        docs = [d for d in yaml.load_all(f.read())]
        if len(docs) != 1:
            raise ReleaseException("Found multiple YAML documents in [%s]"%distro_file)
        doc = docs[0]

    # there are two tiers of dictionaries that we look in for uri rules
    rules_d = [doc.get('stacks', {}),
               doc.get('stacks', {}).get(name, {})]
    rules_d = [d for d in rules_d if d]
    # load the '_rules' from the dictionaries, in order
    props = {}
    for d in rules_d:
        if type(d) == dict:
            props.update(d.get('_rules', {}))

    if not props:
        raise ReleaseException("[%s] is missing '_rules'. Please consult documentation"%(distro_file))
    
    if not 'release' in doc:
        raise ReleaseException("[%s] is missing 'release' key. Please consult documentation"%(distro_file))
    props['release'] = doc['release']

    for reqd in ['release-svn']:
        if not reqd in props:
            raise ReleaseException("[%s] is missing required key [%s]"%(distro_file, reqd))

    # add in some additional keys
    if not 'dev-svn' in props:
        from subprocess import Popen, PIPE
        output = Popen(['svn', 'info'], stdout=PIPE, cwd=stack_dir).communicate()[0]
        url_line = [l for l in output.split('\n') if l.startswith('URL:')]
        if url_line:
            props['dev-svn'] = url_line[0][4:].strip()
        else:
            raise ReleaseException("cannot determine SVN URL of stack [%s]"%name)
    
    return props

def update_rosdistro_yaml(name, version, distro_file):
    if not os.path.exists(distro_file):
        raise ReleaseException("[%s] does not exist"%distro_file)

    with open(distro_file) as f:
        d = [d for d in yaml.load_all(f.read())]
        if len(d) != 1:
            raise ReleaseException("found more than one release document in [%s]"%distro_file)
        d = d[0]

    distro_d = d
    if not 'stacks' in d:
        d['stacks'] = {}
    d = d['stacks']
    if not name in d:
        d[name] = {}
    d = d[name]
    # set the version key, assume not overriding properties
    d['version'] = str(version)

    print "Writing new release properties to [%s]"%distro_file
    with open(distro_file, 'w') as f:
        f.write(yaml.safe_dump(distro_d))
        
def main():
    try:
        props = load_and_validate_properties()
        name, version, distro_file, source_dir, release_props = props[:6]
        tarball = make_dist(name, version, source_dir, release_props)
        tag_urls = tag_subversion(name, version, release_props)
        update_rosdistro_yaml(name, version, distro_file)

        if tarball:
            copy_to_server(name, tarball)
        else:
            print_bold("cannot copy to server as tarball was not built")
        
        print """

Now:
 * update the changelist at http://www.ros.org/wiki/%s/ChangeList
 * email Ken to update ros.org/rosdistros
 * Checkin the rosdistro file."""%name
        
    except ReleaseException, e:
        print >> sys.stderr, "ERROR: %s"%str(e)
        sys.exit(1)

def copy_to_server(name, tarball):
    scp_target = os.environ.get('ROS_RELEASE_SCP', None)
    if scp_target is None:
        print "ROS_RELEASE_SCP is not set, will not upload tarball"
        return
    try:
        file_name = os.path.split(tarball)[1]
        dest = os.path.join(scp_target,name,file_name)
        cmds = [['scp', tarball, dest]]
        if not ask_and_call(cmds):    
            print "create_release will not copy the release tarball to the remote server"
    except:
        print >> sys.stderr, "COPY FAILED, please redo manually. The most likely cause is permissions or a missing directory."

def tag_subversion(name, version, release_props):
    urls = []
    release = release_props['release']
    for k in ['release-svn', 'distro-svn']:
        from_url = expand_uri(release_props['dev-svn'], name, version, release)
        tag_url = expand_uri(release_props[k], name, version, release)
        
        release_name = "%s-%s"%(name, version)

        cmds = []
        # delete old svn tag if it's present
        append_rm_if_exists(tag_url, cmds, 'Making room for new release')
        # svn cp command to create new tag
        cmds.append(['svn', 'cp', '--parents', '-m', 'Tagging %s new release'%release_name, from_url, tag_url])
        if not ask_and_call(cmds):    
            print "create_release will not create this tag in subversion"
        else:
            urls.append(tag_url)
    return urls
    
def print_bold(m):
    print '\033[1m%s\033[0m'%m    

def checkout_svn(name, uri):
    import tempfile
    tmp_dir = tempfile.mktemp()
    dest = os.path.join(tmp_dir, name)
    print 'Checking out a fresh copy of %s from %s to %s...'%(name, uri, dest)
    cmd = ['svn', 'co', uri, dest]
    check_call(cmd)
    return tmp_dir

def make_dist(name, version, source_dir, release_props):
    from_url = expand_uri(release_props['dev-svn'], name, version, release_props['release'])
    
    tmp_dir = checkout_svn(name, from_url)
    tmp_source_dir = os.path.join(tmp_dir, name)
    print 'Building a distribution for %s in %s'%(name, tmp_source_dir)
    cmd = ['make', 'package_source']
    try:
        check_call(cmd, cwd=tmp_source_dir)
    except:
        raise ReleaseException("unable to 'make package_source' in package. Most likely the Makefile and CMakeLists.txt files have not been checked in")
    tarball = "%s-%s.tar.bz2"%(name, version)
    import shutil
    src = os.path.join(tmp_source_dir, 'build', tarball)
    dst = os.path.join("/tmp", tarball)
    shutil.copyfile(src, dst)
    shutil.rmtree(tmp_dir)
    print_bold("Release should be in %s"%dst)
    return dst

def expand_uri(rule, stack_name, stack_ver, release_name):
  s = rule.replace('$STACK_NAME', stack_name)
  s =    s.replace('$STACK_VERSION', stack_ver)
  s =    s.replace('$RELEASE_NAME', release_name)
  return s

def check_svn_status(source_dir):
    """make sure that all outstanding code has been checked in"""
    cmd = ['svn', 'st', '-q']
    output = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=source_dir).communicate()
    if output[0]:
        raise ReleaseException("svn status in stack reported uncommitted files:\n%s"%output[0])
    if output[1]:
        raise ReleaseException("svn status in [%s] reported errors:\n%s"%(source_dir, output[0]))

def svn_url_exists(url):
    cmd = ['svn', 'ls', url]
    output = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
    return bool(output[0])

def append_rm_if_exists(url, cmds, msg):
    if svn_url_exists(url):
        cmds.append(['svn', 'rm', '-m', msg, url]) 

    
if __name__ == '__main__':
    main()

#!/usr/bin/env python

# source code refers to 'stacks', but this can work with apps as well
from __future__ import with_statement
NAME="wg_create_release.py"

import sys
import os
import os.path
from subprocess import Popen, PIPE, call, check_call
import traceback

import roslib.scriptutil
import roslib.stacks

print "WARNING: this script requires ROS *trunk*"

try:
    import yaml
except ImportError:
    print >> sys.stderr, "python-yaml not installed, cannot proceed"
    sys.exit(1)


def load_distro(distro_file):
    if not os.path.isfile(distro_file):
        raise ReleaseException("Cannot find [%s].\nPlease consult documentation on how to create this file"%p)
    with open(distro_file) as f:
        docs = [d for d in yaml.load_all(f.read())]
        if len(docs) != 1:
            raise ReleaseException("Found multiple YAML documents in [%s]"%distro_file)
        distro = docs[0]
    return distro

def load_stack_rules(distro, stack_name):
    # there are two tiers of dictionaries that we look in for uri rules
    rules_d = [distro.get('stacks', {}),
               distro.get('stacks', {}).get(stack_name, {})]
    rules_d = [d for d in rules_d if d]
    # load the '_rules' from the dictionaries, in order
    props = {}
    for d in rules_d:
        if type(d) == dict:
            props.update(d.get('_rules', {}))

    if not props:
        raise ReleaseException("[%s] is missing '_rules'. Please consult distroumentation"%(distro_file))
    
    if not 'release' in distro:
        raise ReleaseException("[%s] is missing 'release' key. Please consult documentation"%(distro_file))
    props['release'] = distro['release']

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
            raise ReleaseException("cannot determine SVN URL of stack [%s]"%stack_name)
    
    return props

def main():
    try:
        from optparse import OptionParser
        parser = OptionParser(usage="usage: %prog <release>", prog=NAME)
        options, args = parser.parse_args()
        if len(args) != 1:
            parser.error("""You must specify: 
 * release name""")
        release_name = args[0]
        if release_name.endswith('.rosdistro'):
            distro_file = release_name
            release_name = release_name[:-len('.rosdistro')]
        else:
            distro_file = "%s.rosdistro"%release_name
        print "distro file", distro_file
        print "release name", release_name

        if not os.path.isfile(distro_file):
            parser.error("[%s] does not appear to be a valid release, no corresponding .rosdistro file"%(release_name))

        # load in an expand URIs for rosinstalls
        distro = load_distro(distro_file)
        stack_props = distro['stacks']
        checkouts = {}
        for stack_name in sorted(stack_props.iterkeys()):
            if stack_name[0] == '_':
                continue
            rules = load_stack_rules(distro, stack_name)
            stack_version = stack_props[stack_name]['version']
            uri = expand_uri(rules['distro-svn'], stack_name, stack_version, release_name)
            checkouts[stack_name] = uri

        # create text for rosinstalls
        variant_rosinstalls = []
        variants = distro['variants']
        tmpl = """- svn:
    uri: %(uri)s
    local-name: %(local_name)s
"""
        #TODO: build_release has the Distro class that computes much of this

        variant_stacks = {}
        variant_stacks_extended = {}
        # create the ros-only variant
        local_name = 'ros'
        uri = checkouts['ros']
        variant_rosinstalls.append(('rosinstall/%s_ros.rosinstall'%release_name,tmpl%locals()))

        for variant_d in variants:
            variant = variant_d.keys()[0]
            variant_props = variant_d[variant]
            variant_stacks[variant] = variant_props['stacks']
            if 'extends' in variant_props:
                variant_stacks_extended[variant] = variant_stacks_extended[variant_props['extends']] + variant_props['stacks']
            else:
                variant_stacks_extended[variant] = variant_props['stacks']
                
            # create two rosinstalls per variant: 'extended' (non-overlay) and normal (overlay)
            text = ''

            local_name = 'ros'
            uri = checkouts['ros']
            text_extended = tmpl%locals()

            for stack_name in sorted(variant_stacks[variant]):
                uri = checkouts[stack_name]
                if stack_name == 'ros':
                    continue
                else:
                    local_name = "stacks/%s"%stack_name
                text += tmpl%locals()
                
            for stack_name in sorted(variant_stacks_extended[variant]):
                uri = checkouts[stack_name]
                if stack_name == 'ros':
                    continue
                else:
                    local_name = "stacks/%s"%stack_name
                text_extended += tmpl%locals()

            # create non-overlay rosinstall
            filename = os.path.join('rosinstall', '%s_%s.rosinstall'%(release_name, variant))
            variant_rosinstalls.append((filename, text_extended))

            # create variant overlay
            filename = os.path.join('rosinstall', '%s_%s_overlay.rosinstall'%(release_name, variant))
            variant_rosinstalls.append((filename, text))

        filename = os.path.join('rosinstall', '%s_wg_all.rosinstall'%(release_name))
        variant_rosinstalls.append((filename, create_wg_all(release_name, tmpl, checkouts)))
        
        # output rosinstalls
        for filename, text in variant_rosinstalls:
            with open(filename,'w') as f:
                f.write(text)
            copy_to_server(filename)

    except Exception, e:
        traceback.print_exc()
        print >> sys.stderr, "ERROR: %s"%str(e)
        sys.exit(1)

def create_wg_all(release_name, tmpl, checkouts):
    # create the wg_all rosinstall
    local_name = 'ros'
    if release_name == 'boxturtle':
        uri = 'https://code.ros.org/svn/ros/stacks/ros/branches/ros-1.0/'
    else:
        uri = checkouts['ros']
    text_extended = tmpl%locals()

    stack_names = sorted(checkouts.keys())
    for stack_name in stack_names:
        uri = checkouts[stack_name]
        if stack_name == 'ros':
            continue
        else:
            local_name = "stacks/%s"%stack_name
        text_extended += tmpl%locals()

    text_extended += """- svn:
    uri: https://code.ros.org/svn/wg-ros-pkg/trunk
    local-name: wg-ros-pkg-unreleased
- svn:
    uri: https://code.ros.org/svn/ros-pkg/trunk
    local-name: ros-pkg-unreleased
- svn:
    uri: https://code.ros.org/svn/ros/stacks/ros_experimental/trunk
    local-name: ros-experimental-trunk
"""
    return text_extended

def copy_to_server(filename):
    try:
        dest = os.path.join('wgs32:/var/www/www.ros.org/html/rosinstalls/%s'%os.path.basename(filename))
        cmds = [['scp', filename, dest]]
        if not roslib.scriptutil.ask_and_call(cmds):    
            print "create_rosinstall will not copy the rosinstall to wgs32"
    except:
        traceback.print_exc()
        print >> sys.stderr, "COPY FAILED, please redo manually"

#TODO: copied from create_release.py
def expand_uri(rule, stack_name, stack_ver, release_name):
  s = rule.replace('$STACK_NAME', stack_name)
  s =    s.replace('$STACK_VERSION', stack_ver)
  s =    s.replace('$RELEASE_NAME', release_name)
  return s

if __name__ == '__main__':
    main()

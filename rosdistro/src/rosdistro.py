# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Revision $Id: distro.py 10301 2010-07-09 01:21:23Z kwc $

"""
Library for process rosdistro files.

New in ROS C-Turtle
"""

from __future__ import with_statement

import roslib; roslib.load_manifest('rosdistro')

import os
import sys
import yaml
import string
import subprocess

import vcstools

class DistroException(Exception): pass

def distro_version(version_val):
    """Parse distro version value, converting SVN revision to version value if necessary"""
    import re
    version_val = str(version_val)
    m = re.search('\$Revision:\s*([0-9]*)\s*\$', version_val)
    if m is not None:
        version_val = 'r'+m.group(1)

    # Check that is a valid version string
    valid = string.ascii_letters + string.digits + '.+~'
    if False in (c in valid for c in version_val):
        raise DistroException("Version string %s not valid"%version_val)
    return version_val

def expand_rule(rule, stack_name, stack_ver, release_name, revision=None):
    s = rule.replace('$STACK_NAME', stack_name)
    s =    s.replace('$STACK_VERSION', stack_ver)
    s =    s.replace('$RELEASE_NAME', release_name)
    if s.find('$REVISION') > 0 and not revision:
        raise DistroException("revision specified but not supplied by build_release")
    elif revision:
        s = s.replace('$REVISION', revision)
    return s

def load_vcs_config(rules, rule_eval):
    vcs_config = None
    if 'svn' in rules or 'dev-svn' in rules:
        import vcstools.svn
        vcs_config = vcstools.svn.SVNConfig()
        
        if 'svn' in rules:
            r = rules['svn']

            vcs_config.dev     = rule_eval(r['dev'])
            vcs_config.distro_tag  = rule_eval(r['distro-tag'])
            vcs_config.release_tag = rule_eval(r['release-tag'])

            # specify urls that are safe to anonymously read
            # from. Users must supply a complete set.
            if 'anon-dev' in r:
                vcs_config.anon_dev = rule_eval(r['anon-dev'])
                vcs_config.anon_distro_tag = rule_eval(r['anon-distro-tag'])                
                vcs_config.anon_release_tag = rule_eval(r['anon-release-tag'])
            else:
                # if no login credentials, assume that anonymous is
                # same as normal keys.
                vcs_config.anon_dev = vcs_config.dev
                vcs_config.anon_distro_tag = vcs_config.distro_tag
                vcs_config.anon_release_tag = vcs_config.release_tag

        else:
            #legacy support
            vcs_config.dev         = rule_eval(rules['dev-svn'])
            vcs_config.distro_tag  = rule_eval(rules['distro-svn'])
            vcs_config.release_tag = rule_eval(rules['release-svn'])
            vcs_config.anon_dev = vcs_config.dev
            vcs_config.anon_distro_tag = vcs_config.distro_tag
            vcs_config.anon_release_tag = vcs_config.release_tag
            
            
    elif 'hg' in rules:
        import vcstools.hg
        vcs_config = vcstools.hg.HGConfig()

        vcs_config.repo_uri      = rule_eval(rules['hg']['uri'])
        vcs_config.dev_branch    = rule_eval(rules['hg']['dev-branch'])
        vcs_config.distro_tag    = rule_eval(rules['hg']['distro-tag'])
        vcs_config.release_tag   = rule_eval(rules['hg']['release-tag'])

    elif 'git' in rules:
        import vcstools.git
        vcs_config = vcstools.git.GITConfig()

        vcs_config.repo_uri      = rule_eval(rules['git']['uri'])
        vcs_config.dev_branch    = rule_eval(rules['git']['dev-branch'])
        vcs_config.distro_tag    = rule_eval(rules['git']['distro-tag'])
        vcs_config.release_tag   = rule_eval(rules['git']['release-tag'])

    return vcs_config
    
def get_variants(distro, stack_name):
    """
    Retrieve names of variants that stack is present in. This operates
    on the raw distro dictionary document.
    
    @param distro: rosdistro document
    @type  distro: dict
    """
    if stack_name == 'ROS':
        stack_name = 'ros'

    retval = []
    variants = distro.get('variants', {})
    
    for variant_d in variants:
        try:
            variant = variant_d.keys()[0]
            variant_props = variant_d[variant]
            if stack_name in variant_props['stacks']:
                retval.append(variant)
            elif 'extends' in variant_props and variant_props['extends'] in retval:
                retval.append(variant)                
        except:
            pass
    return retval

# TODO: integrate with Distro
def get_rules(distro, stack_name):
    """
    Retrieve rules from distro for specified stack This operates on
    the raw distro dictionary document.

    @param distro: rosdistro document
    @type  distro: dict
    @param stack_name: name of stack to get rules for
    @type  stack_name: str
    """

    if stack_name == 'ROS':
        stack_name = 'ros'
        
    # _rules: named section
    named_rules_d = distro.get('_rules', {})
    
    # there are three tiers of dictionaries that we look in for uri rules
    rules_d = [distro.get('stacks', {}),
               distro.get('stacks', {}).get(stack_name, {})]
    rules_d = [d for d in rules_d if d]

    # load the '_rules' from the dictionaries, in order
    props = {}
    for d in rules_d:
        if type(d) == dict:
            update_r = d.get('_rules', {})
            if type(update_r) == str:
                try:
                    update_r = named_rules_d[update_r]
                except KeyError:
                    raise DistroException("no _rules named [%s]"%(update_r))
                
            new_style = True
            for k in ['distro-svn', 'release-svn', 'dev-svn']:
                if k in update_r:
                    new_style = False
            if new_style:
                # in new style, we do not do additive rules
                if not type(update_r) == dict:
                    raise Exception("invalid rules: %s %s"%(d, type(d)))
                # ignore empty definition
                if update_r:
                    props = update_r
            else:
                # legacy: rules overlay higher level rules
                if not type(update_r) == dict:
                    raise Exception("invalid rules: %s %s"%(d, type(d)))
                props.update(update_r)

    if not props:
        raise Exception("cannot load _rules")
    return props
        

def load_distro_stacks(distro_doc, stack_names, release_name=None, version=None):
    """
    @param distro_doc: dictionary form of rosdistro file
    @type distro_doc: dict
    @param stack_names: names of stacks to load
    @type  stack_names: [str]
    @param release_name: (optional) name of distro release to override distro_doc spec.
    @type  release_name: str
    @param version: (optional) distro version to override distro_doc spec.
    @type  version: str
    @return: dictionary of stack names to DistroStack instances
    @rtype: {str : DistroStack}
    @raise DistroException: if distro_doc format is invalid
    """

    # load stacks and expand out uri rules
    stacks = {}
    # we pass these in mostly for small performance reasons, as well as testing
    if version is None:
        version = distro_version(distro_doc.get('version', '0'))        
    if release_name is None:
        release_name = distro_doc['release']

    try:
        stack_props = distro_doc['stacks']
    except KeyError:
        raise DistroException("distro is missing required 'stacks' key")
    for stack_name in stack_names:
        # ignore private keys like _rules
        if stack_name[0] == '_':
            continue

        stack_version = stack_props[stack_name].get('version', 'unversioned')
        rules = get_rules(distro_doc, stack_name)
        stacks[stack_name] = DistroStack(stack_name, rules, stack_version, release_name, version)
    return stacks

class DistroStack(object):
    """Stores information about a stack release"""

    def __init__(self, stack_name, rules, stack_version, release_name, release_version):
        self.name = stack_name
        self.release_name = release_name
        self.release_version = release_version        

        self._rules = rules
        
        self.update_version(stack_version)
        self.repo = rules.get('repo', None)


    def update_version(self, stack_version):
        rules = self._rules
        self.version = stack_version

        #rosdistro key
        # - for future SCM rules, we need to put them in a more
        #   general representation. Leaving the SVN representation
        #   as-is so as to not disturb existing scripts.
        self.dev_svn = self.distro_svn = self.release_svn = None
        self.vcs_config = load_vcs_config(rules, self.expand_rule)

        # legacy support, remove once we stop building box turtle
        if 'svn' in rules or 'dev-svn' in rules:
            self.dev_svn     = self.vcs_config.dev
            self.distro_svn  = self.vcs_config.distro_tag
            self.release_svn = self.vcs_config.release_tag

        
    def expand_rule(self, rule):
        """
        Perform variable substitution on stack rule.
        """
        return expand_rule(rule, self.name, self.version, self.release_name)
        
    def __eq__(self, other):
        if not isinstance(other, DistroStack):
            return False
        return self.name == other.name and \
            self.version == other.version and \
            self.vcs_config == other.vcs_config

class Variant(object):
    """
    A variant defines a specific set of stacks ("metapackage", in Debian
    parlance). For example, "base", "pr2". These variants can extend
    another variant.
    """

    def __init__(self, variant_name, source_uri, variants_props):
        """
        @param variant_name: name of variant to load from distro file
        @type  variant_name: str
        @param source_uri: source URI of distro file
        @type  source_uri: str
        @param variants_props: dictionary mapping variant names to the rosdistro map for that variant
        """
        self.name = variant_name
        self.source_uri = source_uri

        # save the properties for our particular variant
        try:
            props = variants_props[variant_name]
        except:
            raise DistroException("distro does not define a '%s' variant"%variant_name)

        # load in variant properties from distro spec
        if not 'stacks' in props:
            raise DistroException("variant properties must define 'stacks':\n%s"%props[n])
        self.stack_names = list(props['stacks'])

        # check to see if we extend another distro, in which case we prepend their props
        if 'extends' in props:
            self.parent = props['extends']
            self.parent_uri = props.get('extends-uri', source_uri)
            parent_variant = Variant(self.parent, self.parent_uri, variants_props)
            self.stack_names = parent_variant.stack_names + self.stack_names
        self.props = props
      
class Distro(object):
    """
    Store information in a rosdistro file.
    """
    
    def __init__(self, source_uri):
        """
        @param source_uri: source URI of distro file, or path to distro file
        """
        # initialize members
        self.source_uri = source_uri

        self.ros = None
        self.stacks = {} # {str: DistroStack}
        self.stack_names = [] 
        self.variants = {}
        self.distro_props = None

        try:
            # parse rosdistro yaml
            if os.path.isfile(source_uri):
                # load rosdistro file
                with open(source_uri) as f:
                    y = yaml.load(f.read())
            elif 'code.ros.org/svn' in source_uri:
                # Create a temp directory and fetch via svn export so
                # that keywords are evaluated. The test for
                # code.ros.org is a big hack.
                import shutil
                import tempfile

                tmp_dir = tempfile.mkdtemp()
                tmp_distro_file = os.path.join(tmp_dir, os.path.split(source_uri)[-1])
                p = subprocess.Popen(['svn','export',source_uri,tmp_distro_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate()
                if p.returncode != 0:
                    raise Exception("svn export [%s] failed"%(source_uri))
                with open(tmp_distro_file) as f:
                    y = yaml.load(f.read())
                shutil.rmtree(tmp_dir)
            else:
                import urllib2
                y = yaml.load(urllib2.urlopen(source_uri))
                
            self.distro_props = y
  
            stack_props = y['stacks']
            self.stack_names = [x for x in stack_props.keys() if not x[0] == '_']
            self.version = distro_version(y.get('version', '0'))
            self.release_name = y['release']
  
            variants = {}
            for props in y['variants']:
                if len(props.keys()) != 1:
                    raise DistroException("invalid variant spec: %s"%props)
                n = props.keys()[0]
                variants[n] = props[n]
  
        except KeyError, e:
            raise DistroException("this program assumes the yaml has a '%s' map"%(str(e)))

        # load variants
        for v in variants.iterkeys():
            self.variants[v] = Variant(v, source_uri, variants)

        if not 'ros' in stack_props:
            raise DistroException("this program assumes that ros is in your variant")

        self.stacks = load_distro_stacks(self.distro_props, self.stack_names, release_name=self.release_name, version=self.version)
        self.ros = self.stacks.get('ros', None)


def stack_to_rosinstall(stack, branch, anonymous=True):
    """
    Generate the rosinstall dictionary entry for a stack in the rosdistro
    @param stack A DistroStack for a particular stack
    @param branch Select the branch or tag from 'devel', 'release' or 'distro' of the stack to checkout
    @param anonymous For svn use anonymous access url. ( It usually doesn't have write permissions. )
    """
    result = []

    uri = None
    version = None

    vcs = stack.vcs_config
    if not branch in ['devel', 'release', 'distro']:
        raise DistroException('Unsupported branch type %s for stack %s'%(branch, stack.name))

    if not vcs.type in ['svn', 'hg', 'bzr', 'git']:
        raise DistroException( 'Unsupported vcs type %s for stack %s'%(vcs.type, stack.name))
        
    if vcs.type == 'svn':
        if branch == 'devel':
            if anonymous: 
                uri = vcs.anon_dev
            else:
                uri = vcs.dev
            #return "- svn: {uri: '%s', local-name: '%s'}\n"%(vcs.anon_dev, stack.name)
        elif branch == 'distro':
            if anonymous: 
                uri = vcs.anon_distro_tag
            else:
                uri = vcs.distro_tag
        elif branch == 'release':
            if anonymous: 
                uri = vcs.anon_release_tag
            else:
                uri = vcs.release_tag

    else:#if vcs.type == 'hg' or vcs.type == 'git' or vcs.type == 'bzr':
        uri = vcs.repo_uri
        if branch == 'devel':
            version = vcs.dev_branch
        elif branch == 'distro':
            version = vcs.distro_tag
        elif branch == 'release':
            version = vcs.release_tag


    if version:
        result.append({vcs.type: {"uri": uri, 'local-name': stack.name, 'version': version} } )
    else:
        result.append({vcs.type: {"uri": uri, 'local-name': stack.name} } )
    return result

def variant_to_rosinstall(variant_name, distro, branch, anonymous=True):
    rosinstall_dict = []
    variant = distro.variants.get(variant_name, None)
    if not variant:
        return []
    for s in variant.stack_names:
        if s in distro.stacks:
            rosinstall_dict.extend(stack_to_rosinstall(distro.stacks[s], branch, anonymous))
    return rosinstall_dict


def distro_to_rosinstall(distro, branch, anonymous=True):
    rosinstall_dict = []
    for s in distro.stacks:
        rosinstall_dict.extend(stack_to_rosinstall(distro.stacks[s], branch, anonymous))
    return rosinstall_dict

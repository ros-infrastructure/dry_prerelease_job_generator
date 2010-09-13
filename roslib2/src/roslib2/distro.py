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

import os
import sys
import yaml
import urllib2
import re
import string
import subprocess
import tempfile
import shutil

class DistroException(Exception): pass

def distro_version(version_val):
    """Parse distro version value, converting SVN revision to version value if necessary"""
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
                
            if 'svn' in update_r:
                # new style
                if 'svn' not in props:
                    props['svn'] = {}
                props['svn'].update(update_r['svn'])
            else:
                if not type(update_r) == dict:
                    raise Exception("invalid rules: %s %s"%(d, type(d)))
                # legacy
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
        
        self.user_svn = self.pass_svn = None
        # for password-protected repos
        # - for future SCM rules, we need to put them in a more
        #   general representation. Leaving the SVN representation
        #   as-is so as to not disturb existing scripts.
        if 'svn' in rules:
            self.user_svn = rules['svn'].get('username', None)
            self.pass_svn = rules['svn'].get('password', None)
        elif 'user-svn' in rules:
            self.user_svn = rules.get('user-svn', None)
            self.pass_svn = rules.get('pass-svn', None)
    
        self.update_version(stack_version)

    def update_version(self, stack_version):
        rules = self._rules
        self.version = stack_version

        #rosdistro key
        # - for future SCM rules, we need to put them in a more
        #   general representation. Leaving the SVN representation
        #   as-is so as to not disturb existing scripts.
        self.dev_svn = self.distro_svn = self.release_svn = None
        if 'svn' in rules:
            self.dev_svn     = self.expand_rule(rules['svn']['dev'])
            self.distro_svn  = self.expand_rule(rules['svn']['distro-tag'])
            self.release_svn = self.expand_rule(rules['svn']['release-tag'])
        elif 'dev-svn' in rules:
            #legacy support
            self.dev_svn     = self.expand_rule(rules['dev-svn'])
            self.distro_svn  = self.expand_rule(rules['distro-svn'])
            self.release_svn = self.expand_rule(rules['release-svn'])
        
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
            self.dev_svn == other.dev_svn and \
            self.distro_svn == other.distro_svn and \
            self.release_svn == other.release_svn and \
            self.user_svn == other.user_svn and \
            self.pass_svn == other.pass_svn

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
            else:
                # Create a temp directory and fetch via svn export
                tmp_dir = tempfile.mkdtemp()
                tmp_distro_file = os.path.join(tmp_dir, os.path.split(source_uri)[-1])
                subprocess.check_call(['svn','export',source_uri,tmp_distro_file])
                with open(tmp_distro_file) as f:
                    y = yaml.load(f.read())
                shutil.rmtree(tmp_dir)
                
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

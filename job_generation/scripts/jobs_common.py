#!/usr/bin/python

# ROSDISTRO_MAP = {'unstable': 'http://www.ros.org/distros/unstable.rosdistro',
#                  'cturtle': 'http://www.ros.org/distros/cturtle.rosdistro',
#                  'boxturtle': 'http://www.ros.org/distros/boxturtle.rosdistro'}

ROSDISTRO_MAP = {'unstable': 'https://code.ros.org/svn/release/trunk/distros/unstable.rosdistro',
                 'cturtle': 'https://code.ros.org/svn/release/trunk/distros//cturtle.rosdistro',
                 'boxturtle': 'http://www.ros.org/distros/boxturtle.rosdistro'}

# the supported Ubuntu distro's for each ros distro
ARCHES = ['amd64', 'i386']

# ubuntu distro mapping to ros distro
UBUNTU_DISTRO_MAP = {'unstable': ['lucid','karmic'],
                     'cturtle':  ['lucid', 'karmic', 'jaunty'],
                     'boxturtle':['hardy','karmic', 'jaunty']}

# path to hudson server
SERVER = 'http://build.willowgarage.com/'

def stack_to_deb(stack, rosdistro):
    return '-'.join(['ros', rosdistro, str(stack).replace('_','-')])

def stacks_to_debs(stack_list, rosdistro):
    if not stack_list:
        return ''
    return ' '.join([stack_to_deb(s, rosdistro) for s in stack_list])

def stack_to_rosinstall(stack, branch):
    vcs = stack.vcs_config
    if not branch in ['devel', 'release', 'distro']:
        print 'Unsupported branch type %s for stack %s'%(branch, stack.name)
        return ''
    if not vcs.type in ['svn', 'hg']:
        print 'Unsupported vcs type %s for stack %s'%(vcs.type, stack.name)
        return ''
        
    if vcs.type == 'svn':
        if branch == 'devel':
            return "- svn: {uri: '%s', local-name: '%s'}\n"%(vcs.anon_dev, stack.name)
        elif branch == 'distro':
            return "- svn: {uri: '%s', local-name: '%s'}\n"%(vcs.anon_distro_tag, stack.name)            
        elif branch == 'release':
            return "- svn: {uri: '%s', local-name: '%s'}\n"%(vcs.anon_release_tag, stack.name)  

    elif vcs.type == 'hg':
        if branch == 'devel':
            return "- hg: {uri: '%s', version: '%s', local-name: '%s'}\n"%(vcs.repo_uri, vcs.dev_branch, stack.name)
        elif branch == 'distro':
            return "- hg: {uri: '%s', version: '%s', local-name: '%s'}\n"%(vcs.repo_uri, vcs.distro_branch, stack.name)
        elif branch == 'release':
            return "- hg: {uri: '%s', version: '%s', local-name: '%s'}\n"%(vcs.repo_uri, vcs.release_branch, stack.name)



def stacks_to_rosinstall(stack_list, stack_map, branch):
    res = ''
    for s in stack_list:
        if s in stack_map:
            res += stack_to_rosinstall(stack_map[s], branch)
    return res
    

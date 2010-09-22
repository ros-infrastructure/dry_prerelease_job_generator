#!/usr/bin/python

ROSDISTRO_MAP = {'unstable': 'http://www.ros.org/distros/unstable.rosdistro',
                 'cturtle': 'http://www.ros.org/distros/cturtle.rosdistro',
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

def stack_to_rosinstall(stack, stack_map, branch):
    if stack == '' or not stack in stack_map:
        return ''
    vcs = stack_map[stack].cvs_config
    return "- %s: {uri: '%s', local-name: '%s'}\n"%(vcs.type, eval('vcs.%s'%branch), stack)

def stacks_to_rosinstall(stack_list, stack_map, svn='distro_svn'):
    print stack_list
    if len(stack_list) == 0:
        return ''
    return ''.join([stack_to_rosinstall(s, stack_map, svn) for s in stack_list])
    

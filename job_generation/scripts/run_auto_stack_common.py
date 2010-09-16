#!/usr/bin/python

ROSDISTRO_MAP = {'unstable': 'http://www.ros.org/distros/unstable.rosdistro',
                 'cturtle': 'http://www.ros.org/distros/cturtle.rosdistro',
                 'boxturtle': 'http://www.ros.org/distros/boxturtle.rosdistro'}



def stack_to_deb(stack, rosdistro):
    return '-'.join(['ros', rosdistro, str(stack).replace('_','-')])

def stacks_to_debs(stack_list, rosdistro):
    return ' '.join([stack_to_deb(s, rosdistro) for s in stack_list])

def stack_to_rosinstall(stack, stack_map, svn='distro_svn'):
    if stack == '' or not stack in stack_map:
        return ''
    return "- svn: {uri: '%s', local-name: '%s'}\n"%(eval('stack_map[stack].%s'%svn), stack)

def stacks_to_rosinstall(stack_list, stack_map, svn='distro_svn'):
    print stack_list
    if len(stack_list) == 0:
        retrun ''
    return ' '.join([stack_to_rosinstall(s, stack_map, svn) for s in stack_list])
    

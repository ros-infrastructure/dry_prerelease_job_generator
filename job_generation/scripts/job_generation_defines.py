#!/usr/bin/python

def get_ubuntu_distro_map():
    return {'unstable': ['lucid','karmic'],
            'cturtle':  ['lucid', 'karmic', 'jaunty'],
            'boxturtle':['hardy','karmic', 'jaunty']}

def get_rostinstall_config():
    return "- svn: {uri: 'STACKURI', local-name: 'STACKNAME'}"

def get_ros_distro_map():
    return  {'unstable': 'http://www.ros.org/distros/unstable.rosdistro',
             'cturtle': 'http://www.ros.org/distros/cturtle.rosdistro',
             'boxturtle': 'http://www.ros.org/distros/boxturtle.rosdistro'}


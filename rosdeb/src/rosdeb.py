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
# Revision $Id$
"""
Ubuntu/Debian utilities for building debian packages.
"""

# TODO: much to do here to make this more maintainable

_ubuntu_map = { '10.10': 'mighty', '10.04': 'lucid', '9.10': 'karmic', '9.04': 'jaunty', '8.10': 'intrepid', '8.04': 'hardy'}
def ubuntu_release():
    """
    WARNING: this can only be called on an Ubuntu system
    """
    f = open('/etc/issue')
    for s in f:
        if s.startswith('Ubuntu'):
            v = s.split()[1]
            v = '.'.join(v.split('.')[:2])
        try:
            return _ubuntu_map[v]
        except KeyError:
            raise DistroException("unrecognized ubuntu version %s" % v)
    raise DistroException("could not parse ubuntu release version")

def debianize_name(name):
    """
    Convert ROS stack name to debian conventions (dashes, not underscores)
    """
    return name.replace('_', '-')

def debianize_version(stack_version, distro_version, ubuntu_rel=None):
    """
    WARNING: this can only be called on an Ubuntu system
    """
    if ubuntu_rel is None:
        ubuntu_rel = ubuntu_release()
    return stack_version+'-'+distro_version+'~%s'%ubuntu_rel

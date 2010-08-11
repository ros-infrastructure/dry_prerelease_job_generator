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
# $Author$

def convert_html_to_text(d):
    """
    Convert a HTML description to plain text. This routine still has
    much work to do, but appears to handle the common uses of HTML in
    our current manifests.
    """
    # check for presence of tags
    if '<' in d:
        from release.BeautifulSoup import BeautifulSoup
        soup = BeautifulSoup(d)
        # convert all paragraphs to line breaks
        paragraphs = soup.findAll('p')
        for p in paragraphs:
            s = ''.join([str(x) for x in p.contents])+"\n"
            p.replaceWith(s)
        # this logic is incorrect, it only handles one-level-deep nesting of tags
        reduce = ['a', 'b', 'i', 'tt', 'strong', 'em', 'li']
        for t in reduce:
            tags = soup.findAll(t)
            for x in tags:
                x.replaceWith(x.string)

        # findAll text strips remaining tags
        d = ''.join(soup.findAll(text=True))
        
    # double-whitespace is meaningless in HTML, so now we need to reduce
    #  - remove leading whitespace
    d = '\n'.join([x.strip() for x in d.split('\n')])

    d_reduced = ''
    last = None
    for x in d.split('\n'):
        if last is None:
            d_reduced = x
        else:
            if x == '':
                if last == '':
                    pass
                else:
                    d_reduced += '\n'
            else:
                d_reduced += x + ' '
        last = x
    return d_reduced

def stack_rosdeps(stack_name):
    """
    calculate dependencies of stack, including both ROS stacks and their rosdep dependencies
    
    @return: list of debian package deps
    """
    ros_root = roslib.rosenv.get_ros_root()

    # - implicit deps of all ROS packages
    deb_deps = ['libc6','build-essential','cmake','python-yaml','subversion']     
    
    pkgs = roslib.stacks.packages_of(stack_name)
    if not pkgs:
        return []

    cmd = [os.path.join(ros_root, 'bin', 'rosdep'),'satisfy','--include_duplicates'] + pkgs
    rosdep_script = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
    
    marker = "sudo apt-get install"
    install_line = [s for s in rosdep_script.split('\n') if s.startswith(marker)]
    deb_deps += install_line[0][len(marker):].split() if install_line else []
    return deb_deps

if __name__ == '__main__':
    # test out our HTML converter on all known stacks        
    import roslib.stacks
    from roslib.stack_manifest import parse_file, stack_file
    for stack_name in roslib.stacks.list_stacks():
        if 0:
            stack_xml = stack_file(stack_name)
            m = roslib.stack_manifest.parse_file(stack_xml)
            print '#' * 80
            print m.description
            print '---'
            print convert_html_to_text(m.description)
            print '---'
        if 1:
            print stack_name
            print stack_rosdeps(stack_name)
    

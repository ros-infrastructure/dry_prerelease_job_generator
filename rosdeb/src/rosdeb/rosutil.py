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

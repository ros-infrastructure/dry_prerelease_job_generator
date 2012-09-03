#!/usr/bin/env python

import sys
import cgi
import urllib
import os
import subprocess
import tempfile

import cgitb
cgitb.enable()


# Assemble a dictionary of stacks.
def find_stacks(form):
    if 'email' not in form.keys():
        print "<H1>Error</H1>"
        print "Please fill in email address."
        return None
    email = form['email'].value

    if 'distro' not in form.keys():
        print "<H1>Error</H1>"
        print "Please select a valid distribution."
        return None
    distro = form['distro'].value

    import re
    stack_form = re.compile('stack_([0-9]*)')
    stacks = []
    for k in form.keys():
        match = stack_form.match(k)
        if match:
            stacks.append(form['stack_%d'%int(match.group(1))].value)
    if len(stacks) == 0:
        print "<H1>Error</H1>"
        print "Please specify the stack(s) to test."
        return None
        
    return distro, email, stacks
      

def main():
    legacy_distro = ['cturtle', 'diamondback', 'electric']
    rosmake_distro = ['fuerte', 'groovy']
    catkin_distro = ['groovy (catkin)']

    print "Content-Type: text/html"     # HTML is following
    print                               # blank line, end of headers
    
    form = cgi.FieldStorage()

    ret = find_stacks(form)
    if not ret:
        print '<p><a href="http://packages.ros.org/prerelease">Try again</a>'
        return
    distro, email, stacks = ret

    f = open('/var/www/hds.xml')
    info = f.read().split(',')

    # old legacy toolset in /home/willow/ros_release
    if distro in legacy_distro:
      command = 'export ROS_HOME=/tmp && export ROS_PACKAGE_PATH="/home/willow/ros_release:/opt/ros/cturtle/stacks" && export ROS_ROOT="/opt/ros/cturtle/ros" && export PATH="/opt/ros/cturtle/ros/bin:$PATH" && export PYTHONPATH="/opt/ros/cturtle/ros/core/roslib/src" && rosrun job_generation generate_prerelease.py %s %s --repeat 0 --email %s --rosdistro %s'%(info[0], info[1], email, distro)
      for s in stacks:
        command += ' --stack %s'%s
      res, err = subprocess.Popen(['bash', '-c', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()


    # new pypi-based tools
    elif distro in rosmake_distro:
      command = 'generate_prerelease.py %s %s --repeat 0 --email %s --rosdistro %s'%(info[0], info[1], email, distro)
      for s in stacks:
        command += ' --stack %s'%s
      res, err = subprocess.Popen(['bash', '-c', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()


    # catkin stacks
    elif distro in catkin_distro:
      res = ""
      err = ""
      name = '_'.join(stacks)
      name = 'groovy-' + name
      if len(name) > 25:
          name = name[:17]+"..."
      for ubuntu in ['lucid', 'precise']:
          for arch in ['amd64', 'i386']:
              command = "/home/willow/buildfarm/run_jenkins %s %s %s %s prerelease groovy %s"%(ubuntu, arch, name, email, ' '.join(stacks))
              res_part, err_part = subprocess.Popen(['bash', '-c', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
              res = res + '\n' + res_part
              err = err + '\n' + err_part


    # invalid distro
    else:
      print "Unsupported distro: %s"%distro
      return


    res = res.replace('<', '<a href="')
    res = res.replace('>', '">the Hudson server</a>')
    res = res.replace('\n', '<br>')
    print '<h1>Your request was sent to the Hudson server</h1> <p> %s %s'%(str(res), str(err))

if __name__ == '__main__':
    main()

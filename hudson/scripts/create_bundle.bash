#!/bin/bash

# This script creates the pybundle used in the bootstrap stage of runchroot.  This avoids needing to hit pypi all the time.  

pip bundle rosbootstrap.pybundle vcstools pip rospkg rosinstall mock nose coverage genmsg genpy
scp rosbootstrap.pybundle ipr:/var/www/pr.willowgarage.com/html/downloads/rosbootstrap/


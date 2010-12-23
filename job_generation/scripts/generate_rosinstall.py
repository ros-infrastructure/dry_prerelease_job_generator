#!/usr/bin/env python

from __future__ import with_statement
PKG = 'job_generation'
import roslib; roslib.load_manifest(PKG)

import sys
import subprocess
import rosdistro 
import optparse
import datetime
from job_generation.jobs_common import *
from pysqlite2 import dbapi2 as sqlite


def main():
    parser = optparse.OptionParser()
    parser.add_option('--overlay', dest = 'overlay', action='store',
                      help='Create overlay file')    
    parser.add_option('--variant', dest = 'variant', action='store',
                      help="Specify the variant to create a rosinstall for")
    parser.add_option('--rosdistro', dest = 'rosdistro', action='store', 
                      help="Specify the ros distro to operate on")
    parser.add_option('--database', dest = 'database', action='store', 
                      help="Store requests in database")
    (options, args) = parser.parse_args()
    if not options.rosdistro in UBUNTU_DISTRO_MAP.keys():
        print 'Rosdistro %s does not exist. Options are %s'%(options.rosdistro, UBUNTU_DISTRO_MAP.keys())
        return

    # Parse distro file
    distro_obj = rosdistro.Distro(ROSDISTRO_MAP[options.rosdistro])
    

    # check if variant exists
    if not options.variant in distro_obj.variants:
        print 'Variant %s does not exist in rosdistro %s'%(options.variant, options.rosdistro)
        return

    # generate rosinstall file for variant
    if options.overlay == 'yes':
        rosinstall = rosdistro.variant_to_rosinstall(options.variant, distro_obj, 'release')
    else:
        rosinstall = rosdistro.extended_variant_to_rosinstall(options.variant, distro_obj, 'release')        

    print rosinstall

    # write to database
    if options.database:
        try:
            connection = sqlite.connect(options.database)
            cursor = connection.cursor()
            try:
                cursor.execute('CREATE TABLE rosinstall (stamp TIMESTAMP, rosdistro TEXT, variant TEXT, overlay TEXT)')
            except sqlite.OperationalError:
                pass
            cursor.execute('INSERT INTO rosinstall VALUES (?, ?, ?, ?)', (datetime.datetime.now(), options.rosdistro, options.variant, options.overlay))
            connection.commit()
        except:
            pass


if __name__ == '__main__':
    main()

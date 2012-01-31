#!/usr/bin/env python

PKG = 'job_generation'

import sys
import subprocess
import rosdistro 
import optparse
import datetime
from job_generation.jobs_common import *
from pysqlite2 import dbapi2 as sqlite

def main():
    (options, args) = get_options(['rosdistro', 'overlay', 'variant'], ['database'])
    if not options:
        return -1

    # Parse distro file
    distro_obj = rosdistro.Distro(get_rosdistro_file(options.rosdistro))

    # generate rosinstall file for variant
    if options.overlay == 'yes':
        rosinstall = rosdistro.variant_to_rosinstall(options.variant, distro_obj, 'release-tar')
    else:
        rosinstall = rosdistro.extended_variant_to_rosinstall(options.variant, distro_obj, 'release-tar')        

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
    sys.exit(main())

#!/usr/bin/env python

PKG = 'job_generation'

import sys
import subprocess
import rospkg.distro 
import optparse
import datetime
from job_generation.jobs_common import *
from pysqlite2 import dbapi2 as sqlite

def main():
    (options, args) = get_options(['rosdistro', 'overlay', 'variant'], ['database'])
    if not options:
        return -1

    # Parse distro file
    distro_obj = rospkg.distro.load_distro(rospkg.distro.distro_uri(options.rosdistro))

    # generate rosinstall file for variant
    if options.overlay == 'yes':
        rosinstall = rospkg.distro.distro_to_rosinstall(distro_obj, 'release-tar', options.variant, False)
    else:
        rosinstall = rospkg.distro.distro_to_rosinstall(distro_obj, 'release-tar', options.variant, True)

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

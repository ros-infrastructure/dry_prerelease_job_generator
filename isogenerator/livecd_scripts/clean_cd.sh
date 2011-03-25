#!/bin/bash


if [ "x$1" == "xyes" ] ; then
    umount livecd
    rm -rf livecd
    rm -rf cd squashfs custom
else
    echo "This script will delete all the temporary files used for"
    echo "editing the cd. This is a bad idea if the files have been"
    echo "changed without creating a new iso file. If you really"
    echo "want to run this script, please type:"
    echo "$0 yes"
fi
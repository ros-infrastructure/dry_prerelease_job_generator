#!/bin/bash

FILE=$1

if [ "x$FILE" == "x" ] ; then
    echo "You must specifiy an ISO to extract:"
    echo "$0 <file-name>"
    echo "If you don't have one, download it from the Ubuntu site."
    exit 1
fi

mkdir -p /tmp/livecd
sudo umount /tmp/livecd
sudo mount -o loop $FILE /tmp/livecd 

sudo rm -rf cd custom squashfs

mkdir cd
rsync --exclude=/casper/filesystem.squashfs -a /tmp/livecd/ cd


mkdir squashfs
mkdir custom
sudo modprobe squashfs
sudo mount -t squashfs -o loop /tmp/livecd/casper/filesystem.squashfs squashfs
sudo cp -a squashfs/* custom 
sudo umount squashfs
sudo rm -rf squashfs

sudo umount /tmp/livecd
sudo rm -r /tmp/livecd


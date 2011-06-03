#!/bin/bash

LIVECD_SCRIPTS=`pwd`

INITIAL_LIVECD=$1
FINAL_LIVECD=$2
DIRECTORY=$3
INTERNAL_PATCH_SCRIPT=$4

#Need four arguments
if [ "x$4" = "x" ] ; then
    echo "Incorrect usage: not enough arguments"
    echo "$0 <initial-iso> <final-iso> <working-directory> <internal-patch-script>"
    echo "All paths must be absolute"
    exit 1
fi

#FIXME: make sure the scripts can be found
#FIXME: ensure path absoluteness

if [ -e $INITIAL_LIVECD ] ; then
    echo "Found $INITIAL_LIVECD"
else
    echo "The livecd initial ISO file is not present. Customization"
    echo "cannot proceed for $INITIAL_LIVECD"
    exit 2
fi

if [ -e $FINAL_LIVECD ] ; then
    echo "Found $FINAL_LIVECD, must remove"
    #FIXME: prompt
    rm -rf $FINAL_LIVECD
else
    echo "No output file $FINAL_LIVECD"
fi

echo "Checking if the directory exists"
if [ -d $DIRECTORY ] ; then
    echo "The directory already exists. Removing it"
    #FIXME: prompt
    rm -rf $DIRECTORY
fi

echo "Creating directory"
mkdir -p $DIRECTORY

echo "Cding to the directoy"
cd $DIRECTORY

echo "Extracting the livecd"
$LIVECD_SCRIPTS/extract_cd.sh "$INITIAL_LIVECD"

echo "Running the customization scripts"
$LIVECD_SCRIPTS/edit_cd.sh "$INTERNAL_PATCH_SCRIPT"

echo "Recreating the livecd"
$LIVECD_SCRIPTS/create_iso.sh "$FINAL_LIVECD"

echo "Cleaning out the CD files"
$LIVECD_SCRIPTS/clean_cd.sh yes

echo "Leaving the directory"
cd $LIVECD_SCRIPTS

echo "Deleting the directory"
rm -rf $DIRECTORY

#!/bin/bash

. $(dirname $0)/colors.sh

MOUNTPOINT="/mnt/user/fuse/mountpoint"
ROOTPOINT="/mnt/user/fuse/root"


echo "${greenbg}${white}Creating some dirs ad files ...${reset}"
touch $MOUNTPOINT/file1.txt
mkdir -p $MOUNTPOINT/dir1/sousdir/sousousdir
touch $MOUNTPOINT/dir1/sousdir/sousousdir/file1.txt
mkdir -p $MOUNTPOINT/dir2                   
touch $MOUNTPOINT/dir2/file1.txt

x=0;
for  ((x=0; x<10; ++x)); do
    dd if=/dev/urandom bs=10M count=1 of=/$MOUNTPOINT/dir2/FILE$x iflag=fullblock
done

x=0;
for  ((x=0; x<10; ++x)); do
    dd if=/dev/urandom bs=10M count=1 of=$MOUNTPOINT/dir1/sousdir/sousousdir/FILE$x iflag=fullblock
done

x=0;
for  ((x=0; x<10; ++x)); do
    dd if=/dev/urandom bs=10M count=1 of=$MOUNTPOINT/FILE$x iflag=fullblock
done


echo "${greenbg}${white}Show diff beetween mount and root dir ...${reset}"
tree $MOUNTPOINT
tree $ROOTPOINT

echo "${greenbg}${white}Cleaning root dir ...${reset}"
rm -r $ROOTPOINT/*

echo "${greenbg}${white}Show diff beetween mount and root dir ...${reset}"
tree $MOUNTPOINT
tree $ROOTPOINT
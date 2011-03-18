#!/bin/bash

#Create scripts
cat > _____start_edit.sh <<EOF
source /etc/bash.bashrc
source /root/.bashrc
mount -t proc none /proc/
mount -t sysfs none /sys/
export HOME=/root 
EOF

cat > _____end_edit.sh <<EOF
apt-get clean
rm -rf /tmp/*
rm -f /etc/hosts /etc/resolv.conf
rm /root/start_edit.sh
rm /root/end_edit.sh
umount /proc/
umount /sys/
echo "livecd clean"
exit
EOF

#Copy resolv.conf so the internet is accessible.
sudo cp /etc/resolv.conf /etc/hosts custom/etc/

#Copy scripts
sudo mkdir -p custom/root
sudo chown root:root custom/root
sudo cp _____start_edit.sh custom/root/start_edit.sh
sudo cp _____end_edit.sh custom/root/end_edit.sh
sudo chown root:root custom/root/start_edit.sh
sudo chown root:root custom/root/end_edit.sh
sudo chmod a+wrx custom/root/start_edit.sh
sudo chmod a+wrx custom/root/end_edit.sh
rm _____start_edit.sh _____end_edit.sh

echo "You are now ready to begin editing the livecd"
echo "You are chrooted to the live cd. You may edit"
echo "freely, however, you must not quit by closing"
echo "the outer terminal. You must exit by typing"
echo "\"exit\", or control+D so that the cleanup"
echo "script is run, and garbage files are not left"
echo "on the system."

sudo chroot custom bash --init-file /root/start_edit.sh

echo "Cleaning up the livecd"
sudo chroot custom bash -c "source /root/end_edit.sh"
echo "exiting"



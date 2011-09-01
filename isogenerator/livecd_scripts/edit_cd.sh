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
rm /root/edit_script.sh
umount /proc/
umount /sys/
echo "livecd clean"
exit
EOF

#Copy resolv.conf so the internet is accessible.
cp /etc/resolv.conf /etc/hosts custom/etc/

#Copy scripts
mkdir -p custom/root
chown root:root custom/root
cp _____start_edit.sh custom/root/start_edit.sh
cp _____end_edit.sh custom/root/end_edit.sh
chown root:root custom/root/start_edit.sh
chown root:root custom/root/end_edit.sh
chmod a+wrx custom/root/start_edit.sh
chmod a+wrx custom/root/end_edit.sh
rm _____start_edit.sh _____end_edit.sh

if [ -e custom/root/on_install.sh ] ; then
    echo "Already have on_install.sh"
else
    cat > custom/root/on_install.sh <<EOF
#!/bin/bash
echo "Script runs on install - cleans up system"
EOF
    chmod a+wrx custom/root/on_install.sh
fi

if [ "x$1" = "x" ] ; then
    echo "You are now ready to begin editing the livecd"
    echo "You are chrooted to the live cd. You may edit"
    echo "freely, however, you must not quit by closing"
    echo "the outer terminal. You must exit by typing"
    echo "\"exit\", or control+D so that the cleanup"
    echo "script is run, and garbage files are not left"
    echo "on the system."
    echo "Don't forget to add custom post-install cleanup"
    echo "code to: /root/on_install.sh"
    chroot custom /bin/bash --init-file /root/start_edit.sh
else
    cp $1 custom/root/edit_script.sh
    chmod a+wrx custom/root/edit_script.sh
    chroot custom /bin/bash -c "source /root/start_edit.sh ; /root/edit_script.sh"
fi


echo "Cleaning up the livecd"
chroot custom /bin/bash -c "source /root/end_edit.sh"
chmod a+wrx custom/root/on_install.sh
echo "exiting"

if [ "x" == "x`grep success_command cd/preseed/ubuntu.seed`" ] ; then
    echo "Add script"
    echo -e "ubiquity\tubiquity/success_command string chroot /target /bin/bash /root/on_install.sh" >> cd/preseed/ubuntu.seed
else
    echo "already added script"
fi
echo "done"

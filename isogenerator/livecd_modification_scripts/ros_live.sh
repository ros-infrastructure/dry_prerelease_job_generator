#!/bin/bash
#WARNING: this script is run under a chroot, so it cannot access files on the file system in general.

echo "Updating apt-get"
yes | apt-get update
echo "installing ssh and ntp"
yes | apt-get install ssh ntp
echo "removing openoffice"
yes | apt-get remove openoffice.org*

echo "Adding ROS to the apt-get sources"
echo "deb http://packages.ros.org/ros/ubuntu lucid main" > /etc/apt/sources.list.d/ros-latest.list
wget http://packages.ros.org/ros.key -O - | sudo apt-key add -
sudo apt-get update

echo "Updating apt sources file, so that all packages can be read"
cat /etc/apt/sources.list | sed "s/# deb/deb/g" > /tmp/new_sources.list
cp /tmp/new_sources.list /etc/apt/sources.list
sudo apt-get update

#Ros specific operations
echo "Adding ros user and group"
groupadd ros
useradd -m -g ros ros
usermod -a -G sudo ros
usermod -a -G video ros
usermod -s /bin/bash ros
echo -e "ros\nros" | passwd ros

echo "Adding install shortcut"
mkdir -p /home/ros/Desktop/
cat > /home/ros/Desktop/ubiquity-gtkui.desktop <<EOF
[Desktop Entry]
Type=Application
Version=1.0
# Do not translate the word "ROS Ubuntu".  It is used as a marker by casper.
Name=Install ROS Ubuntu
Name[af]=installeer ROS Ubuntu
Name[am]=ROS Ubuntu ይጫን
Name[an]=Instalar ROS Ubuntu
Name[ar]=ثبّت ROS Ubuntu
Name[ast]=Instalar ROS Ubuntu
Name[az]=ROS Ubuntu Quraşdır
Name[be]=Устанавіць ROS Ubuntu
Name[bg]=Инсталиране ROS Ubuntu
Name[bn]=ROS Ubuntu ইনস্টল করুন
Name[br]=Staliañ ROS Ubuntu
Name[bs]=Instaliraj izdanje
Name[ca]=Instal·la la versió ROS Ubuntu
Name[cs]=Nainstalovat ROS Ubuntu
Name[csb]=Winstalëjë ROS Ubuntu
Name[da]=Installér ROS Ubuntu
Name[de]=ROS Ubuntu installieren
Name[el]=Εγκατάσταση ROS Ubuntu
Name[eo]=Instali ROS Ubuntu
Name[es]=Instalar ROS Ubuntu
Name[et]=Paigalda ROS Ubuntu
Name[eu]=ROS Ubuntu instalatu
Name[fa]=نصب ROS Ubuntu
Name[fi]=Asenna ROS Ubuntu
Name[fr]=Installer ROS Ubuntu
Name[fy]=Ynstallear ROS Ubuntu
Name[gl]=Instalar ROS Ubuntu
Name[gu]=રિલીઝ નું સ્થાપન કરો.
Name[he]=התקנת ROS Ubuntu
Name[hi]=प्रकाशन को संस्थापित करें
Name[hr]=Instaliraj ROS Ubuntu
Name[hu]=ROS Ubuntu telepítése
Name[hy]=Տեղադրել ԹՈՂԱՐԿՈՒՄԸ
Name[id]=Instal ROS Ubuntu
Name[is]=Setja upp ROS Ubuntu
Name[it]=Installa ROS Ubuntu
Name[ja]=ROS Ubuntu のインストール
Name[ka]=ROS Ubuntu-ის დაყენება
Name[kk]=РЕЛИЗДІ орнату
Name[ko]=ROS Ubuntu 설치
Name[ku]=ROS Ubuntu saz bike
Name[lb]=ROS Ubuntu installéieren
Name[lt]=Įdiegti ROS Ubuntu į kompiuterį
Name[lv]=Instalēt ROS Ubuntu
Name[ms]=Pasang ROS Ubuntu
Name[nb]=Installer ROS Ubuntu
Name[nl]=ROS Ubuntu installeren
Name[nn]=Installér ROS Ubuntu
Name[oc]=Installar ROS Ubuntu
Name[pl]=Zainstaluj ROS Ubuntu
Name[pt]=Instalar ROS Ubuntu
Name[pt_BR]=Instalar ROS Ubuntu
Name[ro]=Instalare ROS Ubuntu
Name[ru]=Установить ROS Ubuntu
Name[sd]=انسٽال ROS Ubuntu
Name[sk]=Inštalovať ROS Ubuntu
Name[sl]=Namesti ROS Ubuntu
Name[sq]=Instalo ROS Ubuntu
Name[sr]=Инсталирајте ROS Ubuntu
Name[sv]=Installera ROS Ubuntu
Name[ta]=நிறுவு ROS Ubuntuஐ
Name[th]=ติดตั้ง ROS Ubuntu
Name[tl]=Iluklok ang ROS Ubuntu
Name[tr]=ROS Ubuntu Kur
Name[uk]=Встановити ROS Ubuntu
Name[vi]=Cài đặt ROS Ubuntu
Name[zh_CN]=安装 ROS Ubuntu
Name[zh_HK]=安裝 ROS Ubuntu
Name[zh_TW]=安裝 ROS Ubuntu
Comment=Install this system permanently to your hard disk
Comment[af]=Installeer hierdie stelsel permanent op jou hardeskyf
Comment[am]=ይኼን ሲስተም ሀርድ ዲስክዎ ላይ በቋሚነት ይጫኑት
Comment[an]=Instalar iste sistema ta cutio en o tuyo disco duro
Comment[ar]=ثبّت هذا النظام على القرص الصلب
Comment[ast]=Instalar permanentemente esti sistema nel to discu duru
Comment[az]=Sistemi sabit diskə daimlik qur
Comment[be]=Усталяваць гэту сыстэму на ваш жорсткі дыск
Comment[bg]=Инсталиране на тази система за постоянно на твърдия диск
Comment[bn]=আপনার হার্ড ডিস্কে স্থায়ীভাবে এই সিস্টেম ইনস্টল করুন
Comment[br]=Staliañ da vat ar sistem-mañ war ho pladenn galet
Comment[bs]=Instaliraj ovaj sistem trajno na hard disk
Comment[ca]=Instal·leu aquest sistema permanentment al vostre disc dur
Comment[cs]=Nainstalovat tento systém natrvalo na váš disk
Comment[csb]=Instalëjë systemã na twòji cwiadri place
Comment[da]=Installér dette system permanent på din harddisk
Comment[de]=Dieses System dauerhaft auf der Festplatte installieren
Comment[el]=Εγκαταστήστε αυτό το σύστημα μόνιμα στο σκληρό σας δίσκο
Comment[eo]=Instali la sistemon permanente en via disko
Comment[es]=Instalar este sistema permanentemente en su disco duro
Comment[et]=Paigalda see süsteem jäädavalt oma kõvakettale
Comment[eu]=Sistema hau betiko instalatu disko gogorrean
Comment[fa]=نصب دائمی این سیستم بر روی دیسک سخت شما
Comment[fi]=Asenna tämä järjestelmä pysyvästi kiintolevyllesi
Comment[fr]=Installer ce système de façon permanente sur votre disque dur
Comment[fy]=Ynstallear dit systeem permanint op jo hurde skiif.
Comment[ga]=Ionsáigh an córas seo go buan ar do innealra
Comment[gl]=Instalar o sistema de xeito permanente no disco ríxido
Comment[gu]=આ સિસ્ટમ તમારી હાર્ડ ડિસ્ક પર હંમેશ માટે સ્થાપિત કરો
Comment[he]=התקנת המערכת באופן קבוע על הכונן הקשיח
Comment[hi]=इस तंत्र को आपके हार्ड डिस्क में स्थायी रूप से संस्थापित करें
Comment[hr]=Trajno instaliraj sustav na čvrsti disk
Comment[hu]=A rendszer telepítése merevlemezre
Comment[hy]=մշտականապես տեղադրել այս համակարգը ձեր կոշտ սկավառակի վրա
Comment[id]=Pasang sistem ini secara permanen ke disk Anda
Comment[is]=Setja þetta kerfi varanlega upp á harða diskinn
Comment[it]=Installa questo sistema in modo permanente sul disco rigido
Comment[ja]=このシステムをハードディスクにインストールします
Comment[ka]=მოცემული სისტემის მყარ დისკზე ჩადგმა
Comment[kk]=Жүйені қатқыл дискіңізге тұрақты орнату
Comment[ko]=이 시스템을 여러분의 하드 디스크에 영구히 설치합니다
Comment[ku]=Sîstemê di hard dîskê xwe de saz bike
Comment[lb]=Installéier de System permanent op d'Festplack
Comment[lt]=Įdiegti Linux operacinę sistemą į kompiuterio (standųjį) diską
Comment[lv]=Instalēt šo sistēmu cietajā diskā
Comment[mk]=Инсталирајте го системот трајно на Вашиот тврд диск
Comment[ms]=Pasang sistem ini dengan kekal ke cakera keras anda
Comment[nb]=Installer dette systemet på harddisken din
Comment[ne]=यो प्रणाली तपाईको हार्ड डिस्कमा स्थाई रुपमा प्रतिस्थापन गर्नुहोस्
Comment[nl]=Dit systeem definitief op uw harde schijf installeren
Comment[nn]=Installér dette systemet på harddisken din
Comment[no]=Installer dette systemet permanent på din harddisk
Comment[oc]=Installar aqueste sistèma d'un biais permanent sus vòstre disc dur
Comment[pl]=Zainstaluj system na dysku twardym
Comment[pt]=Instalar este sistema permanentemente no seu disco rígido
Comment[pt_BR]=Instalar este sistema de maneira permanente no seu disco rígido
Comment[ro]=Instalează acest sistem pe discul calculatorului
Comment[ru]=Установить эту систему на жёсткий диск
Comment[sd]=هي سسٽم مسقلًا هارڊ ڊسڪ ۾ انسٽال ڪيو
Comment[sk]=Nainštalovať systém natrvalo na pevný disk
Comment[sl]=Trajno namesti sistem na vaš trdi disk
Comment[sq]=Instalo këtë sistem përgjithmonë në Hard Disk
Comment[sr]=Инсталирајте овај систем трајно на ваш хард диск
Comment[sv]=Installera detta system permanent på din hårddisk
Comment[ta]=இந்த நிலையை நிரந்தரமாக தங்களது கணினியில் நிறுவுக
Comment[tg]=Ин системро ба диски сахт ба таври доимӣ барпо кунед
Comment[th]=ติดตั้งระบบนี้อย่างถาวรลงบนฮาร์ดดิสก์ของคุณ
Comment[tl]=Iluklok ng permanente ang systema sa iyong hard disk
Comment[tr]=Bu sistemi sabit diskinize kalıcı olarak kurun
Comment[uk]=Встановити цю систему на жорсткий диск
Comment[vi]=Cài hệ thống vào đĩa cứng của bạn
Comment[zh_CN]=将这个系统永久安装在您的硬盘上
Comment[zh_HK]=安裝系統到您的硬碟
Comment[zh_TW]=將此系統安裝到您的硬碟中
Exec=ubiquity --desktop %k gtk_ui
Icon=ubiquity
Terminal=false
Categories=GTK;System;Settings;
OnlyShowIn=GNOME;XFCE;
#X-Ubuntu-Gettext-Domain=ubiquity-desktop
EOF
sudo chown ros:ros /home/ros/Desktop/ubiquity-gtkui.desktop
sudo chown ros:ros /home/ros/Desktop
sudo chmod a+rw /home/ros/Desktop/ubiquity-gtkui.desktop

echo "Add clean-up script"
cat > /root/on_install.sh <<EOF
#!/bin/bash
echo "Delete icon"
rm /home/turtlebot/Desktop/ubiquity-gtkui.desktop
echo "Delete persistent rules"
echo "" > /etc/udev/rules.d/70-persistent-net.rules
echo "" > /etc/udev/rules.d/70-persistent-cd.rules
EOF
chmod a+wrx /root/on_install.sh

echo "Adding .bashrc"
cp /etc/skel/.bashrc /home/ros/.bashrc
cat >> /home/ros/.bashrc <<EOF
if [ -f /opt/ros/diamondback/setup.bash ] ; then
    source /opt/ros/diamondback/setup.bash
else
    echo "ROS is not installed yet. After installing, please"
    echo "source your .bashrc again by typing:"
    echo "source ~/.bashrc"
fi
EOF
sudo chown ros:ros /home/ros/.bashrc
sudo chmod a+rw /home/ros/.bashrc

echo "Installing ros"
yes | apt-get install ros-diamondback-all



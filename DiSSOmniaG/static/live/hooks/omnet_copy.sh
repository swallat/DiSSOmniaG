#!/bin/sh

#set -e

# Uncomment to debug
#set -n

# Uncomment to enable simple command printing
set -x

user=user
execDir=/home/${user}
omnetHome=${execDir}/OMNeT
inetHome=${execDir}/INET

adduser --home /home/$user --quiet --gecos ,,,, --disabled-password $user
usermod -G sudo,$user $user

aptitude install -y gcc g++ bison flex perl tcl-dev tk-dev blt libxml2-dev zlib1g-dev openjdk-6-jre doxygen graphviz openmpi-bin libopenmpi-dev libpcap-dev

# Export environment parameter
export omnetpp_root=${omnetHome}
export PATH=$omnetpp_root/bin:$PATH
export LD_LIBRARY_PATH=$omnetpp_root/lib:$LD_LIBRARY_PATH
export TCL_LIBRARY=/usr/share/tcltk/tcl8.4

cmd1="export omnetpp_root=$omnetHome"
cmd2="export PATH=/sbin:\$omnetpp_root/bin:\$PATH"
cmd3="export LD_LIBRARY_PATH=\$omnetpp_root/lib:\$LD_LIBRARY_PATH"
cmd4="export TCL_LIBRARY=/usr/share/tcltk/tcl8.4"
cmd5="alias sudo='sudo env PATH=\$PATH'"

# Write exports to users .bashrc
echo $cmd1 >> $execDir/.bashrc
echo $cmd2 >> $execDir/.bashrc
echo $cmd3 >> $execDir/.bashrc
echo $cmd4 >> $execDir/.bashrc
echo $cmd5 >> $execDir/.bashrc

# Write exports to roots .bashrc
echo $cmd1 >> /root/.bashrc
echo $cmd2 >> /root/.bashrc
echo $cmd3 >> /root/.bashrc
echo $cmd4 >> /root/.bashrc

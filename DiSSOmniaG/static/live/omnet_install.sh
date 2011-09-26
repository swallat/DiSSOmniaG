#!/bin/sh

set -e

# Uncomment to debug
#set -n

# Uncomment to enable simple command printing
set -x

user=user
execDir=/home/${user}
omnetHome=${execDir}/OMNET
inetHome=${execDir}/INET
omnetTarball=omnetpp-4.1-src.tgz
inetTarball=inet-20110225-src.tgz
pathToOmnetTarball=/usr/share/omnet/$omnetTarball
pathToInetTarball=/usr/share/omnet/$inetTarball
noWget=0
omnetDownload=http://omnetpp.org/download/release/$omnetTarball
inetDownload=http://omnetpp.org/download/contrib/models/$inetTarball

adduser --home /home/user --quiet --gecos ,,,, --disabled-password $user
usermod -G sudo,$user $user

if [ ! -d $omnetHome ]
then
  mkdir -p ${omnetHome}
  chown ${user}: ${omnetHome}
fi

cd $omnetHome

if [ ! -d $inetHome ]
then
    mkdir -p ${inetHome}
    chown ${user}: ${inetHome}
fi

# Export environment parameter
export omnetpp_root=${omnetHome}
export PATH=$omnetpp_root/bin:$PATH
export LD_LIBRARY_PATH=$omnetpp_root/lib:$LD_LIBRARY_PATH
export TCL_LIBRARY=/usr/share/tcltk/tcl8.4

cmd1="export omnetpp_root=$omnetHome"
cmd2="export PATH=\$omnetpp_root/bin:\$PATH"
cmd3="export LD_LIBRARY_PATH=\$omnetpp_root/lib:\$LD_LIBRARY_PATH"
cmd4="export TCL_LIBRARY=/usr/share/tcltk/tcl8.4"
cmd5="alias sudo=\'sudo env PATH=$PATH\'"

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

#Test for wget
dpkg -s wget
if (($?))
then
    echo "No wget installed"
    noWget=1
fi

if [ ! -e $pathToOmnetTarball ]
then
    wget $omnetDownload
    if (($?))
    then
	echo "Could not download Omnet++ tarball"
    fi
else
    cp $pathToOmnetTarball ./
fi

tar xvf $omnetTarball
mv omnetpp-4.1 $omnetHome/omnet

rm $omnetTarball

mv omnet/* ./

./configure
if (($?))
then
    echo './configure failed'
    exit -1
fi

make
if (($?))
then
    echo 'make failed'
    exit -1
fi

make install-menu-item

make install-desktop-icon

## INET installation

cd $inetHome

if [ ! -e $pathToInetTarball ]
then
    wget $inetDownload
    if (($?))
    then
	echo "Could not download INET tarball"
	fi
else
    cp $pathToInetTarball ./
fi

tar xvf $inetTarball
mv inet/* ./
mv inet/.* ./
rm -rf inet
rm -f $inetTarball

mv Makefile Makefile.bak
sed '
/.*cd src && opp_makemake -f --deep --make-so -o inet -O out $$NSC_VERSION_DEF/ c\
\tcd src && opp_makemake -f --deep --make-so -o inet -O out $$NSC_VERSION_DEF opp_makemake -f --deep -lpcap -DHAVE_PCAP --make-so -o inet -O out $$NSC_VERSION_DEF
' Makefile.bak > Makefile && rm Makefile.bak

make makefiles
cd src
mv Makefile Makefile.bak && sed '
/HAVE_PCAP=no/ c\
#HAVE_PCAP=no
' Makefile.bak > Makefile && rm Makefile.bak

cd ,,

make
if (($?))
then
    echo "make Inet failed"
    exit -1
fi

mkdir -p $inetHome/examples/KN1
cd $execDir/Desktop
ln -s $inetHome/examples/KN1 KN1

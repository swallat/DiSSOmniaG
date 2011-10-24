#!/bin/sh

#set -e

# Uncomment to debug
#set -n

# Uncomment to enable simple command printing
set -x

user=user

adduser --home /home/$user --quiet --gecos ,,,, --disabled-password $user
usermod -G sudo,$user $user

ln -s /usr/share/dissomniag-live/dissomniag_live.py /usr/sbin/dissomniag_live

update-rc.d dissomniag_live defaults 99
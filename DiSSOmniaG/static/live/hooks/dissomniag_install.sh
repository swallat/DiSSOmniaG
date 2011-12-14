#!/bin/sh
# DiSSOmniaG (Distributed Simulation Service wit OMNeT++ and Git)
# Copyright (C) 2011, 2012 Sebastian Wallat, University Duisburg-Essen
# 
# Based on an idea of:
# Sebastian Wallat <sebastian.wallat@uni-due.de, University Duisburg-Essen
# Hakim Adhari <hakim.adhari@iem.uni-due.de>, University Duisburg-Essen
# Martin Becke <martin.becke@iem.uni-due.de>, University Duisburg-Essen
#
# DiSSOmniaG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DiSSOmniaG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with DiSSOmniaG. If not, see <http://www.gnu.org/licenses/>

#set -e

# Uncomment to debug
#set -n

# Uncomment to enable simple command printing
set -x

user=user

adduser --home /home/$user --quiet --gecos ,,,, --disabled-password $user
usermod -G sudo,$user $user

aptitude install -y python3-dev python3-setuptools

easy_install3 setproctitle

ln -s /usr/share/dissomniag-live/dissomniag_live.py /usr/sbin/dissomniag_live

update-rc.d dissomniag_live defaults 99
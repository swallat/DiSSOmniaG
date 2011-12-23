#!/usr/bin/env bash
# -*- coding: utf-8 -*-
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
set -x
chdir DiSSOmniaG_liveClient

sshKeyFile=/home/sw/.ssh/id_rsa.pub
ip=10.11.0.105
tarBallName=dissomniagLive.tar.gz
targetFolder=/usr/share/dissomniag-live/

#Add ssh Key on remote
ssh-copy-id -i $sshKeyFile root@$ip

./createLiveDaemonTarBall.py

scp $tarBallName root@$ip:

ssh root@$ip tar xvfz $tarBallName -C /

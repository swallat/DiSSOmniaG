#!/usr/bin/env bash
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
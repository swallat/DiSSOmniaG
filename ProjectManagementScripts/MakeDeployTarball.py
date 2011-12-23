#!/usr/bin/env python3
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
import os, shutil, sys
import subprocess, shlex
import tarfile

actualPath = os.path.abspath(os.getcwd())
print("Actual Path %s" %actualPath)
try:
    os.chdir("Deployment")
except OSError:
    print("Could not create Tarbal: No such subfolder Deployment")
    sys.exit(-1)

deploymentDir = os.path.abspath(os.getcwd())
print("deploymentDir %s" %deploymentDir)
dissomniagBaseDir = os.path.abspath(os.path.join(actualPath, "DiSSOmniaG"))
print("dissomniagBaseDir %s" %dissomniagBaseDir)
baseDirName = "Deployment/TarTemp"
print("baseDirName %s" %baseDirName)
baseBuildDir = os.path.abspath(os.path.join(actualPath, baseDirName))
print("baseBuildDir %s" %baseBuildDir)
tarFileName = "dissomniag.tar.gz"
print("tarFileName %s" %tarFileName)

dissomniagLiveFolder = os.path.join(baseBuildDir, "usr/share/dissomniag/")
print("dissomniagLiveFolder %s" %dissomniagLiveFolder)
initDFolder = os.path.join(baseBuildDir, "etc/init.d/")
print("initDFolder %s" %initDFolder)
liveFolder = os.path.join(baseBuildDir, "var/lib/dissomniag/")
print("liveFolder %s" %liveFolder)
confFolder = os.path.join(baseBuildDir, "etc/dissomniag/")

ignore_set = set(["createLiveDaemonTarBall.py", baseDirName, tarFileName, ".pydevproject", ".project", "log", "key.pem", "cert.pem", ".gitignore", "dissomniag.db", "htpasswd", "info.file", "linesOfCode.py", "privatekey.pem", "ssh_key", "ssh_key.pub"])  

def createBuildDir():
    os.makedirs(dissomniagLiveFolder, 0o755)
    os.makedirs(initDFolder, 0o755)
    os.makedirs(liveFolder, 0o755)
    os.makedirs(confFolder, 0o755)
    
def copyFilesToBuildDir():
    #1. Copy Daemon Files
 
    listing = os.listdir(dissomniagBaseDir)
    os.chdir(dissomniagBaseDir)
    for obj in listing:
        if obj in ignore_set:
            continue
        else:
            if os.path.isdir(obj):
                shutil.copytree(obj, os.path.join(dissomniagLiveFolder, obj), symlinks = False, ignore=shutil.ignore_patterns('*.pyc', 'tmp*', '*.log'))
            else:
                shutil.copy2(obj, dissomniagLiveFolder)
            
            
    #2. Copy init.d File
    os.chdir(actualPath)
    shutil.copy2(os.path.abspath("Deployment/init.d/dissomniag"), initDFolder)

    #3. copy Sample Conf
    shutil.copy2(os.path.abspath("Deployment/dissomniag.conf.sample"), confFolder)
    
def createLiveTarball():
    
    tarBallName = "dissomniagLive.tar.gz"
    destDir = "DiSSOmniaG/static/live/liveDaemon"
    srcDir = "DiSSOmniaG_liveClient"
    
    dstTarball = os.path.join(destDir, tarBallName)
    srcTarball = os.path.join(srcDir, tarBallName)
    try:
        try:
            os.remove(dstTarball)
        except Exception:
            pass
        os.chdir(actualPath)
        print(os.getcwd())
        cmd = os.path.abspath("createLiveDaemonTarBall.py")
        proc = subprocess.call(cmd)
        shutil.copy2(srcTarball, destDir)
    except OSError as e:
        print("Could not create live Client Tarball. %s" %str(e))
    finally:
        os.chdir(deploymentDir)
    

def createTarFile():
    os.chdir(baseDirName)
    with tarfile.open(tarFileName, "w:gz") as tar:
        listing = os.listdir("./")
        for infile in listing:
            if infile not in ignore_set:
                tar.add(infile)
                
    shutil.copy2(tarFileName, "../")
    os.chdir("../")

def cleanUp():
    try:
        shutil.rmtree(baseBuildDir)
    except Exception:
        print("Clean failed")
        exit(-1)

def deleteOldTarFile():
    try:
        shutil.rmtree(os.path.abspath(tarFileName))
    except Exception:
        pass

if __name__ == '__main__':
    os.chdir("../")
    failed = False
    try:
        deleteOldTarFile()
        createBuildDir()
        createLiveTarball()
        copyFilesToBuildDir()
        createTarFile()
    except Exception as e:
        failed = True
        print(str(e))
    finally:
        cleanUp()
        if failed:
            exit(-1)
        else:
            exit(0)

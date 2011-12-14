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
import logging, argparse
from colorama import Fore, Style, Back
import sys, time
import getpass
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import dissomniag
from dissomniag.utils import CliMethodABCClass
from dissomniag import taskManager

log = logging.getLogger("cliApi.ManageJobs")


class CliJobs(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = 'View or delete jobs.', prog = args[0])
        parser.add_argument("-r", "--running", action = "store_true", dest = "onlyRunning", default = False, help = "Show only currently running jobs.")
        parser.add_argument("-f", "--finished", action = "store_true", dest = "onlyFinished", default = False, help = "Show only finished Jobs.")
        parser.add_argument("-i", "--jobId", action = "store", dest = "jobId", type = int, default = None, help = "Show only the Job with the ID: -i <ID>. \n(with -c delete the job with the id -i <ID>)")
        parser.add_argument("-t", "--trace", action = "store_true", dest = "trace", default = False, help = "Show Jobs with Trace.")
        parser.add_argument("-c", "--clear", action = "store_true", dest = "clear", default = False, help = "Clear Job List of the User.")
        if self.user.isAdmin:
            parser.add_argument("-a", "--all", action = "store_true", dest = "allUser", default = False, help = "Show Jobs of all users or clear all Jobs.")
            parser.add_argument("-u", "--user", action = "store", dest = "userName", default = None, help = "Show Jobs of User or clear Jobs of user: -u <userName>")
            parser.add_argument("-z", "--zombi", action = "store_true", dest = "zombi", default = False, help = "Show Zombi Processes, or delete Zombi Processes. A Zombi Job is a Job without a user.")
        options = parser.parse_args(list(args[1:]))
        
        ###################
        # Debug Help
        #
        #runningStr = "True" if options.onlyRunning else "False"
        #finishedStr = "True" if options.onlyFinished else "False"
        #jobIdStr = 0 if options.jobId == None else int(options.jobId)
        #traceStr = "True" if options.trace else "False"
        #clearStr = "True" if options.clear else "False"
        #self.printInfo("Only Running %s, Only Finished %s, JobId %d, Trace %s, Clear %s" % (runningStr, finishedStr, jobIdStr, traceStr, clearStr))
        #if self.user.isAdmin:
        #    allStr = "True" if options.allUser else "False"
        #    userStr = "None" if options.userName == None else str(options.userName)
        #    zombiStr = "True" if options.zombi else "False"
        #    self.printInfo("All %s, User %s, Zombi %s" % (allStr, userStr, zombiStr))
        #
        # End Debug Help
        ###################
        
        if self.user.isAdmin:
            if options.clear:
                self._clearAdmin(jobId = options.jobId, allUser = options.allUser, userName = options.userName, zombi = options.zombi)
            else:
                self._printAdmin(onlyRunning = options.onlyRunning, onlyFinished = options.onlyFinished, jobId = options.jobId, trace = options.trace, allUser = options.allUser, userName = options.userName, zombi = options.zombi)
        else:
            if options.clear:
                self._clearUser(jobId = options.jobId)
            else:
                self._printUser(onlyRunning = options.onlyRunning, onlyFinished = options.onlyFinished, jobId = options.jobId, trace = options.trace)

    def _printJobs(self, jobs, trace = False):
        if jobs == None:
            self.printInfo("No Jobs available")
        else:
            session = dissomniag.Session()
            for job in jobs:
                session.expire(job)
                if job.endTime == None:
                    endTime = "not defined"
                else:
                    endTime = str(job.endTime)
                    
                self.printInfo("Job ID: %d, Job status: %s, startTime: %s, endTime: %s" % (job.id, taskManager.jobs.JobStates.getStateName(job.state), job.startTime, endTime))
                self.printInfo("Description: %s" % job.description)
                if job.user != None:
                    self.printInfo("User: %s" % job.user.username)
                if trace:
                    self.printInfo("Trace:")
                    self.printInfo(job.trace)
                print("\n")
    
    def _printUser(self, onlyRunning = False, onlyFinished = False, jobId = None, trace = False):
        return self._printAdmin(onlyRunning = onlyRunning, onlyFinished = onlyFinished, jobId = jobId, trace = trace, \
                    allUser = False, userName = None, zombi = False)
    
    def _printAdmin(self, onlyRunning = False, onlyFinished = False, jobId = None, \
                    trace = False, allUser = False, userName = None, zombi = False):
        
        if allUser:
            if self.user.isAdmin:
                if zombi:
                    if not onlyFinished and not onlyRunning:
                        return self._printJobs(taskManager.Job.getJobs(user = self.user, withZombi = True, exclusiveZombi = True, withRunning = True, exclusiveRunning = False), trace)
                    elif not onlyFinished and onlyRunning:
                        return self._printJobs(taskManager.Job.getJobs(user = self.user, withZombi = True, exclusiveZombi = True, withRunning = True, exclusiveRunning = True), trace)
                    elif onlyFinished and not onlyRunning:
                        return self._printJobs(taskManager.Job.getJobs(user = self.user, withZombi = True, exclusiveZombi = True, withRunning = False, exclusiveRunning = False), trace)
                    else:
                        self.printError("Please check your parameters. You cannot request both only finished Jobs and only running Jobs.")
                        return
                else:
                    if not onlyFinished and not onlyRunning:
                        return self._printJobs(taskManager.Job.getJobs(user = self.user, withZombi = True, exclusiveZombi = False, withRunning = True, exclusiveRunning = False), trace)
                    elif not onlyFinished and onlyRunning:
                        return self._printJobs(taskManager.Job.getJobs(user = self.user, withZombi = True, exclusiveZombi = False, withRunning = True, exclusiveRunning = True), trace)
                    elif onlyFinished and not onlyRunning:
                        return self._printJobs(taskManager.Job.getJobs(user = self.user, withZombi = True, exclusiveZombi = False, withRunning = False, exclusiveRunning = False), trace)
                    else:
                        self.printError("Please check your parameters. You cannot request both only finished Jobs and only running Jobs.")
                        return
            else:
                self.printError("You have not the permissions to do that. Go away.")
                return
               
        elif jobId != None:
            if self.user.isAdmin:
                return self._printJobs((taskManager.Job.getJobViaId(user = self.user, jobId = jobId, withZombi = True, exclusiveZombi = False, withRunning = True, exclusiveRunning = False),), trace)
            else:
                job = taskManager.Job.getJobViaId(user = self.user, jobId = jobId, withZombi = False, exclusiveZombi = False, withRunning = True, exclusiveRunning = False)
                if job.user_id == self.user.id:
                    return self._printJobs((job,), trace)
                else:
                    self.printError("You don't have the permissions to do this")
        else:
            #Print a group of Jobs
            if self.user.isAdmin:
                if zombi and userName == None:
                    if not onlyFinished and not onlyRunning:
                        return self._printJobs(taskManager.Job.getJobs(user = self.user, withZombi = True, exclusiveZombi = True, withRunning = True, exclusiveRunning = False), trace)
                    elif not onlyFinished and onlyRunning:
                        return self._printJobs(taskManager.Job.getJobs(user = self.user, withZombi = True, exclusiveZombi = True, withRunning = True, exclusiveRunning = True), trace)
                    elif onlyFinished and not onlyRunning:
                        return self._printJobs(taskManager.Job.getJobs(user = self.user, withZombi = True, exclusiveZombi = True, withRunning = False, exclusiveRunning = False), trace)
                    else:
                        self.printError("Please check your parameters. You cannot request both only finished Jobs and only running Jobs.")
                        return
                elif userName != None and not zombi:
                    if not onlyFinished and not onlyRunning:
                        return self._printJobs(taskManager.Job.getJobsViaUser(user = self.user, userName = userName, withRunning = True, exclusiveRunning = False), trace)
                    elif not onlyFinished and onlyRunning:
                        return self._printJobs(taskManager.Job.getJobsViaUser(user = self.user, userName = userName, withRunning = True, exclusiveRunning = True), trace)
                    elif onlyFinished and not onlyRunning:
                        return self._printJobs(taskManager.Job.getJobsViaUser(user = self.user, userName = userName, withRunning = False, exclusiveRunning = False), trace)
                    else:
                        self.printError("Please check your parameters. You cannot request both only finished Jobs and only running Jobs.")
                        return
                elif userName != None and zombi:
                    self.printError("Please check your parameters. You can not enter both a userName and look up only zombies.")
                    return 
                    
            # Show Jobs of of self User
            if not onlyFinished and not onlyRunning:
                return self._printJobs(taskManager.Job.getJobsViaUser(user = self.user, userName = None, withRunning = True, exclusiveRunning = False), trace)
            elif not onlyFinished and onlyRunning:
                return self._printJobs(taskManager.Job.getJobsViaUser(user = self.user, userName = None, withRunning = True, exclusiveRunning = True), trace)
            elif onlyFinished and not onlyRunning:
                return self._printJobs(taskManager.Job.getJobsViaUser(user = self.user, userName = None, withRunning = False, exclusiveRunning = False), trace)
            else:
                self.printError("Please check your parameters. You cannot request both only finished Jobs and only running Jobs.")
                return
                
    
    def _clearUser(self, jobId = None):
        return self._clearAdmin(jobId = jobId, userName = None, allUser = False, zombi = False)
    
    def _clearAdmin(self, jobId = None, userName = None, allUser = False, zombi = False):
        if allUser and not zombi and jobId == None:
            if self.user.isAdmin:
                if taskManager.Job.cleanUpJobDb(user = self.user):
                    self.printSuccess("All not running jobs were deleted.")
                    return
                else:
                    self.printInfo("No jobs were deleted.")
                    return
            else:
                self.printError("You have not the permissions to do that. Go away.")
                return
        elif jobId != None and not zombi and not allUser:
            if taskManager.Job.cleanUpJobDbViaId(user = self.user, jobId = jobId):
                self.printSuccess("The Job with the Id %d was successfully deleted." % jobId)
                return
            else:
                self.printInfo("No Jobs were deleted. You have either not the permissions to delete this job or, there were no job.")
                return             
        elif zombi and jobId == None and not allUser:
            if taskManager.Job.cleanUpJobDbViaZombi(user = self.user):
                self.printSuccess("All not running zombi jobs were deleted.")
                return
            else:
                self.printInfo("No Jobs were deleted. You have either not the permissions to delete zombi jobs or, there were no zombi jobs.")
                return                 
        elif not zombi and jobId == None and not allUser:
            if self.user.isAdmin and userName != None:
                if taskManager.Job.cleanUpJobDbViaUser(user = self.user, userName = userName):
                    self.printSuccess("All not running jobs of user %s were deleted." % userName)
                    return
                else:
                    self.printSuccess("No jobs were deleted for user %s." % userName)
                    return
            elif userName == None:
                if taskManager.Job.cleanUpJobDbViaUser(user = self.user, userName = None):
                    self.printSuccess("All not running jobs of user %s were deleted." % self.user.username)
                    return
                else:
                    self.printSuccess("No jobs were deleted for user %s." % self.user.username)
                    return
            else:
                self.printError("You do not have the right permissions to do that. Go away!")
                return
        else:
            self.printError("The parameter combination you have entered is not valid. (Delete)")
            return
    
            
    
class stopJob(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        parser = argparse.ArgumentParser(description = 'Stop a job.', prog = args[0])
        parser.add_argument("jobId", action = "store")
        options = parser.parse_args(list(args[1:]))
        
        jobId = int(options.jobId)
        job = taskManager.Dispatcher.getJob(user = self.user, jobId = jobId)
        if job:
            if not self.user.isAdmin and self.user != job.user:
                self.printError("You are not allowed to delete this Job. Go away.")
                return
            else: 
                taskManager.Dispatcher.cancelJob(user = self.user, jobId = jobId)
                self.printSuccess("Job Cancel Request sended")
                return
        else:
            self.printError("JobId is not valid, or Job is no longer handled by the Dispatcher.")
        
        session = dissomniag.Session()
        try:
            job = session.query(taskManager.jobs.JobInfo).filter(taskManager.jobs.JobInfo.id == jobId).filter(taskManager.jobs.JobInfo.state.in_(taskManager.jobs.JobStates.getRunningStates())).one()
            job.state = taskManager.jobs.JobStates.CANCELLED
            dissomniag.saveCommit(session)
            self.printInfo("Job canceled without using ")
        except (NoResultFound, MultipleResultsFound):
            self.printError("Could also not cancel Job in other Job List")
                
            

class addDummyJob(CliMethodABCClass.CliMethodABCClass):
    
    def implementation(self, *args):
        sys.stdout = self.terminal
        sys.stderr = self.terminal
        
        if not self.user.isAdmin:
            self.printError("You are not allowed to use this programm! Go away!")
            return
        
        parser = argparse.ArgumentParser(description = 'Add a dummy Job with a Time', prog = args[0])
        parser.add_argument("-t", "--time", action = "store", dest = "time", default = 10)
        parser.add_argument("-z", "--zombi", action = "store_true", dest = "zombi", default = False)
        parser.add_argument("-i", "--independent", action = "store_true", dest = "independent", default = False)
        options = parser.parse_args(list(args[1:]))
        
        context = taskManager.Context()
        context.timeToSleep = int(options.time)
        if options.zombi:
            job = taskManager.Job(context = context, description = "Just a dummy Job with a specific Time.")
        else:
            job = taskManager.Job(context = context, description = "Just a dummy Job with a specific Time.", user = self.user)
        job.addTask(DummyTask())
        job.addTask(DummyTask())
        jobId = job.id
        if options.independent:
            taskManager.Dispatcher.addJobIndependent(user = self.user, job = job)
        else:
            taskManager.Dispatcher.addJob(user = self.user, job = job)
        self.printSuccess("Your job have the ID %d" % jobId)
        
class DummyTask(taskManager.AtomicTask):
    
    def run(self):
        timeToSleep = self.context.timeToSleep
        time.sleep(timeToSleep)
        return True
    
    def revert(self):
        return True
        

# -*- coding: utf-8 -*-
'''
Created on 17.11.2011

@author: Sebastian Wallat
'''
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import ipaddr, random

import dissomniag
from dissomniag.model import *

user_app = sa.Table('user_app', dissomniag.Base.metadata,
                       sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), primary_key = True),
                       sa.Column('key_id', sa.Integer, sa.ForeignKey('apps.id'), primary_key = True),
)

class AppVmRelation(dissomniag.Base):
    __tablename__= 'app_vm'
    app_id = sa.Column(sa.Integer, sa.ForeignKey('apps.id'), primary_key = True)
    vm_id = sa.Column(sa.Integer, sa.ForeignKey('vms.id'), primary_key = True)
    vm = orm.relationship("VM", backref="AppVmRelations")
    lastSeen = sa.Column(sa.DateTime)
    state = sa.Column(sa.String)
    log = sa.Column(sa.String)
    
    def __init__(self, app, vm):
        self.app = app
        self.vm = vm
        
        session = dissomniag.Session()
        session.add(self)
        dissomniag.saveCommit(session)
        
    def authUser(self, user):
        return self.app.authUser(user)
    
    @staticmethod
    def createRelation(user, app, vm):
        if app.authUser(user) and vm.authUser(user):
            return AppVmRelation(app, vm)
    
    @staticmethod
    def deleteRelation(user, relation, totalDeleteApp = False, triggerPush = True):
        relation.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(relation, "appVmRel")
        job = dissomniag.taskManager.Job(context, "Delete a App VM relation", user = user)
        #1. Delete VM Remotely
        job.addTask(dissomniag.tasks.DeleteAppOnVmRemote())
        #2. Delete Git Branch
        if not totalDeleteApp:
            job.addTask(dissomniag.tasks.DeleteAppVMRelationInGit())
        #3. Add Delete Task
        job.addTask(dissomniag.tasks.DeleteAppVMRelation())
        if triggerPush:
            job.addTask(dissomniag.tasks.GitPushAdminRepo())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, syncObj = dissomniag.GitEnvironment(), job = job)
        return True


class App(dissomniag.Base):
    __tablename__ = 'apps'
    id = sa.Column(sa.Integer, primary_key = True)
    name = sa.Column(sa.String(20), nullable = False)
    AppVmRelations = orm.relationship("AppVmRelation", backref="app")
    users = orm.relationship("User", secondary=user_app, backref="apps")
    
    def __init__(self, user, name):
        self.users.append(user)
        self.name = name
        
        session = dissomniag.Session()
        session.add(self)
        dissomniag.saveCommit(session)
        
    def authUser(self, user):
        if (hasattr(user, "isAdmin") and user.isAdmin) or user in self.users or user.id == self.maintainUser.id:
            return True
        raise dissomniag.UnauthorizedFunctionCall()
    
    def addUser(self, user, userToAdd):
        self.authUser(user)
        if not userToAdd in self.users:
            self.users.append(userToAdd)
    
    @staticmethod
    def delApp(user, app):
        app.authUser(user)
        
        #1. Delete all Relations
        for rel in app.AppVmRelations:
            AppVmRelation.deleteRelation(user, app, totalDeleteApp = True, triggerPush = False)
            
        #2. Delete all Users
        for mUser in app.users:
            App.deleteUserFromApp(user, app, mUser, triggerPush = False)
            
        context = dissomniag.taskManager.Context()
        context.add(app, "app")
        job = dissomniag.taskManager.Job(context, "Delete a App", user = user)
        job.addTask(dissomniag.tasks.DeleteAppRepository())
        job.addTask(dissomniag.tasks.DeleteAppFinally())
        job.addTask(dissomniag.tasks.GitPushAdminRepo())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, syncObj = dissomniag.GitEnvironment(), job = job)
        return True
    
    @staticmethod
    def delUserFromApp(user, app, userToDelete, triggerPush = True):
        app.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(app, "app")
        context.add(userToDelete, "user")
        job = dissomniag.taskManager.Job(context, "Delete a user from a app", user = user)
        job.addTask(dissomniag.tasks.DeleteUserFromApp())
        if triggerPush:
            job.addTask(dissomniag.tasks.GitPushAdminRepo())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, syncObj = dissomniag.GitEnvironment(), job = job)
    
    @staticmethod
    def delVmFromApp(user, app, vm, triggerPush = True):
        app.authUser(user)
        for rel in app.AppVmRelations:
            if rel.vm == vm:
                return AppVmRelation.deleteRelation(user, rel, triggerPush = False)
        context = dissomniag.taskManager.Context()
        job = dissomniag.taskManager.Job(context, "Commit admin Repo", user = user)
        job.addTask(dissomniag.tasks.GitPushAdminRepo())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, syncObj = dissomniag.GitEnvironment(), job = job)
        
        return False

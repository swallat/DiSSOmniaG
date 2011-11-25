# -*- coding: utf-8 -*-
'''
Created on 17.11.2011

@author: Sebastian Wallat
'''
import threading
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

class AppLiveCdRelation(dissomniag.Base):
    __tablename__= 'app_livecd'
    app_id = sa.Column(sa.Integer, sa.ForeignKey('apps.id'), primary_key = True)
    liveCd_id = sa.Column(sa.Integer, sa.ForeignKey('livecds.id'), primary_key = True)
    liveCd = orm.relationship("LiveCd", backref="AppLiveCdRelations")
    lastSeen = sa.Column(sa.DateTime)
    state = sa.Column(sa.String)
    log = sa.Column(sa.String)
    
    def __init__(self, app, liveCd):
        self.app = app
        self.liveCd = liveCd
        
        session = dissomniag.Session()
        session.add(self)
        dissomniag.saveCommit(session)
        
        
    def authUser(self, user):
        return self.app.authUser(user)
    
    @staticmethod
    def createRelation(user, app, liveCd):
        if app.authUser(user) and liveCd.authUser(user):
            try:
                session = dissomniag.Session()
                rels = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.liveCd == liveCd).filter(dissomniag.model.AppLiveCdRelation.app == app).one()
            except NoResultFound:
                rel = AppLiveCdRelation(app, liveCd)
                context = dissomniag.taskManager.Context()
                context.add(app, "app")
                context.add(liveCd, "liveCd")
                job = dissomniag.taskManager.Job(context, "Create initially an AppLiveCdRelation", user)
                job.addTask(dissomniag.tasks.AddAppBranch())
                job.addTask(dissomniag.tasks.GitPushAdminRepo())
                dissomniag.taskManager.Dispatcher.addJobSyncronized(user, dissomniag.GitEnvironment(), job)
                return rel
            except MultipleResultsFound:
                first = True
                rels = session.query(dissomniag.model.AppLiveCdRelation).filter(dissomniag.model.AppLiveCdRelation.liveCd == liveCd).filter(dissomniag.model.AppLiveCdRelation.app == app).all()
                for rel in rels:
                    if first:
                        first = False
                        continue
                    session.delete(rel)
                dissomniag.saveCommit(session)
            else:
                return rels
                 
    
    @staticmethod
    def deleteRelation(user, relation, totalDeleteApp = False, triggerPush = True):
        relation.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add(relation.app, "app")
        context.add(relation.liveCd, "liveCd")
        job = dissomniag.taskManager.Job(context, "Delete a App LiveCd relation", user = user)
        #1. Delete App on LiveCd Remotely
        job.addTask(dissomniag.tasks.DeleteAppOnLiveCdRemote())
        #2. Add Delete Task
        job.addTask(dissomniag.tasks.DeleteAppLiveCdRelation())
        if triggerPush:
            job.addTask(dissomniag.tasks.GitPushAdminRepo())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, syncObj = dissomniag.GitEnvironment(), job = job)
        return True


class App(dissomniag.Base):
    __tablename__ = 'apps'
    id = sa.Column(sa.Integer, primary_key = True)
    name = sa.Column(sa.String(20), nullable = False, unique = True)
    AppLiveCdRelations = orm.relationship("AppLiveCdRelation", backref="app")
    users = orm.relationship("User", secondary=user_app, backref="apps")
    lock = threading.RLock()
    
    def __init__(self, user, name):
        self.users.append(user)
        self.name = name
        
        session = dissomniag.Session()
        session.add(self)
        dissomniag.saveCommit(session)
        context = dissomniag.taskManager.Context()
        context.add(self, "app")
        job = dissomniag.taskManager.Job(context, "Create initially an App", user)
        job.addTask(dissomniag.tasks.GitPushAdminRepo())
        job.addTask(dissomniag.tasks.MakeInitialCommit())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, dissomniag.GitEnvironment(), job)
        
        
    def multiLog(self, msg, job = None):
        if job != None:
            job.trace(msg)
        log.info(msg)
        
    def authUser(self, user):
        if (hasattr(user, "isAdmin") and user.isAdmin) or user in self.users:
            return True
        for rel in self.AppLiveCdRelation:
            if user == rel.liveCd.vm.maintainUser.id:
                return True
        raise dissomniag.UnauthorizedFunctionCall()
    
    def addLiveCdRelation(self, user, liveCd):
        self.authUser(user)
        AppLiveCdRelation.createRelation(user, self, liveCd)  
    
    def addUser(self, user, userToAdd):
        self.authUser(user)
        if not userToAdd in self.users:
            self.users.append(userToAdd)
        context = dissomniag.taskManager.Context()
        job = dissomniag.taskManager.Job(context, "Update git config", user)
        job.addTask(dissomniag.tasks.GitPushAdminRepo())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, dissomniag.GitEnvironment(), job)
    
    @staticmethod
    def delApp(user, app):
        app.authUser(user)
        
        #1. Delete all Relations
        for rel in app.AppLiveCdRelations:
            AppLiveCdRelation.deleteRelation(user, app, totalDeleteApp = True, triggerPush = False)
            
        context = dissomniag.taskManager.Context()
        context.add(app, "app")
        job = dissomniag.taskManager.Job(context, "Delete a App", user = user)
        job.addTask(dissomniag.tasks.DeleteAppFinally())
        job.addTask(dissomniag.tasks.GitPushAdminRepo())
        dissomniag.taskManager.Dispatcher.addJobSyncronized(user, syncObj = dissomniag.GitEnvironment(), job = job)
        return True
    
    @staticmethod
    def delUserFromApp(user, app, userToDelete, triggerPush = True):
        app.authUser(user)
        
        if not isinstance(userToDelete, dissomniag.auth.User):
            return False
        
        if userToDelete in app.users:
            app.users.remove(userToDelete)
        
        if triggerPush:
            context = dissomniag.taskManager.Context()
            job = dissomniag.taskManager.Job(context, "Delete a user from a app", user = user)
            job.addTask(dissomniag.tasks.GitPushAdminRepo())
            dissomniag.taskManager.Dispatcher.addJobSyncronized(user, syncObj = dissomniag.GitEnvironment(), job = job)
    
    @staticmethod
    def delLiveCdFromApp(user, app, liveCd, triggerPush = True):
        app.authUser(user)
        for rel in app.AppLiveCdRelations:
            if rel.liveCd == liveCd:
                return AppLiveCdRelation.deleteRelation(user, rel, triggerPush)
        return False

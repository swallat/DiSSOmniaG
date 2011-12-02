# -*- coding: utf-8 -*-
'''
Created on 17.11.2011

@author: Sebastian Wallat
'''
import lxml
from lxml import etree
import threading
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import ipaddr, random
import xmlrpclib

import dissomniag
from dissomniag.model import *

user_app = sa.Table('user_app', dissomniag.Base.metadata,
                       sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), primary_key = True),
                       sa.Column('key_id', sa.Integer, sa.ForeignKey('apps.id'), primary_key = True),
)

class AppState:
    INIT = 0
    CLONED = 1
    COMPILED = 2
    STARTED = 3
    CLONE_ERROR = 4
    PULL_ERROR = 5
    COMPILE_ERROR = 6
    RUNTIME_ERROR = 7
    
    @staticmethod
    def isValid(appState):
        if 0 <= appState < 8 and isinstance(appState, int):
            return True
        else:
            return False
    
    @staticmethod
    def getName(appState):
        if appState == AppState.INIT:
            return "INIT"
        elif appState == AppState.CLONED:
            return "CLONED"
        elif appState == AppState.COMPILED:
            return "COMPILED"
        elif appState == AppState.STARTED:
            return "STARTED"
        elif appState == AppState.CLONE_ERROR:
            return "CLONE_ERROR"
        elif appState == AppState.PULL_ERROR:
            return "PULL_ERROR"
        elif appState == AppState.COMPILE_ERROR:
            return "COMPILE_ERROR"
        elif appState == AppState.RUNTIME_ERROR:
            return "RUNTIME_ERROR"
        
class AppActions:
    START = 0
    STOP = 1
    COMPILE = 2
    RESET = 3
    INTERRUPT = 4
    REFRESH_GIT = 5
    REFRESH_AND_RESET = 6
    CLONE = 7
    DELETE = 8
    
    @staticmethod
    def isValid(appState):
        if 0 <= appState < 9 and isinstance(appState, int):
            return True
    
        else:
            return False
    
    @staticmethod
    def getName(appState):
        if appState == AppActions.START:
            return "START"
        elif appState == AppActions.STOP:
            return "STOP"
        elif appState == AppActions.COMPILE:
            return "COMPILE"
        elif appState == AppActions.RESET:
            return "RESET"
        elif appState == AppActions.INTERRUPT:
            return "INTERRUPT"
        elif appState == AppActions.REFRESH_GIT:
            return "REFRESH_GIT"
        elif appState == AppActions.REFRESH_AND_RESET:
            return "REFRESH_AND_RESET"
        elif appState == AppActions.CLONE:
            return "CLONE"
        elif appState == AppActions.DELETE:
            return "DELETE"

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
    
    def updateInfo(self, user, state, log):
        session = dissomniag.Session()
        
        self.authUser(user)
        if AppState.isValid(state):
            self.state = state
            
        if log == None or not isinstance(log, str):
            self.log = ""
        else:
            self.log = log
        dissomniag.saveCommit(session)
        
    def _getActionXml(self, user, action):
        self.authUser(user)
        tree = etree.Element("AppOperate")
        
        tree = self._addCommonInfoToTree(user, tree)
        
        action = etree.SubElement(tree, "action")
        action.text = str(action)
        return tree
    
    def _getAppAddInfo(self, user):
        self.authUser(user)
        tree = etree.Element("app")
        
        return self._addCommonInfoToTree(user, tree)
    
    def _addCommonInfoToTree(self, user, tree):
        self.authUser(user)
        name = etree.SubElement(tree, "name")
        name.text = str(self.app.name)
        
        serverUser = etree.SubElement(tree, "serverUser")
        serverUser.text = str(dissomniag.config.git.gitUser)
        
        serverIpOrHost = etree.SubElement(tree, "serverIpOrHost")
        ident = dissomniag.getIdentity()
        serverIpOrHost.text = str(ident.getMaintainanceIP().addr)
        return tree
    
    def _getServerProxy(self, user):
        self.authUser(user)
        return xmlrpclib.ServerProxy(self.liveCd.vm.getRPCUri(user))
    
    def _getXmlString(self, xml):
        return etree.tostring(xml, pretty_print = True)
    
    def operateOnRemote(self, user, action, scriptName = None, tagOrCommit = None, job = None):
        self.authUser(user)
        if not AppActions.isValid(action):
            raise dissomniag.InvalidAction("Action %s not known." % action)
        
        tree = self._getActionXml(user, action)
        
        if scriptName != None:
            scriptName = etree.SubElement(tree, "scriptName")
            scriptName.text = str(scriptName)
        
        if tagOrCommit != None:
            tagOrCommit = etree.SubElement(tree, "tagOrCommit")
            tagOrCommit.text = str(scriptName)
            
        xmlString = self._getXmlString(tree)
        
        proxy = self._getServerProxy(user)
        
        return proxy.appOperate(xmlString)
    
    def addAppOnRemote(self, user):
        self.authUser(user)
        
        tree = etree.Element("AppAdd")
        tree.append_child(self._getAppAddInfo(user))
        
        xmlString = self._getXmlString(tree)
        
        proxy = self._getServerProxy(user)
        
        return proxy.addApps(xmlString)
        
    
    def deleteAppOnRemote(self, user):
        self.authUser(user)
        tree = self._getActionXml(user, AppActions.DELETE)
        
        xmlString = self._getXmlString(tree)
        
        proxy = self._getServerProxy(user)
        
        return proxy.appOperate(xmlString)
        
    def createStartJob(self, user, scriptName = None, **kwargs):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add("app", self.app)
        context.add("liveCd", self.liveCd)
        context.scriptName = scriptName
        context.action = AppActions.START
        
        job = dissomniag.taskManager.Job(context, "Start an App on a VM", user)
        job.addTask(dissomniag.tasks.operateOnApp())
        return dissomniag.taskManager.Dispatcher.addJob(user, job)
    
    def createStopJob(self, user, **kwargs):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add("app", self.app)
        context.add("liveCd", self.liveCd)
        context.action = AppActions.STOP
        
        job = dissomniag.taskManager.Job(context, "Stop an App on a VM", user)
        job.addTask(dissomniag.tasks.operateOnApp())
        return dissomniag.taskManager.Dispatcher.addJob(user, job)
    
    def createCompileJob(self, user, **kwargs):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add("app", self.app)
        context.add("liveCd", self.liveCd)
        context.action = AppActions.COMPILE
        
        job = dissomniag.taskManager.Job(context, "Compile an App on a VM", user)
        job.addTask(dissomniag.tasks.operateOnApp())
        return dissomniag.taskManager.Dispatcher.addJob(user, job)
    
    def createResetJob(self, user, **kwargs):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add("app", self.app)
        context.add("liveCd", self.liveCd)
        context.action = AppActions.RESET
        
        job = dissomniag.taskManager.Job(context, "Reset an App on a VM", user)
        job.addTask(dissomniag.tasks.operateOnApp())
        return dissomniag.taskManager.Dispatcher.addJob(user, job)
    
    def createInterruptJob(self, user, **kwargs):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add("app", self.app)
        context.add("liveCd", self.liveCd)
        context.action = AppActions.INTERRUPT
        
        job = dissomniag.taskManager.Job(context, "Interrupt an App on a VM", user)
        job.addTask(dissomniag.tasks.operateOnApp())
        return dissomniag.taskManager.Dispatcher.addJob(user, job)
    
    def createRefreshGitJob(self, user, tagOrCommit = None, **kwargs):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add("app", self.app)
        context.add("liveCd", self.liveCd)
        context.tagOrCommit = tagOrCommit
        context.action = AppActions.REFRESH_GIT
        
        job = dissomniag.taskManager.Job(context, "Refresh Git on an App on a VM", user)
        job.addTask(dissomniag.tasks.operateOnApp())
        return dissomniag.taskManager.Dispatcher.addJob(user, job)
    
    def createRefreshAndResetJob(self, user, tagOrCommit = None, **kwargs):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add("app", self.app)
        context.add("liveCd", self.liveCd)
        context.tagOrCommit = tagOrCommit
        context.action = AppActions.REFRESH_AND_RESET
        
        job = dissomniag.taskManager.Job(context, "Refresh And Reset an App on a VM", user)
        job.addTask(dissomniag.tasks.operateOnApp())
        return dissomniag.taskManager.Dispatcher.addJob(user, job)
    
    def createCloneJob(self, user, **kwargs):
        self.authUser(user)
        context = dissomniag.taskManager.Context()
        context.add("app", self.app)
        context.add("liveCd", self.liveCd)
        context.action = AppActions.CLONE
        
        job = dissomniag.taskManager.Job(context, "Clone an App on a VM", user)
        job.addTask(dissomniag.tasks.operateOnApp())
        return dissomniag.taskManager.Dispatcher.addJob(user, job)
    
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
                if liveCd.vm.state == dissomniag.model.NodeState.CREATED:
                    job.addTask(dissomniag.tasks.addAppOnRemote())
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
    
    def operateOnSet(self, user, action, set = [], **kwargs):
        self.authUser(user)
        filteredSet = []
        for rel in set:
            if rel in self.AppLiveCdRelations:
                filteredSet.append(rel)
        return self._operateOnSet(user, action, filteredSet, **kwargs)
            
    
    def _operateOnSet(self, user, action, set = [], **kwargs):
        self.authUser(user)
        doneOne = False
        for rel in set:
            if action == AppActions.START:
                rel.createStartJob(user, **kwargs)
            elif action == AppActions.STOP:
                rel.createStopJob(user, **kwargs)
            elif action == AppActions.COMPILE:
                rel.createCompileJob(user, **kwargs)
            elif action == AppActions.RESET:
                rel.createResetJob(user, **kwargs)
            elif action == AppActions.INTERRUPT:
                rel.createInterruptJob(user, **kwargs)
            elif action == AppActions.REFRESH_GIT:
                rel.createRefreshGitJob(user, **kwargs)
            elif action == AppActions.REFRESH_AND_RESET:
                rel.createRefreshAndResetJob(user, **kwargs)
            elif action == AppActions.CLONE:
                rel.createCloneJob(user, **kwargs)
            else:
                continue
            doneOne = True
        return doneOne
    
    def operate(self, user, action, appRel = None, **kwargs):
        if isinstance(appRel, list):
            return self.operateOnSet(user, action, appRel, **kwargs)
        elif isinstance(appRel, dissomniag.model.AppLiveCdRelation) and appRel in self.AppLiveCdRelations:
            return self._operateOnSet(user, action, [appRel], **kwargs)
        elif appRel == None:
            return self._operateOnSet(user, action, self.AppLiveCdRelations, **kwargs)
        else:
            return False
    
    
    def addLiveCdRelation(self, user, liveCd):
        self.authUser(user)
        rel = AppLiveCdRelation.createRelation(user, self, liveCd)
             
    
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

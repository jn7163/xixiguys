#coding:utf-8
import re,logging,os
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext.db import Model as DBModel
import config

class DBUser(db.Model):
	gtalk = db.StringProperty()                    #gtalk
	nickname = db.StringProperty()                 #nickname
	recvOfflineMsg = db.BooleanProperty(default=False)
	isAdmin = db.BooleanProperty(default=False)
	time = db.DateTimeProperty(auto_now_add=True)
	recvOnlineMsg = db.BooleanProperty(default=True)

	def put(self): 
		super(DBUser,self).put() 

	def delete(self): 
		super(DBUser,self).delete()

class DBBlackUserList(db.Model):
	gtalk = db.StringProperty()
	
	def put(self): 
		super(DBBlackUserList,self).put() 

	def delete(self): 
		super(DBBlackUserList,self).delete()

class DBConfig(db.Model):
	name = db.StringProperty()
	value = db.TextProperty()

	def put(self): 
		super(DBConfig,self).put() 

	def delete(self): 
		super(DBConfig,self).delete()

def gblog_init():
	users = DBUser.all().filter('gtalk = ',config.ADMIN_GTALK).fetch(1000)
	if len(users) != 1:
		#for user in users:
		#	user.delete()
		user = DBUser(gtalk=config.ADMIN_GTALK,nickname=config.NICK_NAME,isAdmin=True)
		user.put()

gblog_init()

#coding:utf-8
import wsgiref.handlers
import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import images
from google.appengine.api import xmpp
#from datetime import datetime ,timedelta
import time,datetime
from models import *
import funcs
import config

class PublicPage(webapp.RequestHandler):
	def render(self, template_file, template_value):
		path = os.path.join(os.path.dirname(__file__), template_file)
		self.response.out.write(template.render(path, template_value))
	
	def error(self,code):
		if code==400:
			self.response.set_status(code)
		else:
			self.response.set_status(code)
			
	def is_admin(self):
		return users.is_current_user_admin()
	
	def head(self, *args):
		return self.get(*args) 


class tasksUpdate(PublicPage):
	def get(self):
		#funcs.checkUserOnline()
		#funcs.checkDarkRoomList(10)
		#funcs.checkBlockUserList(2,10)
		self.response.out.write('check all user ok')

class tasksCount(PublicPage):
	def get(self):
		funcs.updateUserCountToDB()
		funcs.updateCmdCountToDB()
		
class cleanUser(PublicPage):
	def get(self):
		num = funcs.cleanUserDo(config.ALLOW_NO_MSG_DAYS)
		self.response.out.write('clean %d user ok' % num)

def main():
	application = webapp.WSGIApplication(
									   [('/tasks/update', tasksUpdate),
									   ('/tasks/count', tasksCount),
									   ('/tasks/cleanuser', cleanUser)
									   ], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
	main()
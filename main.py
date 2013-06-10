#coding:utf-8
import wsgiref.handlers
import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import images
#from datetime import datetime ,timedelta
import time,datetime
from models import *
import funcs
from cmddo import *

class PublicPage(webapp.RequestHandler):
	def render(self, template_file, template_value):
		path = os.path.join(os.path.dirname(__file__), template_file)
		self.response.out.write(template.render(path, template_value))
	
	def error(self,error,reurl='/web/home'):
		self.render('html/error.html', {'error':error,'reurl':reurl})
			
	def is_admin(self):
		return users.is_current_user_admin()
	
	def head(self, *args):
		return self.get(*args) 

#self.redirect('/i/state')
#self.render('html/create.html', {'url':None,tinyurl':tinyUrl})
#self.response.out.write(tinyUrl.host + url.url)
#longurl = self.request.get("longurl")

class MyDebug(PublicPage):
	def get(self):
		self.response.out.write('test')
		#self.response.out.write(CmdTestDo('',''))
		#self.response.out.write(CmdUnfollowDo('/u admin'))
		return
class RunCmd(PublicPage):
	def get(self):
		self.response.out.write('runcmd')
		return
		
def main():
	application = webapp.WSGIApplication(
									   [
									   ('/admin/debug', MyDebug),
									   ('/admin/cmd', RunCmd)
									   ], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
	main()
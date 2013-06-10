############################################################################
#    Copyright (C) 2010 by math2gold                                       #
#    Twitter:@math2gold                                                    #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

from google.appengine.api import xmpp
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import logging

import cmddiv
#from twitter import *
import sys
import funcs
import xmpp_api

class XMPPHandler(webapp.RequestHandler):
	def post(self):
		message = None
		try:
			message=xmpp.Message(self.request.POST)
		except xmpp.InvalidMessageError, e:
			logging.error("Invalid XMPP request: %s", e[0])
			logging.error(self.request.body)
			logging.error(self.request.POST)
			return
		except:
			#from_name=m2ggg_core.get_mail_name(self.request.get('from')).lower()
			#m2ggg_core.activeresouce_record(from_name,4);
			from_name = self.request.get('from')
			logging.error(sys.exc_info()[0])
			raise "under attack:" +from_name.encode("UTF-8");
			return
		from_name = xmpp_api.get_mail_name(self.request.get('from')).lower()
		msgbody = funcs.MsgBlankClean(message.body)
		e = cmddiv.MsgCheckCmd(from_name,msgbody)
		if e == 'NOTCMD':
			if not funcs.isInGroupUser(from_name):
				message.reply('u r NOT in this group,pls join first,see more http://code.google.com/p/twpost/wiki/xixiguys_start')
				return
			if len(msgbody) > 1024:
				message.reply('error:msg too long(<=1024)')
				return
			e = funcs.broastcastMsg(msgbody,from_name,False)
			funcs.updateUserCount(from_name)
			#funcs.Add2OnlineList(from_name)
		else:
			message.reply(str(e))
			
class OnlineHandler(webapp.RequestHandler):
	def post(self):
		#sender = self.request.get('from').split('/')[0]
		sender = xmpp_api.get_mail_name(self.request.get('from')).lower()
		if funcs.isInGroupUser(sender):
			funcs.addUserToOnlineUserList(sender)
		#else:
			#logging.error('error sender %s incoming online' % sender)
			#msg_str = 'Please delete me from your contacts or join us,more info at http://is.gd/xixiguys_start'
			#xmpp_api.xmpp_sendmsg(sender,msg_str)

class OfflineHandler(webapp.RequestHandler):
	def post(self):
		#sender = self.request.get('from').split('/')[0]
		sender = xmpp_api.get_mail_name(self.request.get('from')).lower()
		if funcs.isInGroupUser(sender):
			funcs.delUserFromOnlineUserList(sender)
		else:
			logging.error('error sender %s incoming offline' % sender)

application = webapp.WSGIApplication([
                                       ('/_ah/xmpp/message/chat/', XMPPHandler),
                                       ('/_ah/xmpp/presence/available/', OnlineHandler),
                                       ('/_ah/xmpp/presence/unavailable/', OfflineHandler)
                                       ],
                                     debug=False)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

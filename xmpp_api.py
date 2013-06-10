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
from google.appengine.api import memcache

import logging
import string
import time
import xml.dom.minidom
import sys

class XmppStatusCache():
	Status=False
	def get_cached_xmpp_status(self,username):
		data = memcache.get(username)
		if data is not None:
			#DEBUG:logging.error(username+data)
			n=data.split(',')
			over=int(round(time.time()))-int(n[0])
			if over <60:
				self.Status=(n[1]=='True')
				return True
		return False

def set_cached_xmpp_status(username,s):
	w=str(int(round(time.time())))+','+str(s)
	#DEBUG:logging.error("W:"+username+":"+w)
	if not memcache.set(username,w,60):
		memcache.add(username,w,60)

def cached_xmpp_user_check(username):
	xc=XmppStatusCache()
	if (xc.get_cached_xmpp_status(username)):
		return xc.Status
	else:
		r=xmpp.get_presence(username)
		set_cached_xmpp_status(username,r)
		return r

def CheckAccountOnline(account):
	accstr = "onlineAccount:%s" % account
	data = memcache.get(accstr)
	if account == data:
		return True
	
	if xmpp.get_presence(account):
		memcache.set(accstr,account,20)
		#memcache.add("onlineAccount",account,90)
		return True
	else:
		return False

def isOnline(gtalk):
	ret = False
	try:
		ret = xmpp.get_presence(gtalk)
	except:
		pass

	return ret

def xmpp_sendmsg(account,msg):
	chat_sent=False

	#if CheckAccountOnline(account):
	status_code = xmpp.send_message(account,msg)
	chat_sent= (status_code == xmpp.NO_ERROR)
	
	return chat_sent

def get_mail_name(mailstr):
	try:
		return mailstr[:mailstr.find('/')]
	except:
		return ""

def send_invite(jid, from_jid=None):
	xmpp.send_invite(jid,from_jid)

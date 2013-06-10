#coding:utf-8
import wsgiref.handlers
import os,sys
import re
import urllib2,urllib
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.api import mail
from django.utils import simplejson
from models import *
import time,datetime
from cmddiv import *
import xmpp_api
import hashlib
import config

def getConfigValue(name):
	values = DBConfig.all().filter('name =',name).fetch(1)
	if len(values) != 1:
		return None
	data = simplejson.loads(values[0].value)
	return data
	
def setConfigValue(name,data):
	values = DBConfig.all().filter('name =',name).fetch(1)
	if len(values) != 1:
		value = DBConfig(name=name,value='')
	else:
		value = values[0]
	datastr = simplejson.dumps(data)
	value.value = datastr
	value.put()
	return True
	
def delConfigValue(name):
	values = DBConfig.all().filter('name =',name).fetch(1)
	for value in values:
		value.delete()
	
def getConfigValueWithCache(name):
	data = memcache.get(name)
	if data:
		return data
	else:
		data = getConfigValue(name)
		memcache.set(name,data,43200)
		return data
	
def setConfigValueWithCache(name,data):
	memcache.set(name,data,43200)
	setConfigValue(name,data)
	return True
	
def delConfigValueWithCache(name):
	delConfigValue(name)
	memcache.delete(name)
	return True

def isUTF8(text):
	isutf8 = True
	try:
		if isinstance(text, unicode):
			isutf8 = False
	except:
		pass
	return isutf8
	
def unicode2utf8(text):
	try:
		if isinstance(text, unicode):
			text = text.encode('utf-8')
	except:
		pass
	return text
	
def utf82unicode(text):
	try:
		if isinstance(text, unicode):
			pass
	except:
		text = text.decode('utf-8')
	return text

def isStringLike(str): 
	try: 
		str + '' 
	except:
		return 0 
	else: 
		return 1 

def MsgBlankClean(msg):
	#msg = msg.replace('　',' ')
	msg = msg.strip()	
	msg = msg.replace('\r','')
	msg = msg.replace('\n','')
	while msg.find('  ') != -1:
		msg = msg.replace('  ',' ')

	return msg

def InitUserListFromDb():
	users_data = {}
	users = DBUser.all().fetch(1000)
	for user in users:
		users_data[user.gtalk] = user
	return users_data

def getUserListFromCache():
	users_data = memcache.get('cache_all_user_list')
	if users_data is None:
		users_data = InitUserListFromDb()
		memcache.set('cache_all_user_list',users_data,43200)
	return users_data
	
def updateUserListFromCache(dbuser):
	users_data = getUserListFromCache()
	users_data[dbuser.gtalk] = dbuser
	memcache.set('cache_all_user_list',users_data,43200)
	return users_data

def addUserListFromCache(dbuser):
	updateUserListFromCache(dbuser)
	
def delUserListFromCache(dbuser):
	users_data = getUserListFromCache()
	try:
		users_data.pop(dbuser.gtalk)
	except:
		pass
	memcache.set('cache_all_user_list',users_data,43200)
	return users_data
	
def getUserByNameFromDb(gtalk):
	users = DBUser.all().filter('gtalk = ',gtalk).fetch(1)
	if len(users) == 1:
		return users[0]
	return None

def getUserByName(gtalk):
	users_data = getUserListFromCache()
	return users_data.get(gtalk,None)

def getUserByNicknameFromDb(nickname):
	users = DBUser.all().filter('nickname = ',nickname).fetch(1)
	if len(users) == 1:
		return users[0]
	return None

def getUserByNickname(nickname):
	users_data = getUserListFromCache()
	for user in users_data.values():
		if user.nickname == nickname:
			return user
	return None

def isInGroupUser(gtalk):
	users_dict = getUserListFromCache()
	user_data = users_dict.get(gtalk,None)
	if user_data is not None:
		return True
	else:
		return False

def isAdmin(gtalk):
	user = getUserByNameFromDb(gtalk)
	if user and user.isAdmin:
		return True
	return False

def getUserNo(gtalk):
	user = getUserByName(gtalk)
	if user is None:
		return 0
	users = DBUser.all().filter('time <= ',user.time).fetch(1000)
	return len(users)

##2010-11-14 12:26:18.250000
def getNatureTime(_time):
	_time += datetime.timedelta(hours=8)
	time_str = _time.__str__()
	time1 = time.strptime(time_str[0:19],'%Y-%m-%d %H:%M:%S')
	time2 = time.mktime(time1)
	time3 = time.localtime(time2)
	return time.strftime('%Y-%m-%d %H:%M:%S',time3)

def getNatureTime2(_time):
	_time += 8 * 60 *60
	time3 = time.localtime(_time)
	return time.strftime('%Y-%m-%d %H:%M:%S',time3)

#online user list
def InitOnlineUserListFromDb():
	users = DBUser.all().fetch(1000)
	users_list = []
	for user in users:
		if xmpp_api.isOnline(user.gtalk):
			users_list.append(user.gtalk)
	return users_list

def getOnlineUserListFromCache():
	users = getConfigValueWithCache('cache_online_user_list')
	if users is None:
		users = InitOnlineUserListFromDb()
		setConfigValueWithCache('cache_online_user_list',users)
	return users

def addUserToOnlineUserList(gtalk):
	users = getOnlineUserListFromCache()
	if gtalk not in users:
		users.append(gtalk)
		setConfigValueWithCache('cache_online_user_list',users)
	return users
	
def delUserFromOnlineUserList(gtalk):
	users = getOnlineUserListFromCache()
	if gtalk in users:
		users.remove(gtalk)
		setConfigValueWithCache('cache_online_user_list',users)
	return users

def InitOnlineMsgOnUserListFromDb():
	users = DBUser.all().fetch(1000)
	users_list = []
	for user in users:
		if user.recvOnlineMsg:
			users_list.append(user.gtalk)
	return users_list

def getOnlineMsgOnUserListFromCache():
	users = getConfigValueWithCache('cache_online_msgon_user_list')
	if users is None:
		users = InitOnlineMsgOnUserListFromDb()
		setConfigValueWithCache('cache_online_msgon_user_list',users)
	return users

def addUserToOnlineMsgOnUserList(gtalk):
	users = getOnlineMsgOnUserListFromCache()
	if gtalk not in users:
		users.append(gtalk)
		setConfigValueWithCache('cache_online_msgon_user_list',users)
	return users

def delUserFromOnlineMsgOnUserList(gtalk):
	users = getOnlineMsgOnUserListFromCache()
	if gtalk in users:
		users.remove(gtalk)
		setConfigValueWithCache('cache_online_msgon_user_list',users)
	return users

def InitOnlineMsgOffUserListFromDb():
	users = DBUser.all().fetch(1000)
	users_list = []
	for user in users:
		if not user.recvOnlineMsg:
			users_list.append(user.gtalk)
	return users_list

def getOnlineMsgOffUserListFromCache():
	users = getConfigValueWithCache('cache_online_msgoff_user_list')
	if users is None:
		users = []
		setConfigValueWithCache('cache_online_msgoff_user_list',users)
	return users

def addUserToOnlineMsgOffUserList(gtalk):
	users = getOnlineMsgOffUserListFromCache()
	if gtalk not in users:
		users.append(gtalk)
		setConfigValueWithCache('cache_online_msgoff_user_list',users)
	return users
	
def delUserFromOnlineMsgOffUserList(gtalk):
	users = getOnlineMsgOffUserListFromCache()
	if gtalk in users:
		users.remove(gtalk)
		setConfigValueWithCache('cache_online_msgoff_user_list',users)
	return users
	
def InitOfflineMsgOnUserListFromDb():
	users = DBUser.all().fetch(1000)
	users_list = []
	for user in users:
		if user.recvOfflineMsg:
			users_list.append(user.gtalk)
	return users_list

def getOfflineMsgOnUserListFromCache():
	users = getConfigValueWithCache('cache_offline_msgon_user_list')
	if users is None:
		users = InitOfflineMsgOnUserListFromDb()
		setConfigValueWithCache('cache_offline_msgon_user_list',users)
	return users

def addUserToOfflineMsgOnUserList(gtalk):
	users = getOfflineMsgOnUserListFromCache()
	if gtalk not in users:
		users.append(gtalk)
		setConfigValueWithCache('cache_offline_msgon_user_list',users)
	return users
	
def delUserFromOfflineMsgOnUserList(gtalk):
	users = getOfflineMsgOnUserListFromCache()
	if gtalk in users:
		users.remove(gtalk)
		setConfigValueWithCache('cache_offline_msgon_user_list',users)
	return users

def InitOfflineMsgOffUserListFromDb():
	users = DBUser.all().fetch(1000)
	users_list = []
	for user in users:
		if not user.recvOfflineMsg:
			users_list.append(user.gtalk)
	return users_list

def getOfflineMsgOffUserListFromCache():
	users = getConfigValueWithCache('cache_offline_msgoff_user_list')
	if users is None:
		users = InitOfflineMsgOffUserListFromDb()
		setConfigValueWithCache('cache_offline_msgoff_user_list',users)
	return users

def addUserToOfflineMsgOffUserList(gtalk):
	users = getOfflineMsgOffUserListFromCache()
	if gtalk not in users:
		users.append(gtalk)
		setConfigValueWithCache('cache_offline_msgoff_user_list',users)
	return users
	
def delUserFromOfflineMsgOffUserList(gtalk):
	users = getOfflineMsgOffUserListFromCache()
	if gtalk in users:
		users.remove(gtalk)
		setConfigValueWithCache('cache_offline_msgoff_user_list',users)
	return users

def getAdminUsers(isAdmin=False):	
	users = DBUser.all().filter('isAdmin =', True).fetch(1000)
	usersStr = u'total %d admin user,below\n' % (len(users))
	for user in users:
		if isAdmin:
			usersStr += '%s(%s),' % (user.nickname,user.gtalk)
		else:
			usersStr += user.nickname + '(*),'
	return usersStr.encode('utf-8')
	
def sendMsgToAdminUsers(msg):
	users = DBUser.all().filter('isAdmin =', True).fetch(1000)
	for user in users:
		xmpp_api.xmpp_sendmsg(user.gtalk,msg)

def getOnlineUser(num=0):
	users = getOnlineUserListFromCache()
	online = u'total %d user online,below\n' % (len(users))
	for gtalk in users:
		user = getUserByName(gtalk)
		if user is None:
			continue
		if user.isAdmin:
			online += user.nickname + u'(★),'
		else:
			online += user.nickname + u','
	return online.encode('utf-8')

def broastcastMsg(msg,from_gtalk,hint=True):
	msg = utf82unicode(msg)
	user = getUserByName(from_gtalk)
	if user is None:
		return
	if hint:
		msg_body = u'[administrator]: %s' % msg
	else:
		msg_body = u'%s: %s' % (user.nickname,msg)

	if isInDarkRoomUserList(from_gtalk):
		msg_body = u'[%s]: %s' % (user.nickname,msg)
		users_dict = getDarkRoomUserList()
		for gtalk in users_dict.keys():
			if from_gtalk == gtalk:
				continue
			xmpp_api.xmpp_sendmsg(gtalk,msg_body)
		return
		
	online_users = getOnlineUserListFromCache()
	online_msgon_users = getOnlineMsgOnUserListFromCache()
	for gtalk in online_msgon_users:
		if from_gtalk == gtalk:
			continue
		if gtalk in online_users:
			xmpp_api.xmpp_sendmsg(gtalk,msg_body)
	
	nowtime = time.time() + 8 * 3600
	tmptime = time.localtime(nowtime)
	time_str = ' (%s)' % time.strftime('%m.%d %H:%M',tmptime)

	if not hint:
		offline_msgon_users = getOfflineMsgOnUserListFromCache()
		for gtalk in offline_msgon_users:
			if from_gtalk == gtalk:
				continue
			if gtalk not in online_users:
				xmpp_api.xmpp_sendmsg(gtalk,msg_body + time_str)

def checkUserOnline():
	ret_msg = ''
	online_users = getOnlineUserListFromCache()
	all_users = getUserListFromCache()
	for user in all_users.values():
		if user.gtalk.find('@gmail.com') == -1:
			continue
		if xmpp_api.isOnline(user.gtalk):
			if user.gtalk not in online_users:
				addUserToOnlineUserList(user.gtalk)
				if not user.recvOnlineMsg:
					xmpp_api.xmpp_sendmsg(user.gtalk,'[NOTICE]:You CANT Receive Any Msg Since Your OnlineMsgFlag is Off.')
		else:
			if user.gtalk in online_users:
				delUserFromOnlineUserList(user.gtalk)

def addUserAdmin(gtalk,from_gtalk):
	user = getUserByNameFromDb(gtalk)
	if user is None:
		return '%s Not found' % gtalk
	if user.isAdmin:
		return '%s already admin' % gtalk
	else:
		user.isAdmin = True
		user.put()
		updateUserListFromCache(user)
		#ret_msg = u'set %s as administrator' % user.nickname
		#Broadcast(ret_msg)
		return 'add %s to admin success' % gtalk

def delUserAdmin(gtalk,from_gtalk):
	user = getUserByNameFromDb(gtalk)
	if user is None:
		return '%s Not found' % gtalk
	if user.isAdmin:
		user.isAdmin = False
		user.put()
		updateUserListFromCache(user)
		#ret_msg = u'cancel %s as administrator' % user.nickname
		#Broadcast(ret_msg)
		return 'del %s from admin success' % gtalk
	else:
		return '%s not admin yet' % gtalk

def addBlackList(gtalk):
	ret = False
	blacklist = getConfigValueWithCache('cache_black_list')
	if blacklist is None or len(blacklist) == 0:
		blacklist = [gtalk]
		ret = True
	else:
		if gtalk not in blacklist:
			blacklist.append(gtalk)
			ret = True
	if ret:
		setConfigValueWithCache('cache_black_list',blacklist)

def isInBalckList(gtalk):
	ret = False
	blacklist = getConfigValueWithCache('cache_black_list')
	if blacklist is None or len(blacklist) == 0:
		return False
	if gtalk in blacklist:
		return True
	return False

def delBlackList(gtalk):
	ret = False
	blacklist = getConfigValueWithCache('cache_black_list')
	if blacklist is None or len(blacklist) == 0:
		return ret
	else:
		if gtalk in blacklist:
			blacklist.remove(gtalk)
			setConfigValueWithCache('cache_black_list',blacklist)
			ret = True
	return ret

def getBlackList():
	return getConfigValueWithCache('cache_black_list')

def kickuser(gtalk,from_gtalk=None):
	user = getUserByNameFromDb(gtalk)
	if user:
		delUserFromOnlineUserList(user.gtalk)
		if user.recvOnlineMsg:
			delUserFromOnlineMsgOnUserList(user.gtalk)
		else:
			delUserFromOnlineMsgOffUserList(user.gtalk)
		if user.recvOfflineMsg:
			delUserFromOfflineMsgOnUserList(user.gtalk)
		else:
			delUserFromOfflineMsgOffUserList(user.gtalk)
		nickname = user.nickname
		delUserListFromCache(user)
		user.delete()
		addBlackList(gtalk)
		
		users_dict = getUserCountList()
		user_data = users_dict.get(gtalk,None)
		if user_data is not None:
			users_dict.pop(gtalk)
			updateUserCountToDB(users_dict)
		#ret_msg = u'kick %s from this group' % nickname
		#Broadcast(ret_msg)
		return True
	else:
		return False

def getDarkRoomUserList():
	users_dict = getConfigValueWithCache('cache_darkroom_user_list')
	if users_dict is None:
		users_dict = {}
	return users_dict
	
def addDarkRoomUserList(gtalk):
	users_dict = getDarkRoomUserList()
	users_dict[gtalk] = time.time()
	setConfigValueWithCache('cache_darkroom_user_list',users_dict)
	return True

	
def delDarkRoomUserList(gtalk):
	users_dict = getDarkRoomUserList()
	if gtalk in users_dict.keys():
		users_dict.pop(gtalk)
		setConfigValueWithCache('cache_darkroom_user_list',users_dict)
		return True
	return False
	
def isInDarkRoomUserList(gtalk):
	users_dict = getDarkRoomUserList()
	if gtalk in users_dict.keys():
		return True
	else:
		return False

def getBlockUserList():
	users_dict = getConfigValueWithCache('cache_block_user_list')
	return users_dict

def addBlockUserList(from_user,block_user):
	if from_user == block_user:
		if isInDarkRoomUserList(block_user):
			addDarkRoomUserList(block_user)
			return
		ret_msg = u'%s 自己钻到小黑屋了'

		db_user = getUserByName(block_user)
		if db_user.recvOfflineMsg:
			delUserFromOfflineMsgOnUserList(block_user)
		if db_user.recvOnlineMsg:
			delUserFromOnlineMsgOnUserList(block_user)
		broastcastMsg(ret_msg % db_user.nickname,block_user)
		xmpp_api.xmpp_sendmsg(block_user,ret_msg % db_user.nickname)
		addDarkRoomUserList(block_user)
		return
	users_dict = getBlockUserList()
	if	users_dict is None:
		users_dict = {}
	if users_dict.get(block_user,None) is None:
		users_dict[block_user] = {}
	users_dict[block_user][from_user] = time.time()
	setConfigValueWithCache('cache_block_user_list',users_dict)

def Broadcast(msg):
	msg = utf82unicode(msg)
	msg_body = u'[administrator]: %s' % msg
	users_dict = getUserListFromCache()
	for gtalk in users_dict.keys():
		xmpp_api.xmpp_sendmsg(gtalk,msg_body)
	return len(users_dict.keys())

def checkDarkRoomList(minute):
	ret_msg = u'%s 从小黑屋里刑满释放了'
	users_list = getDarkRoomUserList()
	time_now = time.time()
	for gtalk in users_list.keys():
		offset = time_now - users_list[gtalk]
		if offset > minute*60:
			delDarkRoomUserList(gtalk)
			db_user = getUserByName(gtalk)
			if db_user.recvOfflineMsg:
				addUserToOfflineMsgOnUserList(gtalk)
			if db_user.recvOnlineMsg:
				addUserToOnlineMsgOnUserList(gtalk)
			broastcastMsg(ret_msg % db_user.nickname,gtalk)
			xmpp_api.xmpp_sendmsg(gtalk,ret_msg % db_user.nickname)
			#return ret_msg % db_user.nickname
		elif offset > (minute*60-60) and offset < minute*60:
			xmpp_api.xmpp_sendmsg(gtalk,'[administrator]: you will be free 1 minute')

def checkBlockUserList(number,minute):
	time_now = time.time()
	ret_msg = u'%s 被大家抬到小黑屋了'
	block_users = getBlockUserList()
	for block_user in block_users.keys():
		from_users = block_users[block_user]
		for from_user in from_users.keys():
			if time_now - from_users[from_user] > minute*60:
				from_users.pop(from_user)
		if len(from_users.keys()) >= number:
			if isInDarkRoomUserList(block_user):
				#return 'blocked already'
				continue

			block_users.pop(block_user)
			setConfigValueWithCache('cache_block_user_list',block_users)
			db_user = getUserByName(block_user)
			if db_user.recvOfflineMsg:
				delUserFromOfflineMsgOnUserList(block_user)
			if db_user.recvOnlineMsg:
				delUserFromOnlineMsgOnUserList(block_user)
			broastcastMsg(ret_msg % db_user.nickname,block_user)
			xmpp_api.xmpp_sendmsg(block_user,ret_msg % db_user.nickname)
			addDarkRoomUserList(block_user)
			#return ret_msg % db_user.nickname

def getUserCountList():
	users = getConfigValueWithCache('cache_user_count_list')
	if users is None:
		users = {}
	return users
	
def updateUserCount(gtalk):
	users_dict = getUserCountList()
	user_data = users_dict.get(gtalk,None)
	if user_data is None:
		user_data = {'time':time.time(),'count':1}
	else:
		user_data['time'] = time.time()
		user_data['count'] += 1
	users_dict[gtalk] = user_data
	memcache.set('cache_user_count_list',users_dict,43200)

def updateUserCountToDB(users_dict=None):
	if users_dict is None:
		users_dict = getUserCountList()
	setConfigValueWithCache('cache_user_count_list',users_dict)
	
def getCmdCountList():
	cmds = getConfigValueWithCache('cache_cmd_count_list')
	if cmds is None:
		cmds = {}
	return cmds
	
def updateCmdCount(cmd):
	cmds_dict = getCmdCountList()
	cmd_data = cmds_dict.get(cmd,None)
	if cmd_data is None:
		cmd_data = 1
	else:
		cmd_data += 1
	cmds_dict[cmd] = cmd_data
	memcache.set('cache_cmd_count_list',cmds_dict,43200)

def updateCmdCountToDB(cmds_dict=None):
	if cmds_dict is None:
		cmds_dict = getCmdCountList()
	setConfigValueWithCache('cache_cmd_count_list',cmds_dict)

def getUserCountFromDb():
	users = DBUser.all().filter('recvOnlineMsg = ',True).fetch(1000)
	count1 = len(users)
	users = DBUser.all().filter('recvOnlineMsg = ',False).fetch(1000)
	count2 = len(users)
	users = DBUser.all().filter('recvOfflineMsg = ',True).fetch(1000)
	count3 = len(users)
	users = DBUser.all().filter('recvOfflineMsg = ',False).fetch(1000)
	count4 = len(users)
	return count1,count2,count3,count4

def testdo():
	return 'testdo'
	
def isHavePassword():
	passwd = getConfigValueWithCache('cache_group_password')
	if passwd is None:
		return False
	return True

def getPassword():
	return getConfigValueWithCache('cache_group_password')
	
def setPassword(passwd):
	setConfigValueWithCache('cache_group_password',passwd)
	if isHavePassword():
		return True
	else:
		return False
	
def checkPassword(passwd):
	passwd_str = getPassword()
	if passwd_str == passwd:
		return True
	else:
		return False
	
def delPassword():
	delConfigValueWithCache('cache_group_password')
	if not isHavePassword():
		return True
	else:
		return False
	
def addWhiteList(gtalk):
	ret = False
	whitelist = getConfigValueWithCache('cache_white_list')
	if whitelist is None or len(whitelist) == 0:
		whitelist = [gtalk]
		ret = True
	else:
		if gtalk not in whitelist:
			whitelist.append(gtalk)
			ret = True
	if ret:
		setConfigValueWithCache('cache_white_list',whitelist)
	return ret

def isInWhiteList(gtalk):
	ret = False
	whitelist = getConfigValueWithCache('cache_white_list')
	if whitelist is None or len(whitelist) == 0:
		return False
	if gtalk in whitelist:
		return True
	return False

def delWhiteList(gtalk):
	ret = False
	whitelist = getConfigValueWithCache('cache_white_list')
	if whitelist is None or len(whitelist) == 0:
		pass
	else:
		if gtalk in whitelist:
			whitelist.remove(gtalk)
			setConfigValueWithCache('cache_white_list',whitelist)
			ret = True
	return ret

def getWhiteList():
	return getConfigValueWithCache('cache_white_list')

def userJoin(gtalk,nickname):
	user = DBUser(gtalk=gtalk,nickname=nickname)
	user.put()
	addUserListFromCache(user)
	addUserToOnlineUserList(gtalk)
	addUserToOnlineMsgOnUserList(gtalk)
	addUserToOfflineMsgOffUserList(gtalk)
	delWhiteList(gtalk)
	
def userQuit(gtalk):
	user = getUserByNameFromDb(gtalk)
	if user:
		delUserFromOnlineUserList(user.gtalk)
		delUserFromOnlineMsgOnUserList(user.gtalk)
		delUserFromOnlineMsgOffUserList(user.gtalk)
		delUserFromOfflineMsgOnUserList(user.gtalk)
		delUserFromOfflineMsgOffUserList(user.gtalk)
		nickname = user.nickname
		delUserListFromCache(user)
		user.delete()

		users_dict = getUserCountList()
		user_data = users_dict.get(gtalk,None)
		if user_data is not None:
			users_dict.pop(gtalk)
			updateUserCountToDB(users_dict)
		addBlackList(gtalk)
		ret_msg = u'[administrator]: %s(%s) left group' % (nickname,gtalk)
		#Broadcast(ret_msg)
		sendMsgToAdminUsers(ret_msg)
		return True
	else:
		return False

def isInOnlinelist(gtalk):
	online_users = getOnlineUserListFromCache()
	if gtalk in online_users:
		return True
	else:
		return False

def cleanUserDo(days=90):
	time_dot = time.time() - days * 24 * 60 * 60
	time_dot_warning = time_dot + 10 * 24 * 60 * 60
	all_users_dict = getUserListFromCache()
	users_dict = getUserCountList()
	
	num = 0
	for gtalk in all_users_dict.keys():
		if gtalk in users_dict.keys():
			user_data = users_dict[gtalk]
			if user_data['time'] < time_dot:
				kickuser(gtalk)
				notice_msg = 'NOTICE:Its so long time since you last chat,you are kicked out of group %s' % config.GROUP_ACCOUNT
				xmpp_api.xmpp_sendmsg(gtalk,notice_msg)
				mail.send_mail(config.ADMIN_GTALK, gtalk, notice_msg, notice_msg)
				num += 1
			else:
				if user_data['time'] < time_dot_warning:
					notice_msg = 'WARNING:Its so long time since you last chat in group %s,you will be kicked out of this group in 10 days' % config.GROUP_ACCOUNT
					xmpp_api.xmpp_sendmsg(gtalk,notice_msg)
					mail.send_mail(config.ADMIN_GTALK, gtalk, notice_msg, notice_msg)
		else:
			user = all_users_dict[gtalk]
			join_time = user.time
			time_str = join_time.__str__()
			time1 = time.strptime(time_str[0:19],'%Y-%m-%d %H:%M:%S')
			time2 = time.mktime(time1)
			#return time2
			if time2 < time_dot:
				kickuser(gtalk)
				notice_msg = 'NOTICE:Its so long time and you never chat in group %s,you are kicked out of this group' % config.GROUP_ACCOUNT
				xmpp_api.xmpp_sendmsg(gtalk,notice_msg)
				mail.send_mail(config.ADMIN_GTALK, gtalk, notice_msg, notice_msg)
				num += 1
			else:
				if time2 < time_dot_warning:
					notice_msg ='WARNING:Its so long time and you never chat in group %s,you will be kicked out of this group in 10 days' % config.GROUP_ACCOUNT
					xmpp_api.xmpp_sendmsg(gtalk,notice_msg)
					mail.send_mail(config.ADMIN_GTALK, gtalk, notice_msg, notice_msg)
	return num

#http://api.longurl.org/v2/expand?format=json&url=http://t.co/lV8bVzK
def getLongUrl(shortUrl):
	long_url = shortUrl
	para = {'url' : shortUrl, 'format' : 'json'}
	url = "http://api.longurl.org/v2/expand?" + urllib.urlencode(para)
	try:
		response = urllib2.urlopen(urllib2.Request(url))
		json = response.read()
		dataDict = simplejson.loads(json)
		long_url = dataDict.get('long-url',shortUrl)
	#except Exception,e:
		#return str(e)
	except:
		return shortUrl
	return long_url

def CheckOnlineUser():
	time_dot = time.time() - 30 * 60
	users_dict = getUserCountList()

	for gtalk in users_dict.keys():
		user_data = users_dict[gtalk]
		if user_data['time'] < time_dot:
			delUserFromOnlineUserList(gtalk)

def Add2OnlineList(gtalk):
	online_users = getOnlineUserListFromCache()
	if gtalk not in online_users:
		addUserToOnlineUserList(gtalk)

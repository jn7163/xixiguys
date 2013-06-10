#coding:utf-8
#import wsgiref.handlers
#import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.api import mail
import time,datetime
#import logging
#import base64,random
from models import *
#from funcs import *
import funcs
import xmpp_api
import cmddiv

def GetCmdByNum(msg,num):
	cmdlist = msg.split()
	if len(cmdlist) <= num-1:
		return None
	return cmdlist[num-1]

def GetCmdNum(msg):
	cmdlist = msg.split()
	return len(cmdlist)

def CmdJoinDo(from_name,msg):
	if funcs.isInBalckList(from_name):
		return 'you are in black list,contact administrator'
	if funcs.isHavePassword() and not funcs.isInWhiteList(from_name):
		if GetCmdNum(msg) != 3:
			if not funcs.isInGroupUser(from_name):
				ret_str = '%s was trying to join group' % from_name
				funcs.sendMsgToAdminUsers(ret_str)
			return 'ERROR:this group need password!'
		passwd = GetCmdByNum(msg,3)
		if not funcs.checkPassword(passwd):
			if not funcs.isInGroupUser(from_name):
				ret_str = '%s was trying to join group' % from_name
				funcs.sendMsgToAdminUsers(ret_str)
			return 'ERROR:group password not correct!'

	if GetCmdNum(msg) < 2:
		return 'need nickname'
	nickname = GetCmdByNum(msg,2)
	user = funcs.getUserByNickname(nickname)

	if user:
		return 'nickname:%s is taken by somebody' % nickname
	user = funcs.getUserByName(from_name)
	if user:
		return 'you have been joined already'
	funcs.userJoin(from_name,nickname)
	ret_msg = u'welcome %s joined this group' % nickname
	funcs.Broadcast(ret_msg)
	return 'you join successfully'

def CmdQuitDo(from_name,msg):
	if funcs.userQuit(from_name):
		return 'you are left successfully and added to blacklist'
	else:
		return 'you are not joined before'

def CmdAdminDo(from_name,msg):
	isAdmin_flag = funcs.isAdmin(from_name)
	if GetCmdNum(msg) == 1:
		return funcs.getAdminUsers(isAdmin_flag)
	if not isAdmin_flag:
		return 'you are not administrator'
	if GetCmdNum(msg) != 3:
		return 'para error'
	cmd = GetCmdByNum(msg,2)
	gtalk = GetCmdByNum(msg,3)
	if cmd == 'add':
		return funcs.addUserAdmin(gtalk,from_name)
	if cmd == 'del':
		return funcs.delUserAdmin(gtalk,from_name)
	return 'para error'

def CmdKickDo(from_name,msg):
	if not funcs.isAdmin(from_name):
		return 'you are not administrator'
	if GetCmdNum(msg) == 1:
		blacklist = funcs.getBlackList()
		if blacklist is None or len(blacklist) == 0:
			return 'blacklist is null'
		else:
			retstr = ''
			for item in blacklist:
				retstr += item + ','
			return retstr

	if GetCmdNum(msg) != 3:
		return 'para error'
	cmd = GetCmdByNum(msg,2)
	para3 = GetCmdByNum(msg,3)
	if mail.is_email_valid(para3):
		gtalk = para3
	else:
		user = funcs.getUserByNickname(para3)
		gtalk = user.gtalk

	if cmd == 'add':
		ret = funcs.kickuser(gtalk,from_name)
		if ret:
			return 'kick %s success' % gtalk
		else:
			return 'kick %s fail' % gtalk
	if cmd == 'del':
		ret =  funcs.delBlackList(gtalk)
		if ret:
			return 'del %s from blacklist success' % gtalk
		else:
			return 'del %s from blacklist fail' % gtalk
	return 'para error'

def CmdNickDo(from_name,msg):
	if GetCmdNum(msg) < 2:
		return 'need nickname'
	ret_msg = None
	nickname = GetCmdByNum(msg,2)
	if len(nickname) > 20:
		ret_msg = u'nickname %s too long(<=20)' % nickname
		return ret_msg.encode('utf-8')
	user = funcs.getUserByNickname(nickname)
	if user:
		if user.gtalk == from_name:
			ret_msg = u'your nickname is %s already.' % nickname
		else:
			ret_msg = u'nickname:%s is taken by somebody' % nickname
		return ret_msg.encode('utf-8')
	user = funcs.getUserByNameFromDb(from_name)
	if user is None:
		return 'you are not joined'
	old_name = user.nickname
	user.nickname = nickname
	user.put()
	funcs.updateUserListFromCache(user)
	
	try:
		ret_msg = u'%s change nickname to %s' % (old_name,nickname)
		funcs.broastcastMsg(ret_msg,from_name)
	except:
		pass
	ret_msg = u'you have changed nickname:%s' % nickname
	return ret_msg.encode('utf-8')

def CmdOnlineDo(from_name,msg):
	num = 0
	if GetCmdNum(msg) > 1:
		cmd2 = GetCmdByNum(msg,2)
		if cmd2.isdigit():
			num = int(cmd2)
	return funcs.getOnlineUser(num)

def CmdAllUserDo(from_name,msg):
	#if not funcs.isAdmin(from_name):
	#	return 'you are not administrator'
	isAdmin = funcs.isAdmin(from_name)
	num = 1
	if GetCmdNum(msg) > 1:
		cmd2 = GetCmdByNum(msg,2)
		if cmd2.isdigit():
			num = int(cmd2)
	num = num -1
	allusers = DBUser.all().fetch(1000)
	users = DBUser.all().fetch(20,num*20)
	ret_msg = u'total %d user,below %d user\n' % (len(allusers),len(users))
	for user in users:
		if isAdmin:
			if user.isAdmin:
				ret_msg += u'*%s(%s),' % (user.nickname,user.gtalk)
			else:
				ret_msg += u'%s(%s),' % (user.nickname,user.gtalk)
		else:
			if user.isAdmin:
				ret_msg += u'*%s,' % (user.nickname)
			else:
				ret_msg += u'%s,' % (user.nickname)
	return ret_msg.encode('utf-8')

def CmdMsgFlagDo(from_name,msg):
	from_user = funcs.getUserByNameFromDb(from_name)
	if GetCmdNum(msg) == 1:
		if from_user.recvOnlineMsg:
			return 'your msg flag is on'
		else:
			return 'your msg flag is off'

	flag = GetCmdByNum(msg,2)
	if flag == 'on':
		ret_str = 'your msg flag is on already'
		if not from_user.recvOnlineMsg:
			from_user.recvOnlineMsg = True
			ret_str = 'your msg flag is changed to on ok'
		funcs.updateUserListFromCache(from_user)
		funcs.delUserFromOnlineMsgOffUserList(from_name)
		funcs.addUserToOnlineMsgOnUserList(from_name)
		return ret_str

	if flag == 'off':
		ret_str = 'your msg flag is off already'
		if from_user.recvOnlineMsg:
			from_user.recvOnlineMsg = False
			ret_str = 'your msg flag is changed to off ok'
		funcs.updateUserListFromCache(from_user)
		funcs.delUserFromOnlineMsgOnUserList(from_name)
		funcs.addUserToOnlineMsgOffUserList(from_name)
		return ret_str

def CmdPrivateMsgDo(from_name,msg):
	if GetCmdNum(msg) < 3:
		return 'need nickname and msg'
	nickname = GetCmdByNum(msg,2)
	user = funcs.getUserByNickname(nickname)
	if user is None:
		return 'nickname %s is unknowned' % nickname
	from_user = funcs.getUserByName(from_name)
	msg_pre = '@%s:' % from_user.nickname
	msgbody = msg_pre + msg[msg.find(nickname) + len(nickname)+1:].strip()
	
	xmpp_api.xmpp_sendmsg(user.gtalk,msgbody)
	ret_str = u'you send private msg to %s successfully' % nickname
	return ret_str.encode('utf-8')

def CmdOfflinemsgDo(from_name,msg):
	from_user = funcs.getUserByNameFromDb(from_name)
	if GetCmdNum(msg) == 1:
		if from_user.recvOfflineMsg:
			return 'your offlinemsg flag is on'
		else:
			return 'your offlinemsg flag is off'
	flag = GetCmdByNum(msg,2)
	if flag == 'on':
		ret_str = 'your offlinemsg flag is on already'
		if not from_user.recvOfflineMsg:
			from_user.recvOfflineMsg = True
			from_user.put()
			ret_str = 'your offlinemsg flag change to on'
		funcs.updateUserListFromCache(from_user)
		funcs.delUserFromOfflineMsgOffUserList(from_name)
		funcs.addUserToOfflineMsgOnUserList(from_name)
		return ret_str

	if flag == 'off':
		ret_str = 'your offlinemsg flag is off already'
		if from_user.recvOfflineMsg:
			from_user.recvOfflineMsg = False
			from_user.put()
			ret_str = 'your offlinemsg flag change to off'
		funcs.updateUserListFromCache(from_user)
		funcs.delUserFromOfflineMsgOnUserList(from_name)
		funcs.addUserToOfflineMsgOffUserList(from_name)
		return ret_str
	return 'offlinemsg need off or on'
	
def CmdFlushOnLineDo(from_name,msg):
	if not funcs.isAdmin(from_name):
		return 'you are not administrator'
	memcache.flush_all()	
	return 'flush online user list ok'

def CmdBroadcastDo(from_name,msg):
	if not funcs.isAdmin(from_name):
		return 'you are not administrator'
	cmd_str =  GetCmdByNum(msg,1)
	msgbody = msg[len(cmd_str)+1:].strip()
	num = funcs.Broadcast(msgbody)
	return 'Broadcast to %d users ok' % num

def CmdHelpDo(from_name,msg):
	ret_msg = 'more help at http://is.gd/xixiguys'
	return ret_msg
	
def CmdStateDo(from_name,msg):
	if not funcs.isAdmin(from_name):
		return 'you are not administrator'
	ret_msg = ''
	users = DBUser.all().fetch(1000)
	users_count_db = len(users)
	users = funcs.getUserListFromCache()
	users_count_cache = len(users)
	if users_count_cache == users_count_db:
		ret_msg += 'user db and cache count ok:%d\n' % users_count_db
	else:
		ret_msg += 'user db and cache count fail:%d/%d\n' % (users_count_db,users_count_cache)
	users = funcs.getOnlineMsgOnUserListFromCache()
	count0 = len(users)
	users = funcs.getOnlineMsgOffUserListFromCache()
	count1 = len(users)
	users = funcs.getOfflineMsgOnUserListFromCache()
	count2 = len(users)
	users = funcs.getOfflineMsgOffUserListFromCache()
	count3 = len(users)
	if users_count_db == count0+count1 == count2+count3:
		ret_msg += 'user onlinemsgon/onlinemsgoff/offlinemsgon/offlinemsgoff ok:%d/%d/%d/%d\n' % (count0,count1,count2,count3)
	else:
		ret_msg += 'user onlinemsgon/onlinemsgoff/offlinemsgon/offlinemsgoff fail:%d/%d/%d/%d\n' % (count0,count1,count2,count3)
		count0,count1,count2,count3 = funcs.getUserCountFromDb()
		ret_msg += 'DB   onlinemsgon/onlinemsgoff/offlinemsgon/offlinemsgoff fail:%d/%d/%d/%d\n' % (count0,count1,count2,count3)
	return ret_msg

def CmdInviteDo(from_name,msg):
	if GetCmdNum(msg) < 2:
		return 'error:need gtalk who be invited'
	invite_gmail = GetCmdByNum(msg,2)
	if not mail.is_email_valid(invite_gmail):
		return 'error:account not email'
	if funcs.isInBalckList(invite_gmail):
		funcs.delBlackList(invite_gmail)
	else:
		user = funcs.getUserByName(invite_gmail)
		if user:
			return '%s have been joined already' % invite_gmail
	xmpp_api.send_invite(invite_gmail)
	if not funcs.isInWhiteList(invite_gmail):
		funcs.addWhiteList(invite_gmail)
	return 'An invitation has been sent to %s ok,she/he can NOT chat until /join' % invite_gmail
	
def CmdInitUserFromDbDo(from_name,msg):
	if not funcs.isAdmin(from_name):
		return 'you are not administrator'
	users_data = {}
	all_users = DBUser.all().fetch(1000)
	
	users_online_list = []
	users_onlinemsgon_list = []
	users_onlinemsgoff_list = []
	users_offlinemsgon_list = []
	users_offlinemsgoff_list = []
	for user in all_users:
		users_data[user.gtalk] = user
		if xmpp_api.isOnline(user.gtalk):
			users_online_list.append(user.gtalk)

		if user.recvOnlineMsg:
			users_onlinemsgon_list.append(user.gtalk)
		else:
			users_onlinemsgoff_list.append(user.gtalk)
		if user.recvOfflineMsg:
			users_offlinemsgon_list.append(user.gtalk)
		else:
			users_offlinemsgoff_list.append(user.gtalk)

	memcache.flush_all()
	memcache.set('cache_all_user_list',users_data,43200)
	
	funcs.setConfigValueWithCache('cache_online_user_list',users_online_list)
	
	funcs.setConfigValueWithCache('cache_online_msgon_user_list',users_onlinemsgon_list)
	funcs.setConfigValueWithCache('cache_online_msgoff_user_list',users_onlinemsgoff_list)
	funcs.setConfigValueWithCache('cache_offline_msgon_user_list',users_offlinemsgon_list)
	funcs.setConfigValueWithCache('cache_offline_msgoff_user_list',users_offlinemsgoff_list)
	return 'init cache from db ok'
	
def CmdBlockDo(from_name,msg):
	if GetCmdNum(msg) != 2:
		return 'error:need user nickname'
	nickname = GetCmdByNum(msg,2)
	user = funcs.getUserByNickname(nickname)
	if user is None:
		ret_str = u'cant find user %s' % nickname
		return ret_str.encode('utf-8')
	if funcs.isInDarkRoomUserList(from_name) and from_name!=user.gtalk:
		return 'you are in DarkRoom,CANT block somebody'
	funcs.addBlockUserList(from_name,user.gtalk)
	funcs.checkBlockUserList(2,10)
	ret_str = u'block %s ok' % nickname
	return ret_str.encode('utf-8')
	
def CmdPasswordDo(from_name,msg):
	if GetCmdNum(msg) == 1:
		if funcs.isHavePassword():
			passwd = funcs.getPassword()
			ret_str =  u'password:%s' % passwd
			return ret_str.encode('utf-8')
		else:
			return 'no password'
	if not funcs.isAdmin(from_name):
		return 'you are not administrator'
	if GetCmdNum(msg) == 2:
		cmd = GetCmdByNum(msg,2)
		if cmd == 'del':
			funcs.delPassword()
			return 'delete password sucess'
		else:
			return 'cmd para error '
	if GetCmdNum(msg) == 3:
		cmd = GetCmdByNum(msg,2)
		passwd = GetCmdByNum(msg,3)
		if cmd=='set' and passwd:
			funcs.setPassword(passwd)
			ret_str =  u'set password:%s sucess' % passwd
			return ret_str.encode('utf-8')
		
	return 'cmd para error '

def CmdWhitelistDo(from_name,msg):
	if not funcs.isAdmin(from_name):
		return 'you are not administrator'
	if GetCmdNum(msg) == 1:
		whitelist = funcs.getWhiteList()
		if whitelist is None or len(whitelist) == 0:
			retstr = 'whitelist is null'
		else:
			retstr = ''
			for item in whitelist:
				retstr += item + ','
		return retstr
	if GetCmdNum(msg) != 3:
		return 'para error'
	cmd = GetCmdByNum(msg,2)
	gtalk = GetCmdByNum(msg,3)
	if not mail.is_email_valid(gtalk):
		return 'ERROR:gtalk is not email'

	if cmd == 'add':
		ret = funcs.addWhiteList(gtalk)
		if ret:
			return 'add %s to whitelist success' % gtalk
		else:
			return 'add %s to whitelist fail' % gtalk
	if cmd == 'del':
		ret = funcs.delWhiteList(gtalk)
		if ret:
			return 'delete %s from whitelist success' % gtalk
		else:
			return 'delete %s from whitelist fail' % gtalk
	return 'para error'

def CmdSetOnlineDo(from_name,msg):
	if GetCmdNum(msg) == 1:
		if funcs.isInOnlinelist(from_name):
			return 'you are in online list'
		else:
			return 'you are NOT in online list'
	flag = GetCmdByNum(msg,2)
	if flag == 'on':
		funcs.addUserToOnlineUserList(from_name)
		return 'you are in online list'
	if flag == 'off':
		funcs.delUserFromOnlineUserList(from_name)
		return 'you are NOT in online list now'

def CmdUserDo(from_name,msg):
	ret_str = u'init'
	if GetCmdNum(msg) != 2:
		return 'error:need user nickname or gtalk'
	nickname = GetCmdByNum(msg,2)
	if mail.is_email_valid(nickname):
		user = funcs.getUserByName(nickname)
		if user is None:
			user = funcs.getUserByNickname(nickname)
	else:
		user = funcs.getUserByNickname(nickname)
	if user is None:
		ret_str = u'CANT find user:%s' % nickname
		return ret_str.encode('utf-8')
	ret_str = u'%s' % user.nickname
	if funcs.isAdmin(from_name) or user.gtalk==from_name:
		ret_str += u'(%s)' % user.gtalk
	ret_str += u',在%s第%d个加入本群\n' % (funcs.getNatureTime(user.time),funcs.getUserNo(user.gtalk))
	
	if funcs.isAdmin(from_name) or user.gtalk==from_name:
		ret_str += u'设置:'
		if user.recvOfflineMsg:
			ret_str += u'离线时接收消息'
		else:
			ret_str += u'离线时不接收消息'
		if user.recvOnlineMsg:
			ret_str += u',在线时接收消息\n'
		else:
			ret_str += u',在线时不接收消息\n'
	users_dict = funcs.getUserCountList()
	if user.gtalk in users_dict.keys():
		user_data = users_dict[user.gtalk]
		ret_str += u'共发%d个消息,最后一次发消息在%s' % (user_data['count'],funcs.getNatureTime2(user_data['time']))

	return ret_str.encode('utf-8')

def CmdMeDo(from_name,msg):
	ret_msg = None
	user = funcs.getUserByName(from_name)
	if user is None:
		return 'you(%s) are not joined' % from_name

	return CmdUserDo(from_name,'/user %s' % from_name)

def CmdGroupInfoDo(from_name,msg):
	if not funcs.isAdmin(from_name):
		return 'you are not administrator'
	if GetCmdNum(msg) != 2:
		return 'error:need days'
	days = int(GetCmdByNum(msg,2))
	time_dot = time.time() - days * 24 * 60 * 60
	all_users_dict = funcs.getUserListFromCache()
	users_dict = funcs.getUserCountList()
	ret_str = u'user info:\n'
	
	for gtalk in all_users_dict.keys():
		if gtalk in users_dict.keys():
			user_data = users_dict[gtalk]
			if user_data['time'] < time_dot:
				ret_str += u'%s[%d],%s\n' % (gtalk,user_data['count'],funcs.getNatureTime2(user_data['time']))
		else:
			ret_str += u'%s[0]\n' % gtalk
	return ret_str.encode('utf-8')

def CmdOfflineMsgonDo(from_name,msg):
	if not funcs.isAdmin(from_name):
		return 'you are not administrator'
	users = funcs.getOfflineMsgOnUserListFromCache()
	ret_str = u'offline msg on user below:\n'
	for gtalk in users:
		user_data = funcs.getUserByName(gtalk)
		ret_str += u'%s(%s)\n' % (user_data.nickname,gtalk)
	return ret_str.encode('utf-8')

def CmdLongUrlDo(from_name,msg):
	if GetCmdNum(msg) != 2:
		return 'cmd short url'
	short_url = GetCmdByNum(msg,2)
	return funcs.getLongUrl(short_url)

def CmdCmdDo(from_name,msg):
	ret = cmddiv.MsgCheckCmd('',msg)
	return ret

def CmdTestDo(from_name,msg):
	ret = 'test'
	#if GetCmdNum(msg) == 2:
	#	funcs.testdo()
	#	return 'testdo'

	return ret 


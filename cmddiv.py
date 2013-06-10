#coding:utf-8
#import wsgiref.handlers
#import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import images
from google.appengine.ext import db
#from datetime import datetime ,timedelta
#from datetime import *
#import logging
#import base64,random
from models import *
import funcs
from cmddo import *
import config

def GetCmdByNum1(cmd,num):
	cmdlist = cmd.split()
	if len(cmdlist) <= num-1:
		return None
	return cmdlist[num-1]

def sortdict(dic):
	return sorted(dic.iteritems(), key=lambda d:d[1], reverse = True )

def CmdHelpDo(from_name,msg):
	global CmdTable
	global CmdTableDesc
	cmd_prefix = msg[0:1]
	cmdDict = funcs.getCmdCountList()
	if GetCmdNum(msg) == 2 or len(cmdDict.keys())<8:
		ret = u''
		for key in CmdTable.keys():
			ret += u'%s%s  %s\n' % (cmd_prefix,key.ljust(12),CmdTableDesc.get(key))
		ret += u'more help at http://is.gd/xixiguys \n'
		return ret.encode('utf-8')
	else:
		tmpcmdDict = sortdict(cmdDict)
		cmdDict = {}
		forcount = 1
		for item in tmpcmdDict:
			if forcount>8:
				break
			forcount += 1
			cmd = item[0]
			cmdDict[cmd] = item[1]
		#return str(cmdDict)

		ret = u'使用次数最多8个命令,查看所有命令使用/help all\n'
		#return str(cmdDict)
		for key in cmdDict.keys():
			ret += u'%s%s  %s\n' % (cmd_prefix,key.ljust(12),CmdTableDesc.get(key))
		ret += u'more command at http://is.gd/xixiguys \n'
		return ret.encode('utf-8')

CmdTable = {'join':CmdJoinDo,
			'quit':CmdQuitDo,
			'admin':CmdAdminDo,
			'online':CmdOnlineDo,
			'all':CmdAllUserDo,
			'onlinemsg':CmdMsgFlagDo,
			'nick':CmdNickDo,
			'kick':CmdKickDo,
			'd':CmdPrivateMsgDo,
			'p':CmdPrivateMsgDo,
			'pm':CmdPrivateMsgDo,
			'flushonline':CmdFlushOnLineDo,
			'state':CmdStateDo,
			'initcache':CmdInitUserFromDbDo,
			'invite':CmdInviteDo,
			'me':CmdMeDo,
			'broadcast':CmdBroadcastDo,
			'help':CmdHelpDo,
			#'cmd':CmdCmdDo,
			'offlinemsg':CmdOfflinemsgDo,
			#'block':CmdBlockDo,
			'password':CmdPasswordDo,
			'whitelist':CmdWhitelistDo,
			'user':CmdUserDo,
			'info':CmdGroupInfoDo,
			'offon':CmdOfflineMsgonDo,
			'long':CmdLongUrlDo,
			'test':CmdTestDo
}

CmdTableDesc = {'join':u'加入群',
			'quit':u'退出群',
			'admin':u'管理员操作',
			'online':u'查看在线成员',
			'all':u'浏览所有成员',
			'onlinemsg':u'设置在线是否接收消息',
			'nick':u'修改昵称',
			'kick':u'踢出群',
			'd':u'发送私信',
			'p':u'发送私信',
			'pm':u'发送私信',
			'flushonline':u'刷新缓存',
			'state':u'群运行状态',
			'initcache':u'同步缓存数据',
			'invite':u'邀请朋友加入群',
			'me':u'我的设置',
			'broadcast':u'发送广播消息',
			'help':u'帮助，命令列表',
			#'/cmd':CmdCmdDo,
			'offlinemsg':u'设置离线是否接收消息',
			#'block':u'Block成员',
			'password':u'操作群密码',
			'whitelist':u'操作白名单',
			'user':u'查看成员信息',
			'info':u'查看群信息',
			'offon':u'查看离线接收消息成员',
			'long':u'还原缩略网址',
			'test':u'测试'
}

def CmdProcess(from_name,msg):
	global CmdTable
	cmd = GetCmdByNum1(msg,1)
	CmdFunc = CmdTable.get(cmd[1:],None)
	if CmdFunc:
		funcs.updateCmdCount(cmd[1:])
		return CmdFunc(from_name,msg)
	else:
		return None
	
def MsgCheckCmd(from_name,msg):
	if msg[0:1] not in config.CMD_PREFIX:
		return 'NOTCMD'
	if msg[1:5] != "join" and msg[1:5] != "help" and not funcs.isInGroupUser(from_name):
		return 'u r NOT in this group,pls join first,see more http://is.gd/xixiguys_start'
	msg = msg.strip()
	cmdret =  CmdProcess(from_name,msg)

	if not cmdret:
		if msg[0:1] in config.CMD_PREFIX:
			return 'error command'
		else:
			return 'NOTCMD'
	else:
		return cmdret


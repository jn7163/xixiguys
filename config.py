#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 
#

# Change the APP_ID account below to your GAE Application Identifier.
# 机器人的地址，将下面参数改为你在GAE创建的应用ID，
APP_ID='xixiguys'

#上面GAE应用所属的google帐号，这个帐号默认是管理员
ADMIN_GTALK='example@gmail.com'
NICK_NAME='nickname'


#=========================以下参数可以不用修改========================
#命令前缀默认支持/ \ -三种前缀，可以自定义，前缀只能是一个字符
#警告：\是特殊字符，\\才表示一个\,不要修改成一个\ 
CMD_PREFIX=['/','\\','-']

#允许成员不发言的天数，接近这个值10天会提前发邮件提醒，如10天后再未发言则会被自动踢出群
ALLOW_NO_MSG_DAYS=365

#========================以下参数不能修改===========================
# Initing the bot account.Do not Change this expression
# 不要修改这个参数
GROUP_ACCOUNT = APP_ID+'@appspot.com'

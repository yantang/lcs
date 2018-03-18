#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     settings
   Description :
   Author :       tangyan
   date：          2018/1/24
-------------------------------------------------
   Change Activity:
                   2018/1/24:
-------------------------------------------------
"""
listen_client_port = 19300
server_host = ''

# client使用的命令号
CMD_SEND_PEER = 101    # 给另一个client发送消息
# server使用的命令号
CMD_NEW_MSG = 201    # 给client转发消息
CMD_ACK = 202    # 给client发送响应


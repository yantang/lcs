#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     client
   Description :
   Author :       tangyan
   date：          2018/1/7
-------------------------------------------------
   Change Activity:
                   2018/1/7:
-------------------------------------------------
"""
import sys
import socket
import select
import json
from time import sleep
import traceback
from settings import listen_client_port, server_host, CMD_SEND_PEER, CMD_ACK, CMD_NEW_MSG
from lcssocket import LcsSocket as LCK
from Message import Msg, parse_msg

sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sk.connect((server_host, listen_client_port))
except Exception as e:
    print 'exception: ', str(e)
    # sys.exit(1)
sk.setblocking(0)
lck = LCK(sk)

# 监听fd是否可写
watch_write_fd = set()
# 监听fd是否写读
watch_read_fd = set([lck.socket, sys.stdin])
# 监听fd是否异常
watch_exp_fd = set([lck.socket, sys.stdin])


def print_screen(msg):
    print '\n%s\n>>>' % msg,
    sys.stdout.flush()


def print_prompt():
    prompt_cmd = 'enter cmd: (格式：<命令号> <参数>...)\n' \
                 '1, send some client msg: [send cmd] [client fd] [your msg] ' \
                 '(e.g. %d 5 hello my friend.)' % CMD_SEND_PEER
    print_screen(prompt_cmd)


def handle_user_cmd(data):
    global lck
    
    try:
        cmd, argv = data.split(' ', 1)
        cmd = int(cmd)
    except Exception as e:
        print_screen('[ERROR] command format wrong: %s' % str(e))
        return
    if cmd == CMD_SEND_PEER:
        try:
            fd, msg = argv.split(' ', 1)
            fd = int(fd)
        except Exception as e:
            print_screen('[ERROR] command of sending client format wrong: %s' % str(e))
            return
        msg = dict(fd=fd, msg=msg)
        msg = Msg(cmd, json.dumps(msg))
        lck.put_send_data(msg.convert2bytes())
        if lck.socket not in watch_write_fd:
            watch_write_fd.add(lck.socket)
    else:
        print_screen('[ERROR] cmd[%d] not supported now.' % cmd)
    

def handle_server_msg(lck):
    msgs, lck.recv_buffer = parse_msg(lck.recv_buffer)
    for msg in msgs:
        if msg.cmd == CMD_ACK:
            print_screen("[reply from server: %s]: " % msg.data)
        if msg.cmd == CMD_NEW_MSG:
            try:
                data = json.loads(msg.data)
                print '[DEBUG] data:', data
            except Exception as e:
                print_screen('[ERROR] data recved unpack failed: %s' % str(e))
            else:
                fr = int(data['fd'])
                content = data['msg']
                print_screen("[msg from %d]: %s" % (fr, content))


def handle_sk_read(sk):
    global lck
    
    if sk is sys.stdin:
        handle_user_cmd(sys.stdin.readline())
    if sk is lck.socket:
        try:
            lck.recv_data()
            handle_server_msg(lck)
        except Exception as e:
            traceback.print_exc()
            print_screen('[ERROR] exception happens while reading server msg: %s' % str(e))
            sys.exit(1)


def handle_sk_write(sk):
    global lck
    
    try:
        lck.send_data()
    except Exception as e:
        traceback.print_exc()
        print_screen("[ERROR] exception happens while sending data: %s" % str(e))
        sys.exit(1)
    if lck.empty_send_buffer():
        watch_write_fd.remove(sk)
        
        
if __name__ == '__main__':
    print_prompt()
    while 1:
        rlist, wlist, xlist = select.select(watch_read_fd, watch_write_fd, watch_exp_fd)
        if xlist:
            print_screen('[ERROR] exception happens to socket: %s' % repr(xlist))
            sys.exit(1)
        for sk in rlist:
            handle_sk_read(sk)
        for sk in wlist:
            handle_sk_write(sk)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     server
   Description :
   Author :       tangyan
   date：          2018/1/7
-------------------------------------------------
   Change Activity:
                   2018/1/7:
-------------------------------------------------
"""
import socket
import select
import json
import sys
import traceback

from lcssocket import LcsSocket as LSK
from Message import Msg, parse_msg
from settings import server_host, listen_client_port, CMD_ACK, CMD_SEND_PEER, CMD_NEW_MSG

# socket.fileno() -> LSK 的映射关系
socket_map = {}

# 监听写事件
watch_write_sks = set()
# 监听读事件
watch_read_sks = set()
# 监听异常事件
watch_excp_sks = set()


def ret_socket_map():
    global socket_map
    return [sk for sk in socket_map.keys()]
    

def ret_multiplex_tuple(multiplex_tuple):
    return [_.fileno() for _ in multiplex_tuple]


def init_listen_port(port):
    """
    初始化监听端口
    """
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sk.bind((server_host, port))
        # 一般系统的最大值是5
        sk.listen(5)
    except Exception as e:
        print 'init listen socket failed. ', str(e)
        return False
    return LSK(sk)


def send_lsk_msg(lsk, msg):
    """
    给socket对应的peer发送消息
    
    只是放到写入缓冲区中，当socket可写的时候再真正发送
    """
    global watch_write_sks
    lsk.put_send_data(msg.convert2bytes())
    if lsk.socket not in watch_write_sks:
        watch_write_sks.add(lsk.socket)


def establish_client_connection(lsk):
    """
    建立同client的连接
    """
    global socket_map, watch_read_sks
    csk, addr = lsk.socket.accept()
    # socket要设置成非阻塞的
    csk.setblocking(0)
    lsk = LSK(csk)
    socket_map[lsk.socket.fileno()] = lsk
    # 监听读事件
    watch_read_sks.add(lsk.socket)
    # 监听异常事件
    watch_excp_sks.add(lsk.socket)
    # 连接建立好后，需要给client发送响应
    send_lsk_msg(lsk, Msg(CMD_ACK, 'connect success'))
    print '[INFO] establish client connection: ', lsk.socket.fileno(), addr


def clear_socket(lsk):
    """
    socket关闭及清理工作
    """
    sk = lsk.socket
    del socket_map[sk.fileno()]
    if sk in watch_read_sks:
        watch_read_sks.remove(sk)
    if sk in watch_write_sks:
        watch_write_sks.remove(sk)
    if sk in watch_excp_sks:
        watch_excp_sks.remove(sk)
    print 'socket close: ', sk.fileno()
    sk.close()
    return True


def lsk_read(lsk):
    """
    socket有数据可读
    """
    print '[INFO] lsk ready to read. ', lsk.socket.fileno()
    try:
        lsk.recv_data()
        msg_list, lsk.recv_buffer = parse_msg(lsk.recv_buffer)
        for msg in msg_list:
            print 'lsk recv msg: ', msg.cmd, msg.data
            handle_msg(lsk, msg)
    except Exception as e:
        traceback.print_exc()
        print 'lsk close: ', lsk.socket.fileno(), str(e)
        clear_socket(lsk)
        

def handle_msg(lsk, msg):
    """
    处理接收到的消息
    """
    global socket_map, watch_write_sks
    print 'sender[%d] handle msg[%d]' % (lsk.socket.fileno(), msg.cmd)

    if msg.cmd == CMD_SEND_PEER:
        data = json.loads(msg.data)
        fd, msg = int(data['fd']), data['msg']
        client_lsk = socket_map.get(fd, None)
        if not client_lsk:
            print 'target client socket closed. fd: %d' % fd
            return False
        print '[INFO] ready to send client msg: ', client_lsk.socket.fileno()
        # 给target client转发消息
        sending_msg = dict(fd=lsk.socket.fileno(), msg=msg)
        send_lsk_msg(client_lsk, Msg(CMD_NEW_MSG, json.dumps(sending_msg)))
        # 回应sender
        send_lsk_msg(lsk, Msg(CMD_ACK, 'msg send success'))


def lsk_write(lsk):
    """
    socket可以写数据了
    """
    print 'lsk[%d] ready to write.' % lsk.socket.fileno()
    try:
        lsk.send_data()
    except:
        print 'lsk closed while write. ', lsk.socket.fileno()
        clear_socket(lsk)
    # lsk没有待发送的数据了，取消监听
    if lsk.empty_send_buffer():
        watch_write_sks.remove(lsk.socket)


if __name__ == '__main__':
    listen_lsk = init_listen_port(listen_client_port)
    if not listen_lsk:
        sys.exit(1)
    socket_map[listen_lsk.socket.fileno()] = listen_lsk
    watch_read_sks.add(listen_lsk.socket)
    watch_excp_sks.add(listen_lsk.socket)
    
    while 1:
        print 'ready to recieve msg.'
        rlist, wlist, xlist = select.select(watch_read_sks, watch_write_sks, watch_excp_sks)
        print 'select ret:', ret_multiplex_tuple(rlist), ret_multiplex_tuple(wlist), ret_multiplex_tuple(xlist)
        for sk in rlist:
            lcs_sk = socket_map.get(sk.fileno(), None)
            if not lcs_sk:
                continue
            if lcs_sk is listen_lsk:
                # 监听socket可读, 处理新连接
                establish_client_connection(lcs_sk)
            else:
                lsk_read(lcs_sk)
        for sk in wlist:
            lcs_sk = socket_map.get(sk.fileno(), None)
            if not lcs_sk:
                continue
            lsk_write(lcs_sk)
        for sk in xlist:
            lcs_sk = socket_map.get(sk.fileno(), None)
            if not lcs_sk:
                continue
            if lcs_sk is listen_lsk:
                # 监听socket异常，server终止
                print 'client listenner exception.'
                sys.exit(1)
            clear_socket(lcs_sk)
        print 'socket map at loop end: ', ret_socket_map()

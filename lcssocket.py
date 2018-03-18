#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     lcs_socket
   Description :
   Author :       tangyan
   date：          2018/1/10
-------------------------------------------------
   Change Activity:
                   2018/1/10:
-------------------------------------------------
"""
import traceback


class LcsSocket(object):
    
    def __init__(self, sk):
        self.socket = sk
        # 接收缓冲区
        self.recv_buffer = ''
        # 发送缓冲区
        self.send_buffer = ''
        
    def recv_data(self):
        """
        接收到的数据放入buffer
        
        :return nlen
            接收到的数据长度
        :raise exp
            连接关闭
        """
        
        data = ''
        while 1:
            try:
                _d = self.socket.recv(4096)
            except Exception as e:
                # 非阻塞模式下，socket不可读时调用recv会抛异常
                # print traceback.print_exc()
                break
            if not _d:
                break
            data += _d
        nlen = len(data)
        print '[INFO] socket %d recv data: %d bytes' % (
            self.socket.fileno(), nlen)
        if data:
            self.recv_buffer += data
            return nlen
        else:
            raise Exception('[ERROR] socket[read data] closed.')
        
    def put_send_data(self, data):
        """
        准备发送的数据放入缓冲区
        """
        
        self.send_buffer += data

    def send_data(self):
        """
        监测到socket可写后，发送缓冲区中的数据
        """
        
        nbytes = self.socket.send(self.send_buffer)
        print '[INFO] lsk[%d] send data %d bytes' % (self.socket.fileno(), nbytes)
        if nbytes:
            self.send_buffer = self.send_buffer[nbytes:]
        else:
            raise Exception('[ERROR] socket[write data] closed.')

    def send_all_data(self):
        """
        发送所有缓冲区的数据（会阻塞，只用于客户端）
        """
        
        try:
            self.socket.sendall(self.send_buffer)
        except Exception as e:
            raise e

    def empty_send_buffer(self):
        """
        发送缓冲区是否为空
        """
        
        return not self.send_buffer

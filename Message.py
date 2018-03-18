#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     Message
   Description :
   Author :       tangyan
   date：          2018/1/9
-------------------------------------------------
   Change Activity:
                   2018/1/9:
-------------------------------------------------
"""
import struct

# 命令号长度
LEN_CMD = 1
# 表示数据段长度的字段
LEN_BODY_LEN = 4


class Msg(object):
    """
    二进制消息格式（网络序=big-endian）：
    unsigned char, unsigned long, char
    |-1 byte-|----4 byte----|--------n byte--------|
       cmd           len               data
    """
    
    def __init__(self, cmd, data):
        self.cmd = cmd
        self.len = len(data)
        self.data = data
    
    def convert2bytes(self):
        dl = len(self.data)
        fmt = '!BL%ds' % dl
        return struct.pack(fmt, self.cmd, self.len, self.data)
    
    
def parse_msg(data):
    """
    从data中解析出消息
    :param data
        字符串
    :return msg_list, left_data
        消息列表, 剩余字符串
    """
    msg_list = []
    len_header = LEN_CMD + LEN_BODY_LEN
    while 1:
        # 消息的最小长度
        if len(data) < len_header:
            break
        mlen, = struct.unpack('!L', data[LEN_CMD:len_header])
        if len(data) < mlen + len_header:
            # 消息未接受完整
            break
        fmt = '!BL%ds' % mlen
        cmd, mlen, body = struct.unpack(fmt, data[0:mlen+len_header])
        msg_list.append(Msg(cmd, body))
        data = data[mlen+len_header:]
    return msg_list, data
        
if __name__ == '__main__':
    cmd = 101
    data = '万人如海一身藏'
    msg = Msg(cmd, data)
    bytes = msg.convert2bytes()
    bytes += struct.pack('!BLs', 102, 44, 'a')
    print 'msg len:', len(bytes)
    msgs, data = parse_msg(bytes)
    for index, msg in enumerate(msgs):
        print 'the %d msg:' % index, msg.cmd, msg.len, msg.data
    print 'the left data len: ', len(data)

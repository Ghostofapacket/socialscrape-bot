# -*- coding: utf-8 -*-

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST = 'irc.netgamers.org' #irc server
PORT = 6665 #port
NICK = 'testbot1234'
USERNAME = 'testbot1234'
REALNAME = 'little pony'

print('soc created |', s)
remote_ip = socket.gethostbyname(HOST)
print('ip of irc server is:', remote_ip)


s.connect((HOST, PORT))

print('connected to: ', HOST, PORT)

nick_cr = ('NICK ' + NICK + '\r\n').encode()
s.send(nick_cr)
usernam_cr= ('USER megadeath megadeath megadeath :rainbow pie \r\n').encode()
s.send(usernam_cr)
s.send('JOIN #ibot \r\n'.encode()) #chanel

while 1:
    data = s.recv(4096).decode('utf-8')
    print(data)
    if data.find('PING') != -1:
        s.send(str('PONG ' + data.split(':')[1] + '\r\n').encode())
        print('PONG sent \n')
    if data.find('hi') != -1:
        s.send((str('PRIVMSG ' + data.split()[2]) + ' Hi! \r\n').encode())

s.close()
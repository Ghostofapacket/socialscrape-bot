# -*- coding: utf-8 -*-

import socket
import datetime
import threading
import re
import time
import pytz
import psutil
#import snscraperun

import settings


class IRC(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.channel_bot = settings.irc_channel_bot
        self.nick = settings.irc_nick
        self.server_name = settings.irc_server_name
        self.server_port = settings.irc_server_port
        self.server = None
        self.scrapesite = None
        self.messages_received = []
        self.messages_sent = []
        self.commands_received = []
        self.commands_sent = []

    def run(self):
        self.connect()

    def connect(self):
        if self.server:
            self.server.close()
        settings.logger.log('Connecting to IRC server ' + self.server_name)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((self.server_name, self.server_port))
        #self.server.send(str(('NICK', '{nick}'.format(nick=self.nick))).encode())
        self.send('USER', '{nick} {nick} {nick} :I am a bot; '
                           'https://github.com/Ghostofapacket/iBot/.'
                   .format(nick=self.nick, channel_main=self.channel_bot))
        time.sleep(5)
        self.send('NICK', '{nick}'.format(nick=self.nick))
        self.send('JOIN', '{channel_bot}'.format(
             channel_bot=self.channel_bot))
        self.send('PRIVMSG', 'Version {version}.'
                  .format(version=settings.version), self.channel_bot)

        self.start_pinger()
        self.listener()
        settings.logger.log('Connected to ' + self.server_name + ' as ' + self.nick)


    def start_pinger(self):
        self.pinger = threading.Thread(target=self.pinger)
        self.pinger.daemon = True
        self.pinger.start()

    def pinger(self):
        while True:
            time.sleep(600)
            self.send('PING', ':')

    def send(self, command, string, channel=''):
        if channel != '':
            channel += ' :'
        message = '{command} {channel}{string}'.format(**locals())
        try:
            settings.logger.log('IRC - {message}'.format(**locals()))
            self.messages_sent.append(message)
            self.server.send('{message}\n'.format(**locals()).encode('utf-8'))
        except Exception as exception:
            settings.logger.log('{exception}'.format(**locals()), 'WARNING')
            # self.connect()
            # self.server.send('{message}\n'.format(**locals()))

    def listener(self):
        while True:
            message = self.server.recv(2048)
            self.messages_received.append(message)
            for line in message.splitlines():
                settings.logger.log('IRC - {line}'.format(**locals()))
            if message.startswith('PING :'):
                message_new = re.search(r'^[^:]+:(.*)$', message).group(1)
                self.send('PONG', ':{message_new}'.format(**locals()))
            elif re.search(r'^:.+PRIVMSG[^:]+:!.*', message):
                command = re.search(r'^:.+PRIVMSG[^:]+:(!.*)', message) \
                    .group(1).strip().split(' ')
                command = [s.strip() for s in command if len(s.strip()) != 0]
                user = re.search(r'^:([^!]+)!', message).group(1)
                channel = re.search(r'^:[^#]+(#[^ :]+) ?:', message).group(1)
                self.commands_received.append({'command': command,
                                               'user': user,
                                               'channel': channel})
                self.command(command, user, channel)
    def check_admin(username):
        # change to db
        if str(username) == "Igloo":
            return True
        else:
            return False

    def command(self, command, user, channel):
        if command[0] == self.nick and command[1] == '!help'.format(**locals()):
            self.send('PRIVMSG', '{user}: For IRC commands can be found at -  '
                                 'https://github.com/ghostofapacket/ibot/blob/commands.md'
                      .format(**locals()), channel)
        elif command[0] == self.nick and command[1] == 'stop' and check_admin({user}.format(**locals())):
            settings.logger.log('EMERGENCY: {user} has requested I stop'.format(**locals()))
            settings.run_services.stop()
            self.send('PRIVMSG', '{user}: Stopped.'
                      .format(**locals()), channel)
            settings.running = False
        elif command[0] == self.nick and command[1] == 'update' and check_admin({user}.format(**locals())):
            open('STOP', 'w').close()
            settings.logger.log('WARNING: {user} has requested I update'.format(**locals()))
            self.server.close()
            settings.run_services.stop()
        elif command[0] == self.nick and command[1] == 'version':
            self.send('PRIVMSG', '{user}: Version is {version}.'
                      .format(user=user, version=settings.version), channel)
        elif command[0] == self.nick and command[1] == 'snsupdate' and check_admin({user}.format(**locals())):
            # Do the git pull and reload the module here
            settings.logger.log('WARNING: {user} has requested I update snscrape'.format(**locals()))
        elif command[0] == self.nick and command[1] == 'snscrape':
            # Get the site to scrape
            if not command[2]:
                self.send('PRIVMSG', '{user}: Missing site; try ' + self.nick + ' snscrape facebook,gab,instagram'\
                          + ',twitter,vkontake etc'.format(**locals()), channel)
            # try:
            #     #Check if module exists
            #     scrapesite = command[2]
            #     # if os.path.isfile('snscrape/' + command[2] +'.py'):
            #     #     #Pass to scraping process
            #     #     settings.scrape = snscraperrun.run()
            #     #     settings.snscraperun.daemon = True
            #     #     settings.snscraperun.start()

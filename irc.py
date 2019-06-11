# -*- coding: utf-8 -*-

import socket
import datetime
import threading
import re
import time
import pytz
import psutil
import hashlib
import subprocess
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
        self.send('USER', '{nick} {nick} {nick} :I am a bot; '
                           'https://github.com/Ghostofapacket/iBot/.'
                   .format(nick=self.nick))
        self.send('NICK', '{nick}'.format(nick=self.nick))
        self.send('JOIN', '{channel_bot}'.format(
             channel_bot=self.channel_bot))
        self.send('PRIVMSG', 'Version {version}.'
                  .format(version=settings.version), self.channel_bot)
        self.listener()

        self.start_pinger()
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
            message = self.server.recv(4096).decode('utf-8')
            self.messages_received.append(message)
            for line in message.splitlines():
                settings.logger.log('IRC - {line}'.format(**locals()))
            if message.startswith('PING :'):
                settings.logger.log('Received message ' + message)
                message_new = re.search(r'^[^:]+:(.*)$', message).group(1)
                self.send('PONG', ':{message_new}'.format(**locals()))
            elif re.search(r'^:.+PRIVMSG[^:]+:socialscr', message):
                    if re.search(r'^:.+PRIVMSG[^:]+:socialscr .*', message):
                        command = re.search(r'^:.+PRIVMSG[^:]+:socialscr (.*)', message) \
                             .group(1).strip().split(' ')
                        command = [s.strip() for s in command if len(s.strip()) != 0]
                        user = re.search(r'^:([^!]+)!', message).group(1)
                        channel = re.search(r'^:[^#]+(#[^ :]+) ?:', message).group(1)
                        self.commands_received.append({'command': command,
                                               'user': user,
                                               'channel': channel})
                        self.command(command, user, channel)
                        settings.logger.log('COMMAND - Received in channel {channel} - {command[0]}'.format(**locals()))

    def check_admin(self, user):
        # change to db
        if str(user) == "Igloo":
            return True
        else:
            return False

    def getjobid(self, user):
        sha_1 = hashlib.sha1()
        sha_1.update(user)
        jobid = sha_1.hexdigtest())
        return jobid

    def run_snscrape(self, user, module, args, target):
        getjobid(user + '-' + module + '-' + target)
        settings.logger.log('SNSCRAPE - Job ID {jobid}'.format(**locals()))
        settings.logger.log('SNSCRAPE - Trying to run snscrape with the following arguments - {module} - {target}' \
                            .format(**locals()))
        subprocess.run(["snscrape " + module + target + " >" + jobid])

    def command(self, command, user, channel):
        if command[0] == 'help':
            self.send('PRIVMSG', '{user}: For IRC commands can be found at -  '
                                 'https://github.com/ghostofapacket/ibot/blob/commands.md'
                      .format(**locals()), channel)
        elif command[0] == 'stop' and self.check_admin(user) == True:
            settings.logger.log('EMERGENCY: {user} has requested I stop'.format(**locals()))
            settings.run_services.stop()
            self.send('PRIVMSG', '{user}: Stopped.'
                      .format(**locals()), channel)
            settings.running = False
        elif command[0] == 'update' and self.check_admin(user) == True:
            open('STOP', 'w').close()
            settings.logger.log('WARNING: {user} has requested I update'.format(**locals()))
            self.server.close()
            settings.run_services.stop()
        elif command[0] == 'version':
            self.send('PRIVMSG', '{user}: Version is {version}.'
                      .format(user=user, version=settings.version), channel)
        elif command[0] == 'snsupdate' and self.check_admin(user) == True:
            # Do the git pull and reload the module here
            settings.logger.log('WARNING: {user} has requested I update snscrape'.format(**locals()))
            bot.send('PRIVMSG','Starting snscrape update')
            subprocess.run(["updatesnscrape.sh"])
            bot.send('PRIVMSG','snscrape update complete')
        elif command[0] == 'snscrape':
            # Get the site to scrape
            try:
                function = command[1]
            except IndexError:
                self.send('PRIVMSG', user + ': Missing site; try ' + self.nick + ' snscrape facebook,gab,instagram'\
                          + ',twitter,vkontake etc'.format(user=user), channel)
            if command[1] == 'twitter':
                #twit twoo
                module = command[1]
                target = command[2]
                try:
                    args = command[3]
                    self.run_snscrape(user, module, args, target)
                except IndexError:
                    self.run_snscrape(user, module, target)

            if command[1] == 'instagram':
                #sendnudez
            if command[1] == 'gab':
                #whatevenisgab?
            if command[1] == 'vkontakte':
                #imgonatakte
            if command[1] == 'facebook':
                #faceballs

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
import os
import datetime
from multiprocessing import Process, Queue, Pool
from shlex import quote

import settings
import abcalc


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
#        self.running_instagram = []
#        self.running_instagram = 0
#        self.processpool = Pool(processes=1)

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
#        self.send('PRIVMSG', 'Version {version}.'
#                  .format(version=settings.version), self.channel_bot)
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
            elif re.search(r'^:.+PRIVMSG[^:]+:socialbot', message):
                    if re.search(r'^:.+PRIVMSG[^:]+:socialbot .*', message):
                        command = re.search(r'^:.+PRIVMSG[^:]+:socialbot (.*)', message) \
                             .group(1).strip().split(' ')
                        command = [s.strip() for s in command if len(s.strip()) != 0]
                        user = re.search(r'^:([^!]+)!', message).group(1)
                        channel = re.search(r'^:[^#]+(#[^ :]+) ?:', message).group(1)
                        self.commands_received.append({'command': command,
                                               'user': user,
                                               'channel': channel})
                        self.command(command, user, channel)
                        settings.logger.log('COMMAND - Received in channel {channel} - {command[0]}'.format(**locals()))
                    elif re.search(r'^:.+PRIVMSG[^:]+:socialbot\: .*', message):
                        command = re.search(r'^:.+PRIVMSG[^:]+:socialbot\: (.*)', message) \
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
        time = str(datetime.datetime.now()) + '-' + user
        sha_1.update(time.encode('utf-8'))
        jobid = sha_1.hexdigest()
        return jobid

    def run_snscrape(self, channel, user, module, target, **kwargs):
        jobid = self.getjobid(user + '-' + module + '-' + target)
        settings.logger.log('SNSCRAPE - Job ID ' + jobid)
        self.send('PRIVMSG', '{user}: {jobid} has been queued.' .format(user=user, jobid=jobid), channel)
        settings.logger.log('SNSCRAPE - Trying to run snscrape with the following arguments - {module} - {target}' \
                            .format(**locals()))
        sanityregex = re.compile('([\"\'\@\#])')
        if str(module).startswith("twitter"):
            if str(module).startswith("twitter-user"):
                settings.logger.log('SNSCRAPE - Checking username capitalisation for user ' + sanityregex.sub(r'',target))
                try:
                    newtarget = subprocess.check_output("snscrape --max-results 1 twitter-user " + quote(sanityregex.sub(r'',target)) + " | grep -Po '^https?://twitter\.com/\K[^/]+'", shell=True).decode("utf-8")
                except subprocess.CalledProcessError as error:
                    newtarget = None
                if newtarget is None:
                    settings.logger.log("SNSCRAPE - Twitter user " + quote(sanityregex.sub(r'',target)) + " not found")
                    self.send('PRIVMSG', '{user}: Sorry, No results found for {jobid} - User does not exist' .format(user=user, jobid=jobid), channel)
                else:
                    settings.logger.log("SNSCRAPE - Running with updated settings - snscrape --format '{url} {tcooutlinksss} {outlinksss}'  " + quote(module) + " " + newtarget.strip() + " >jobs/twitter-@" + jobid)
                    subprocess.run("snscrape --format '{url} {tcooutlinksss} {outlinksss}'  " + quote(module) + " " + newtarget.strip() + " >jobs/twitter-@" + jobid, shell=True)
                    settings.logger.log('SNSCRAPE - Finished ' + jobid + ' - Uploading to https://transfer.notkiska.pw/' + module + "-" + sanityregex.sub(r'',target))
                    #Insert the profile as per JAA's request :-)
                    outfile = open("jobs/twitter-@" + jobid, "r")
                    profileline = "https://www.twitter.com/" + target + "\n"
                    lines = []
                    for line in outfile.read().split():
                        lines.append(line + "\n")
                    lines.insert(0,profileline)
                    outfile.close()
                    outfile=open("jobs/twitter-@" + jobid, "w")
                    outfile.writelines(lines)
                    outfile.close()
                    uploadedurl = subprocess.check_output("curl -s --upload-file jobs/twitter-@" + jobid + " https://transfer.notkiska.pw/twitter-@" + newtarget, shell=True).decode("utf-8")

            elif str(module).startswith("twitter-hash"):
                subprocess.run("snscrape --format '{url} {tcooutlinksss} {outlinksss}'  " + quote(module) + " " + quote(sanityregex.sub(r'',target)) + " >jobs/twitter-#" + jobid, shell=True)
                settings.logger.log('SNSCRAPE - Finished ' + jobid + ' - Uploading to https://transfer.notkiska.pw/' + module + '-' + sanityregex.sub(r'',target))
                settings.logger.log("CURL - Uploading with curl -s --upload-file jobs/twitter-#" + jobid + " https://transfer.notkiska.pw/twitter-#" + sanityregex.sub(r'',target))
                outfile = open("jobs/twitter-#" + jobid, "r")
                hashline1 = "https://www.twitter.com/hashtag/" + target + "\n"
                hashline2 = "https://www.twitter.com/hashtag/" + target + "?src=hash\n"
                hashline3 = "https://www.twitter.com/hashtag/" + target + "?f=tweets&vertical=default\n"
                hashline4 = "https://www.twitter.com/hashtag/" + target + "?f=tweets&vertical=default&src=hash\n"
                lines = []
                for line in outfile.read().split():
                    lines.append(line + "\n")
                lines.insert(0,hashline4)
                lines.insert(0,hashline3)
                lines.insert(0,hashline2)
                lines.insert(0,hashline1)
                outfile.close()
                outfile=open("jobs/twitter-#" + jobid, "w")
                outfile.writelines(lines)
                outfile.close()
                uploadedurl = subprocess.check_output("curl -s --upload-file jobs/twitter-#" + jobid + " https://transfer.notkiska.pw/twitter-%23" + quote(sanityregex.sub(r'',target)), shell=True).decode("utf-8")
                newtarget = sanityregex.sub(r'',target)

            elif str(module).startswith("twitter-search"):
                maxpages = kwargs.get('maxpages', None)
                if not maxpages is None:
                    subprocess.run("snscrape twitter-search --max-position " + maxpages + " " + quote(sanityregex.sub(r'',target)) + " >jobs/twitter-search-" + jobid, shell=True)
                    settings.logger.log('SNSCRAPE - Finished ' + jobid + ' - Uploading to https://transfer.notkiska.pw/' + module  + " " + sanityregex.sub(r'',target) + " maxpages set")
                    uploadedurl = subprocess.check_output("curl -s --upload-file jobs/twitter-search-" + jobid + " https://transfer.notkiska.pw/twitter-search-" + quote(sanityregex.sub(r'',target)), shell=True).decode("utf-8")
                    newtarget = sanityregex.sub(r'',target)
                if maxpages is None:
                    subprocess.run("snscrape twitter-search " + quote(sanityregex.sub(r'',target)) + " >jobs/twitter-search-" + jobid, shell=True)
                    settings.logger.log('SNSCRAPE - Finished ' + jobid + ' - Uploading to https://transfer.notkiska.pw/' + module + "-" + sanityregex.sub(r'',target))
                    uploadedurl = subprocess.check_output("curl -s --upload-file jobs/twitter-search-" + jobid + " https://transfer.notkiska.pw/twitter-search-" + quote(sanityregex.sub(r'',target)), shell=True).decode("utf-8")
                    newtarget = sanityregex.sub(r'',target)
            else:
                    settings.logger.log('SNSCRAPE - Command not found')
                    bot.send('PRIVMSG', 'Sorry {user} command not found'.format(user=user), channel)

            if not newtarget is None:
                if uploadedurl.startswith("400"):
                    self.send('PRIVMSG', '{user}: Sorry, No results returned for {jobid}'.format(user=user,jobid=jobid),channel)
                elif uploadedurl.startswith("Could not upload empty file"):
                    self.send('PRIVMSG', '{user}: Sorry, No results returned for {jobid}'.format(user=user,jobid=jobid),channel)
                else:
                    uploadedurl = uploadedurl.replace('%40','@')
                    self.send('PRIVMSG', '!ao < {uploadedurl} --explain "For {user} - socialscrape job {jobid}" --concurrency 6 --delay 0' \
                          .format(user=user, uploadedurl=uploadedurl, jobid=jobid), channel)

        if str(module).startswith("instagram"):
            while os.path.isfile('Instagram_run'):
                settings.logger.log('SNSCRAPE - instagram scrape already in progress, sleeping for 5 seconds')
                time.sleep(5)
            open('Instagram_run', 'w').close()
            if str(module).startswith("instagram-user"):
                settings.logger.log("snscrape --format '{dirtyUrl}'  " + module + " " + sanityregex.sub(r'',target) + " >jobs/instagram-@" + jobid)
                subprocess.run("snscrape --format '{dirtyUrl}'  " + quote(module) + " " + quote(sanityregex.sub(r'',target)) + " >jobs/instagram-@" + jobid, shell=True)
                if not os.stat("jobs/instagram-@" + jobid).st_size == 0:
                    settings.logger.log('SNSCRAPE - Finished ' + jobid + ' - Uploading to https://transfer.notkiska.pw/' + module + "-@" + sanityregex.sub(r'',target))
                    #Insert the profile as per JAA's request :-)
                    outfile = open("jobs/instagram-@" + jobid, "r")
                    profileline = "https://www.instagram.com/" + target + "\n"
                    lines = outfile.readlines()
                    lines.insert(0,profileline)
                    outfile.close()
                    outfile=open("jobs/instagram-@" + jobid, "w")
                    outfile.writelines(lines)
                    outfile.close()
                    uploadedurl = subprocess.check_output("curl -s --upload-file jobs/instagram-@" + jobid + " https://transfer.notkiska.pw/instagram-@" + quote(sanityregex.sub(r'',target)), shell=True).decode("utf-8")
                    archivebotid = abcalc.jobid(uploadedurl)
                    jobfile = "jobs/instagram-@" + jobid
                else:
                    self.send('PRIVMSG', '{user}: Sorry, No results returned for {jobid} - User does not exist'.format(user=user,jobid=jobid),channel)
                    jobfile = "jobs/instagram-@" + jobid

            elif str(module).startswith("instagram-hashtag"):
                subprocess.run("snscrape --format '{dirtyUrl}'  " + quote(module) + " " + quote(sanityregex.sub(r'',target)) + " >jobs/instagram-#" + jobid, shell=True)
                if not os.stat("jobs/instagram-#" + jobid).st_size == 0:
                    settings.logger.log('SNSCRAPE - Finished ' + jobid + ' - Uploading to https://transfer.notkiska.pw/' + module + "-" + sanityregex.sub(r'',target))
                    uploadedurl = subprocess.check_output("curl -s --upload-file jobs/instagram-#" + jobid + " https://transfer.notkiska.pw/instagram-%23" + quote(sanityregex.sub(r'',target)), shell=True).decode("utf-8")
                    archivebotid = abcalc.jobid(uploadedurl)
                    uploadedurl = uploadedurl.replace('%40','@')
                    jobfile = "jobs/instagram-#" + jobid
                else:
                    self.send('PRIVMSG', '{user}: Sorry, No results returned for {jobid} - Hashtag does not exist'.format(user=user,jobid=jobid),channel)
                    jobfile = "jobs/instagram-#" + jobid
            else:
                    settings.logger.log('SNSCRAPE - Command not found')
                    bot.send('PRIVMSG', 'Sorry {user} command not found'.format(user=user), channel)

            if not os.stat(jobfile).st_size == 0:
                #Should be standard for all jobs
                if uploadedurl.startswith("400"):
                    self.send('PRIVMSG', '{user}: Sorry, No results returned for {jobid}'.format(user=user,jobid=jobid),channel)
                elif uploadedurl.startswith("Could not upload empty file"):
                    self.send('PRIVMSG', '{user}: Sorry, No results returned for {jobid}'.format(user=user,jobid=jobid),channel)
                else:
                    uploadedurl = uploadedurl.replace('%40','@')
                    self.send('PRIVMSG', '!a < {uploadedurl} --explain "For {user} - socialscrape job {jobid}"' \
                          .format(user=user, uploadedurl=uploadedurl, jobid=jobid), channel)
                    time.sleep(5)
                    ignoreregex = "^https?://www\.instagram\.com/.*[?&]hl="
                    self.send('PRIVMSG', '!ignore {jobid} {ignoreregex}' \
                         .format(jobid=archivebotid,ignoreregex=ignoreregex),channel)
                os.remove('Instagram_run')

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
            self.send('PRIVMSG','Starting snscrape update')
            subprocess.run(["updatesnscrape.sh"])
            self.send('PRIVMSG','snscrape update complete')
        elif command[0] == 'snscrape':
            # Get the site to scrape
            try:
                function = command[1]
                queue = Queue()
                if function.startswith('twitter-'):
                    module = command[1]
                    target = command[2]
                    try:
                        args = command[3]
                        print(args)
                        if str(args) != "maxpages":
                            self.send('PRIVMSG', user + ': Sorry, Command not recognised. Did you mean "maxpages" ?'.format(user=user), channel)
                        else:
                            keywords = {'maxpages': command[4]}
                            runsnscrape = Process(target=self.run_snscrape, args=(channel, user, module, target), kwargs=keywords)
                            runsnscrape.start()
                    except IndexError:
                        runsnscrape = Process(target=self.run_snscrape, args=(channel, user, module, target))
                        runsnscrape.start()

                if function.startswith('instagram-'):
                    # sendnudez
                    module = command[1]
                    target = command[2]
                    try:
                        args = command[3]
                        runsnscrape = Process(target=self.run_snscrape, args=(channel, user, module, target))
                        runsnscrape.start()
#                        runsnscrape = self.processpool.apply_async(self.run_snscrape, args=(channel, user, module, target))
#                        self.running_instagram.append(runsnscrape)
                    except IndexError:
                        runsnscrape = Process(target=self.run_snscrape, args=(channel, user, module, target))
                        runsnscrape.start()
#                        runsnscrape = self.processpool.apply_async(self.run_snscrape, args=(channel, user, module, target))
#                        self.running_instagram.append(runsnscrape)
                if function == 'gab':
                    # whatevenisgab?
                    settings.logger.log('gab')
                if function == 'vkontakte':
                    # imgonatakte
                    settings.logger.log('vkon')
                if function == 'facebook':
                    # faceballs
                    settings.logger.log('faceballs')
            except IndexError:
                self.send('PRIVMSG', user + ': Missing site; try ' + self.nick + ' snscrape instagram-user,instagram-hashtag'\
                          + ',twitter-user,twitter-hashtag,twitter-search'.format(user=user), channel)

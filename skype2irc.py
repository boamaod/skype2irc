#! /usr/bin/env python
# -*- coding: utf-8 -*-

# IRC ⟷  Skype Gateway Bot: Connects Skype Chats to IRC Channels
# Copyright (C) 2014  Märt Põder <tramm@p6drad-teel.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# *** This bot deliberately prefers IRC to Skype! ***

# Snippets from
#
#  Feebas Skype Bot (C) duxlol 2011 http://sourceforge.net/projects/feebas/
#  IRC on a Higher Level http://www.devshed.com/c/a/Python/IRC-on-a-Higher-Level/
#  Time until a date http://stackoverflow.com/questions/1580227/find-time-until-a-date-in-python
#  Skype message edit code from Kiantis fork https://github.com/Kiantis/skype2irc

import sys, signal
import time, datetime
import string, textwrap

from ircbot import SingleServerIRCBot
from irclib import ServerNotConnectedError
from threading import Timer

version = "0.3"

servers = [
("irc.freenode.net", 6667),
("hitchcock.freenode.net", 6667),
("leguin.freenode.net", 6667),
("verne.freenode.net", 6667),
("roddenberry.freenode.net", 6667),
]

nick = "skype-}"
botname = "IRC ⟷  Skype".decode('UTF-8')
password = None

mirrors = {
'#test':
'iWwCuTwsjoIglPL3Fbmc_BM95EyK3683btIvrV_B2lQN4agJGCX7-REKzMl7-ruRqvo2RIgcOkQ',
}

max_irc_msg_len = 442
ping_interval = 2*60
reconnect_interval = 30

# to avoid flood excess
max_seq_msgs = 2
delay_btw_msgs = 0.35
delay_btw_seqs = 0.15

preferred_encodings = ["UTF-8", "CP1252", "ISO-8859-1"]

name_start = "<".decode('UTF-8') # "◀"
name_end = ">".decode('UTF-8') # "▶"
emote_char = "*".decode('UTF-8') # "✱"

muted_list_filename = nick + '.%s.muted'

topics = ""

usemap = {}
bot = None
mutedl = {}
lastsaid = {}
edmsgs = {}

pinger = None
bot = None

wrapper = textwrap.TextWrapper(width=max_irc_msg_len - 2)
wrapper.break_on_hyphens = False

# Time consts
SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
MONTH = 30 * DAY

def get_relative_time(dt, display_full = True):
    """Returns relative time compared to now from timestamp"""
    now = datetime.datetime.now()
    delta_time = now - dt

    delta =  delta_time.days * DAY + delta_time.seconds 
    minutes = delta / MINUTE
    hours = delta / HOUR
    days = delta / DAY

    if delta <= 0:
        return "in the future" if display_full else "!"
    if delta < 1 * MINUTE: 
      if delta == 1:
          return "moment ago" if display_full else "1s"
      else:
          return str(delta) + (" seconds ago" if display_full else "s")
    if delta < 2 * MINUTE:    
        return "a minute ago" if display_full else "1m"
    if delta < 45 * MINUTE:    
        return str(minutes) + (" minutes ago" if display_full else "m")
    if delta < 90 * MINUTE:
        return "an hour ago" if display_full else "1h"
    if delta < 24 * HOUR:
        return str(hours) + (" hours ago" if display_full else "h")
    if delta < 48 * HOUR:
        return "yesterday" if display_full else "1d"
    if delta < 30 * DAY:    
        return str(days) + (" days ago" if display_full else "d")
    if delta < 12 * MONTH:
        months = delta / MONTH
        if months <= 1:
            return "one month ago" if display_full else "1m"
        else:
            return str(months) + (" months ago" if display_full else "m")
    else:
      years = days / 365.0
      if  years <= 1:
          return "one year ago" if display_full else "1y"
      else:
          return str(years) + (" years ago" if display_full else "y")

def cut_title(title):
    """Cuts Skype chat title to be ok"""
    newtitle = ""
    for chunk in title.split():
        newtitle += chunk.strip(string.punctuation) + " "
        if len(newtitle) > 10:
            break
    return newtitle.strip()

def get_nick_decorated(nick):
    """Decorate nicks for better visibility in IRC (currently bold)"""
    return "\x02" + nick + "\x02"

def load_mutes():
    """Loads people who don't want to be broadcasted from IRC to Skype"""
    for channel in mirrors.keys():
        mutedl[channel] = []
        try:
            f = open(muted_list_filename % channel, 'r')
            for line in f.readlines():
                name = line.rstrip("\n")
                mutedl[channel].append(name)
                mutedl[channel].sort()
            f.close()
            print 'Loaded list of ' + str(len(mutedl[channel])) + ' mutes for ' + channel + '!'
        except:
            pass

def save_mutes(channel):
    """Saves people who don't want to be broadcasted from IRC to Skype"""
    try:
        f = open(muted_list_filename % channel, 'w')
        for name in mutedl[channel]:
            f.write(name + '\n')
        mutedl[channel].sort()
        f.close
        print 'Saved ' + str(len(mutedl[channel])) + ' mutes for ' + channel + '!'
    except:
        pass

def OnMessageStatus(Message, Status):
    """Skype message object listener"""
    raw = Message.Body
    msgtype = Message.Type
    chat = Message.Chat
    send = chat.SendMessage
    senderDisplay = Message.FromDisplayName
    senderHandle = Message.FromHandle

    # Only react to defined chats
    if chat in usemap:
        if Status == 'RECEIVED':
            if msgtype == 'EMOTED':
                bot.say(usemap[chat], emote_char + " " + get_nick_decorated(senderHandle) + " " + raw)
            elif msgtype == 'SAID':
                bot.say(usemap[chat], name_start + get_nick_decorated(senderHandle) + name_end + " " + raw)

def OnNotify(n):
    """Skype notification listener"""
    params = n.split()
    if len(params) >= 4 and params[0] == "CHATMESSAGE":
        if params[2] == "EDITED_TIMESTAMP":
            edmsgs[params[1]] = True
        elif params[1] in edmsgs and params[2] == "BODY":
            msg = skype.Message(params[1])
            if msg:
                chat = msg.Chat
                if chat in usemap:
                    bot.say(usemap[chat], name_start + get_nick_decorated(msg.FromHandle) + " ✎".decode('UTF-8') + get_relative_time(msg.Datetime, display_full = False) + name_end + " " + msg.Body)
            del edmsgs[params[1]]

def decode_irc(raw, preferred_encs = preferred_encodings):
    """Heuristic IRC charset decoder"""
    changed = False
    for enc in preferred_encs:
        try:
            res = raw.decode(enc)
            changed = True
            break
        except:
            pass
    if not changed:
        try:
            import chardet
            enc = chardet.detect(raw)['encoding']
            res = raw.decode(enc)
        except:
            res = raw.decode(enc, 'ignore')
            #enc += "+IGNORE"
    return res

def signal_handler(signal, frame):
    print "Ctrl+C pressed!"
    if pinger is not None:
        print "Cancelling the pinger..."
        pinger.cancel()
    if bot is not None:
        print "Killing the bot..."
        for dh in bot.ircobj.handlers["disconnect"]:
            bot.ircobj.remove_global_handler("disconnect", dh[1])
        if len(bot.ircobj.handlers["disconnect"]) == 0:
            print "Finished."
            bot.die()

class MirrorBot(SingleServerIRCBot):
    """Create IRC bot class"""

    def __init__(self):
        SingleServerIRCBot.__init__(self, servers, nick, (botname + " " + topics).encode("UTF-8"), reconnect_interval)

    def start(self):
        """Override default start function to avoid starting/stalling the bot with no connection"""
        while not self.connection.is_connected():
            self._connect()
            if not self.connection.is_connected():
                time.sleep(self.reconnection_interval)
                self.server_list.append(self.server_list.pop(0))
        SingleServerIRCBot.start(self)

    def routine_ping(self, first_run = False):
        """Ping server to know when try to reconnect to a new server."""
        global pinger
        if not first_run and not self.pong_received:
            print "Ping reply timeout, disconnecting from", self.connection.get_server_name()
            self.disconnect()
            return
        self.pong_received = False
        self.connection.ping(self.connection.get_server_name())
        pinger = Timer(ping_interval, self.routine_ping, ())
        pinger.start()

    def on_pong(self, connection, event):
        """React to pong"""
        self.pong_received = True

    def say(self, target, msg, do_say = True):
        """Send messages to channels/nicks"""
        target = target.lower()
        try:
            lines = msg.encode("UTF-8").split("\n")
            cur = 0
            for line in lines:
                for irc_msg in wrapper.wrap(line.strip("\r")):
                    print target, irc_msg
                    irc_msg += "\r\n"
                    if target not in lastsaid.keys():
                        lastsaid[target] = 0
                    while time.time()-lastsaid[target] < delay_btw_msgs:
                        time.sleep(0.2)
                    lastsaid[target]=time.time()
                    if do_say:
                        self.connection.privmsg(target, irc_msg)
                    else:
                        self.connection.notice(target, irc_msg)
                    cur += 1
                    if cur % max_seq_msgs == 0:
                        time.sleep(delay_btw_seqs) # to avoid flood excess
        except ServerNotConnectedError:
            print "{" +target + " " + msg+"} SKIPPED!"
			
    def notice(self, target, msg):
        """Send notices to channels/nicks"""
        self.say(self, target, msg, False)

    def on_welcome(self, connection, event):
        """Do stuff when when welcomed to server"""
        print "Connected to", self.connection.get_server_name()
        if password is not None:
            bot.say("NickServ", "identify " + password)
        self.connection.add_global_handler("ctcp", self.handle_ctcp)
        for pair in mirrors:
            connection.join(pair)
            print "Joined " + pair
        self.routine_ping(first_run = True)

    def on_pubmsg(self, connection, event):
        """React to channel messages"""
        args = event.arguments()
        source = event.source().split('!')[0]
        target = event.target().lower()
        cmds = args[0].split()
        if cmds and cmds[0].rstrip(":,") == nick:
            if len(cmds)==2:
                if cmds[1].upper() == 'ON' and source in mutedl[target]:
                    mutedl[target].remove(source)
                    save_mutes(target)
                elif cmds[1].upper() == 'OFF' and source not in mutedl[target]:
                    mutedl[target].append(source)
                    save_mutes(target)
            return
        if source in mutedl[target]:
            return
        msg = name_start + source + name_end + " "
        for raw in args:
            msg += decode_irc(raw) + "\n"
        msg = msg.rstrip("\n")
        print cut_title(usemap[target].FriendlyName), msg
        usemap[target].SendMessage(msg)

    def handle_ctcp(self, connection, event):
        """Handle CTCP events for emoting"""
        args = event.arguments()
        source = event.source().split('!')[0]
        target = event.target().lower()
        if target in mirrors.keys():
            if source in mutedl[target]:
                return
        if args[0]=='ACTION' and len(args) == 2:
            # An emote/action message has been sent to us
            msg = emote_char + " " + source + " " + decode_irc(args[1]) + "\n"
            print cut_title(usemap[target].FriendlyName), msg
            usemap[target].SendMessage(msg)

    def on_privmsg(self, connection, event):
        """React to ON, OF(F), ST(ATUS), IN(FO) etc for switching gateway (from IRC side only)"""
        source = event.source().split('!')[0]
        raw = event.arguments()[0].decode('utf-8', 'ignore')
        args = raw.split()
        if not args:
            return
        two = args[0][:2].upper()
        
        if two == 'ST': # STATUS
            muteds = []
            brdcsts = []
            for channel in mirrors.keys():
                if source in mutedl[channel]:
                    muteds.append(channel)
                else:
                    brdcsts.append(channel)
            if len(brdcsts) > 0:
                bot.say(source, "You're mirrored to Skype from " + ", ".join(brdcsts))
            if len(muteds) > 0:
                bot.say(source, "You're silent to Skype on " + ", ".join(muteds))
                
        if two == 'OF': # OFF
            for channel in mirrors.keys():
                if source not in mutedl[channel]:
                    mutedl[channel].append(source)
                    save_mutes(channel)
            bot.say(source, "You're silent to Skype now")
                
        elif two == 'ON': # ON
            for channel in mirrors.keys():
                if source in mutedl[channel]:
                    mutedl[channel].remove(source)
                    save_mutes(channel)
            bot.say(source, "You're mirrored to Skype now")
                
        elif two == 'IN' and len(args) > 1 and args[1] in mirrors: # INFO
            chat = usemap[args[1]]
            members = chat.Members
            active = chat.ActiveMembers
            msg = args[1] + " ⟷  \"".decode("UTF-8") + chat.FriendlyName + "\" (%d/%d)\n" % (len(active), len(members))
            # msg += chat.Blob + "\n"
            userList = []
            for user in members:
                if user in active:
                    desc = " * " + user.Handle + " [" + user.FullName
                else:
                    desc = " - " + user.Handle + " [" + user.FullName
                #print user.LastOnlineDatetime
                last_online = user.LastOnline
                timestr = ""
                if last_online > 0:
                    timestr += " --- " + get_relative_time(datetime.datetime.fromtimestamp(last_online))
                mood = user.MoodText
                if len(mood) > 0:
                    desc += ": \"" + mood + "\""
                desc += "]" + timestr
                userList.append(desc)
                userList.sort()
            for desc in userList:
                 msg += desc + '\n'
            msg = msg.rstrip("\n")
            bot.say(source, msg)
            
        elif two in ('?', 'HE', 'HI', 'WT'): # HELP
            bot.say(source, botname + " " + version + " " + topics + "\n * ON/OFF/STATUS --- Trigger mirroring to Skype\n * INFO #channel --- Display list of users from relevant Skype chat\nDetails: https://github.com/boamaod/skype2irc#readme")

# *** Start everything up! ***

signal.signal(signal.SIGINT, signal_handler)

print "Running", botname, "Gateway Bot", version
try:
    import Skype4Py
except:
    print 'Failed to locate Skype4Py API! Quitting...'
    sys.exit()
try:
    skype = Skype4Py.Skype();
except:
    print 'Cannot open Skype API! Quitting...'
    sys.exit()

if skype.Client.IsRunning:
    print 'Skype process found!'
elif not skype.Client.IsRunning:
    try:
        print 'Starting Skype process...'
        skype.Client.Start()
    except:
        print 'Failed to start Skype process! Quitting...'
        sys.exit()

try:
    skype.Attach();
    skype.OnMessageStatus = OnMessageStatus
    skype.OnNotify = OnNotify
except:
    print 'Failed to connect! You have to log in to your Skype instance and enable access to Skype for Skype4Py! Quitting...'
    sys.exit()

print 'Skype API initialised.'

topics = "["
for pair in mirrors:
    chat = skype.CreateChatUsingBlob(mirrors[pair])
    topic = chat.FriendlyName
    print "Joined \"" + topic + "\""
    topics += cut_title(topic) + "|"
    usemap[pair] = chat
    usemap[chat] = pair
topics = topics.rstrip("|") + "]"

load_mutes()

bot = MirrorBot()
print "Starting IRC bot..."
bot.start()

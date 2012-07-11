#! /usr/bin/env python
# -*- coding: utf-8 -*-

# IRC ⟷  Skype Gateway Bot: Connects Skype Chats to IRC Channels
# Copyright (C) 2012  Guido Tabbernuk <boamaod@gmail.com>
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

import sys
import ircbot
import time, datetime
import string

version = "0.0.1"

server = "irc.freenode.net"
port = 6667
nick = "skype-}"
botname = "IRC ⟷  Skype".decode('utf-8', 'ignore')
password = None
preferred_encodings = ["UTF-8", "CP1252", "ISO-8859-1"]

mirrors = {
'#test':
'X0_uprrk9XD40sCzSx_QtLT-oELEiV63Jw402jjG0dUaHiq2CD-F-6gKEQiFrgF_YPiUBcH-d6JcgmyWRPnteETG',
}

topics = ""

muted_list_filename = server + '.muted'

usemap = {}
bot = None
mutedl = []

# Time consts
SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
MONTH = 30 * DAY

def get_relative_time(dt):
    """Returns relative time compared to now from timestamp"""
    now = datetime.datetime.now()
    delta_time = now - dt

    delta =  delta_time.days * DAY + delta_time.seconds 
    minutes = delta / MINUTE
    hours = delta / HOUR
    days = delta / DAY

    if delta <= 0:
        return "in the future"
    if delta < 1 * MINUTE: 
      if delta == 1:
          return  "moment ago"
      else:
          return str(delta) + " seconds ago"
    if delta < 2 * MINUTE:    
        return "a minute ago"
    if delta < 45 * MINUTE:    
        return str(minutes) + " minutes ago"
    if delta < 90 * MINUTE:    
        return "an hour ago"
    if delta < 24 * HOUR:
        return str(hours) + " hours ago"
    if delta < 48 * HOUR:    
        return "yesterday"
    if delta < 30 * DAY:    
        return str(days) + " days ago"
    if delta < 12 * MONTH:    
        months = delta / MONTH
        if months <= 1:
            return "one month ago"
        else:
            return str(months) + " months ago"
    else:    
      years = days / 365.0
      if  years <= 1:
          return "one year ago"
      else:
          return str(years) + " years ago"

def cut_title(title):
    """Cuts chat title to be ok"""
    newtitle = ""
    for chunk in title.split():
        newtitle += chunk.strip(string.punctuation) + " "
        if len(newtitle) > 10:
            break
    return newtitle.strip()
    
def load_mutes():
    """Loads people who don't want to be broadcasted from IRC to Skype"""
    try:
        f = open(muted_list_filename, 'r')
        for line in f.readlines():
            name = line.replace('\n', '');
            mutedl.append(name)
            mutedl.sort()
        f.close()
        print 'Added list of ' + str(len(mutedl)) + ' mutes!'
    except:
        pass

def save_mutes():
    """Saves people who don't want to be broadcasted from IRC to Skype"""
    try:
        f = open(muted_list_filename, 'w')
        for name in mutedl:
            f.write(name + '\n')
        mutedl.sort()
        f.close
        print 'Saved ' + str(len(mutedl)) + ' mutes!'
    except:
        pass

def OnMessageStatus(Message, Status):
    """Create Skype object listener"""
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
                bot.say(usemap[chat], '* ' + senderHandle + ' ' + raw)
            elif msgtype == 'SAID':
                bot.say(usemap[chat], '<' + senderHandle + '> ' + raw)

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
            enc = chardet.detect(raw)['encoding']
            res = raw.decode(enc)
        except:
            res = raw.decode(enc, 'ignore')
            #enc += "+IGNORE"
    return res
    
class MirrorBot (ircbot.SingleServerIRCBot):
    """Create IRC bot class"""
    
    def say(self, target, msg, do_say = True):
        """Send messages to channels/nicks"""
        print target, msg
        lines = msg.encode("UTF-8").split("\n")
        cur = 0
        for line in lines:
            if do_say:
                self.connection.privmsg(target, line)
            else:
                self.connection.notice(target, line)
            cur += 1
            if cur % 4 == 0:
                time.sleep(3) # to avoid flood excess

    def notice(self, target, msg):
        """Send notices to channels/nicks"""
        self.say(self, target, msg, False)

    def on_welcome(self, connection, event):
        """Do stuff when when welcomed to server"""
        if password is not None:
            bot.say("NickServ", "identify " + password)
        self.connection.add_global_handler("ctcp", self.handle_ctcp)
        for pair in mirrors:
            connection.join(pair)
            print "Joined " + pair

    def on_pubmsg(self, connection, event):
        """React to channel messages"""
        source = event.source().split('!')[0]
        if source in mutedl:
            return
        msg = "<" + source + "> "
        target = event.target()
        for raw in event.arguments():
            msg += decode_irc(raw) + "\n"
        # A regular message has been sent to us
        msg = msg.rstrip("\n")
        print cut_title(usemap[target].FriendlyName), msg
        usemap[target].SendMessage(msg)

    def handle_ctcp(self, connection, event):
        """Handle ctcp events for emoting"""
        source = event.source().split('!')[0]
        if source in mutedl:
            return
        target = event.target()
        raw = event.arguments()[0].decode('utf-8', 'ignore')
        msg = "* " + source + " " + raw
        # An emote/action message has been sent to us
        if (event.arguments()[0]=='ACTION'):
            print cut_title(usemap[target].FriendlyName), msg
            usemap[target].SendMessage(msg)

    def on_privmsg(self, connection, event):
        """React to ON, OF(F), ST(ATUS), IN(FO) etc for switching gateway (from IRC side only)"""
        source = event.source().split('!')[0]
        raw = event.arguments()[0].decode('utf-8', 'ignore')
        args = raw.split()
        two = args[0][:2].upper()
        
        if two == 'ST': # STATUS
            if source in mutedl:
                bot.say(source, "You're muted")
            else:
                bot.say(source, "You're broadcasted")
                
        if two == 'OF': # OFF
            if source not in mutedl:
                mutedl.append(source)
                save_mutes()
                bot.say(source, "You're muted now")
                
        elif two == 'ON': # ON
            if source in mutedl:
                mutedl.remove(source)
                save_mutes()
                bot.say(source, "You're broadcasted now")
                
        elif two == 'IN' and len(args) > 1 and args[1] in mirrors: # INFO
            chat = usemap[args[1]]
            members = chat.Members
            active = chat.ActiveMembers
            msg = args[1] + " ⟷  \"".decode('utf-8', 'ignore') + chat.FriendlyName + "\" (%d/%d)\n" % (len(active), len(members))
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
            msg = msg[0:len(msg)-1] # remove '\n'
            bot.say(source, msg)
            
        elif two in ('/', '?', 'HE'): # HELP
            bot.say(source, botname + " " + version + " " + topics + ":\n * ON/OFF/STATUS --- Trigger broadcasting to Skype\n * INFO #channel --- Display list of users from relevant Skype chat")

# *** Start everything up! ***
    
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

bot = MirrorBot ([( server, port )], nick, (botname + " " + topics).encode("UTF-8"))
print "Starting IRC bot..."
bot.start()

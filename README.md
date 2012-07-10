IRC ⟷  Skype Gateway Bot
=========================

FEATURES
--------

* Mirror all messages from IRC channel to Skype chatroom and vice versa
* Support regular messages and emotes (`/em`)
* Provide bot commands from IRC side using direct messages to the bot
  * Turn broadcasting to Skype `ON` or `OFF` for the user, get present `STATUS`
  * Query for Skype users connected to channel using `INFO #channel`

INSTALL
-------

On Ubuntu/Debian you need `python-irclib` and `python-skype` as well as Skype itself to run the script.

If you are using `python-irclib` 0.4.8 from Ubuntu 12.04 repositories, you have to patch `/usr/share/pyshared/irclib.py` like that:

    --- irclib_old.py	2012-07-10 20:44:10.341948937 +0300
    +++ irclib_new.py	2012-07-10 20:51:48.989934682 +0300
    @@ -785,9 +785,9 @@
                 raise ServerNotConnectedError, "Not connected."
             try:
                 if self.ssl:
    -                self.ssl.write(string + "\r\n")
    +                self.ssl.write(string.encode('utf-8') + "\r\n")
                 else:
    -                self.socket.send(string + "\r\n")
    +                self.socket.send(string.encode('utf-8') + "\r\n")
                 if DEBUG:
                     print "TO SERVER:", string
             except socket.error, x:

If you use `python-irclib` 0.6.4 from [SourceForge][], you still have to do it.

For python-skype I used the version 1.0.31.0 provided at `ppa:skype-wrapper/ppa`. Although newer version is packaged even for Ubuntu 11.04, this package didn't work out of the box on Ubuntu 12.04.

Skype has to be installed to use Skype API, which is used to communicate with Skype.

[SourceForge]: http://sourceforge.net/projects/python-irclib/

CONFIGURE
---------

You can configure the IRC servers and Skype chatrooms to mirror in the header of `skype2irc.py`. You are able to define one IRC server and as many pairs of IRC channel and Skype chatroom as you like. Skype chatrooms are defined by the blob, which you can obtain writing `/get uri` in a chatroom.

You may need to join your Skype chatroom to be mirrored before actually starting the gateway, because it seems that Skype API isn't always able to successfully join the chatroom using a blob provided. Make sure you have an access to chatroom using GUI before starting to hassle with the code.

The default values provided in the header of `skype2irc.py` should be enough to give the program a test run.

If you want to use an option to save broadcast states for IRC users, working directory for the script has to be writable.

RUN
--- 

To run the gateway, Skype must be running and you must be logged in. You can do command line log in using `echo username password | skype --pipelogin` or you may just enable auto login from GUI. If you start `skype2irc.py` there will be a pop up window opened by your Skype instance on first run to authorize access to Skype for Skype4Py. You can either allow access just once or remember your choice.

You can run `skype2irc.py` just from command line or use `ircbot.sh` to loop it. You can also run it from plain terminal providing the X desktop Skype will be started like `DISPLAY="host:0.0" ./skype2irc.py`.

It could also make sense to run it using `ssh -X user@host` session or with something similar.

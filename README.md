Simple IRC ⟷  Skype Gateway Bot
================================

FEATURES
--------

* Mirror messages from IRC channel to Skype chatroom and vice versa
* Support regular messages and emotes (`/em`)
* Provide commands from IRC side using direct messages to the bot
  * Turn broadcasting to Skype `ON` or `OFF` for the user, get user's present `STATUS`
  * Query for Skype users mirrored to IRC channel using `INFO #channel`
* Quick and transparent Skype broadcasting `ON` and `OFF` during chat by adressing the bot in channel openly with a string for desired state

**This bot deliberately prefers IRC to Skype!**

INSTALL
-------

On Ubuntu/Debian you need `python-irclib` and `python-skype` as well as Skype itself to run the script.

For `python-skype` I used the version 1.0.31.0 provided at `ppa:skype-wrapper/ppa`. Although newer version is packaged even for Ubuntu 11.04, this package didn't work out of the box on Ubuntu 12.04.

CONFIGURE
---------

You can configure the IRC servers and Skype chatrooms to mirror in the header of `skype2irc.py`. You may define one IRC server and as many pairs of IRC channels and Skype chatrooms as you like. Skype chatrooms are defined by the blob, which you can obtain writing `/get uri` in a chatroom.

You may need to join your Skype chatroom to be mirrored before actually starting the gateway, because it seems that Skype API isn't always able to successfully join the chatroom using a blob provided (I usually get a timeout error). So make sure you have an access to chatroom using GUI before starting to hassle with the code.

The default values provided in the header of `skype2irc.py` should be enough to give the program a test run.

If you want to use an option to save broadcast states for IRC users, working directory for the script has to be writable.

RUN
--- 

To run the gateway, Skype must be running and you must be logged in. You can do command line log in using `echo username password | skype --pipelogin` or you may just enable auto login from GUI. If you start `skype2irc.py` there will be a pop up window opened by your Skype instance on first run to authorize access to Skype for Skype4Py. You can either allow access just once or remember your choice.

You can run `skype2irc.py` just from command line or use `ircbot.sh` to loop it. You can also run it from plain terminal providing the X desktop Skype will be started like `DISPLAY="host:0.0" ./skype2irc.py`.

It could also make sense to run it using `ssh -X user@host` session or with something similar.

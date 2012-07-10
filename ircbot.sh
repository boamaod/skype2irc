#!/bin/sh

echo "Initiating IRC ⟷  Skype Gateway Bot"

while :
do

   date --rfc-3339=seconds | sed -r -e "s/(.*)/\1 STARTED/"
   DISPLAY="host:0.0" python skype2irc.py
   date --rfc-3339=seconds | sed -r -e "s/(.*)/\1 STOPPED/"
   sleep 30

done

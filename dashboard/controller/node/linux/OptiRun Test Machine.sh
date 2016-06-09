#!/bin/bash

if [ "$(id -u)" != "0" ]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

chmod +x drivers/chromedriver
apt-get install --upgrade python
apt-get install --upgrade python2.7
apt-get install java-common
apt-get install default-jre
apt-get install selenium

python start.py

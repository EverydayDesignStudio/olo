#!/bin/sh
# oloLauncher.sh

### Follow instructions on https://github.com/EverydayDesignStudio/olo/blob/master/README.md to add this script to Cron

### @reboot sh /home/pi/bbt/oloLauncher.sh >/home/pi/logs/cronlog 2>&1

cd /
cd /home/pi/Desktop/olo
sudo python3 oloMain.py
cd/

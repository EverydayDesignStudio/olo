#!/bin/sh
# oloUpdater.sh

### Follow instructions on https://github.com/EverydayDesignStudio/olo/blob/master/README.md to add this script to Cron

### 0 4 * * * sh /home/pi/bbt/oloUpdater.sh >/home/pi/logs/cronlog 2>&1

cd /
cd /home/pi/Desktop/olo
sudo python3 dbUpdate.py > /home/pi/Desktop/olo/updateLog.txt
cd/

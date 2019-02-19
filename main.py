#!/usr/bin/env python3
#-*-coding:utf-8-*-

### TODO:

# 1:
#   ** Use Linux Process Monitor (https://gist.github.com/connorjan/01f995511cfd0fee1cfae2387024b54a)
#   - run script on boot
#   - auto recovery on exception

#   - *** headless start to connect to wifi >> Making RPI as an Access Point ???

#   ** Adjustments in the Main script
#   - fade-out when switching musics
#   - no random selection in a bucket >> create counter for buckets and initialize when update
#   - calculate abs bucket index for year >> calculate the diff from the oldest and the newest entry >> add to sh (global var)
#   - define abs bucket size for months and days >> fixed number = constant var
#   - normalize volume control (https://mycurvefit.com/)





import dbtest as fn
import sh
sh.init()
import os.path
from random import randint
import spotipy
import RPi.GPIO as gpio
import oloFunctions as olo
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from oloFunctions import *

current_milli_time = lambda: int(round(time.time() * 1000))

sliderOffset = 15
bucketSize = 16
basepath = os.path.abspath(os.path.dirname(__file__))
# dbpath = os.path.join(basepath, "./test.db")
dbpath = os.path.join(basepath, "./sample.db")

#if (os.name == 'nt'):
# username = '31r27sr4fzqqd24rbs65vntslaoq'
# client_id = '3f77a1d68f404a7cb5e63614fca549e3'
# client_secret = '966f425775d7403cbbd66b838b23a488'
# device_desktop = '2358d9d7c020e03c0599e66bb3cb244347dfe392'
# device_oloradio1 = '1daca38d2ae160b6f1b8f4919655275043b2e5b4'
# else:
scope = 'user-modify-playback-state'
username = '9mgcb91qlhdu2kh4nwj83p165'
client_id = '86456db5c5364110aa9372794e146bf9'
client_secret = 'cd7177a48c3b4ea2a6139b88c1ca87f5'
device_oloradio1 = '984b0223d4e3c3fec177a61e40c42c935217020c'
redirect_uri = 'https://example.com/callback/'


token = fn.getSpotifyAuthToken()
sp = spotipy.Spotify(auth=token)

# TODO: save and load from a file
lastUpdatedDate = 0

# STATUS VARIABLES
mode = 0  # Mode: 0 - life, 1 - year, 2 - day
volume = 0
currSliderPos = 0

# currBucket
startTime = 0
currSongTime = 0
currSongTimestamp = 0
currVolume = 0
currBucket = 0
currMode = ""

loopCount = 0
loopPerBucket = 1

isPlaying = False
isOn = False
isMoving = False

cur = fn.getDBCursor()
totalCount = fn.getTotalCount(cur);
totalBuckets = int(1024/bucketSize);
### TODO: do not calculate the pos by #songs in a bucket - use abs index
songsInABucket = int(totalCount/totalBuckets);

### TODO: enble pins
mcp = Adafruit_MCP3008.MCP3008(clk=sh.CLK, cs=sh.CS, miso=sh.MISO, mosi=sh.MOSI)

# GPIO configuration:
gpio.setup(sh.mEnable, gpio.OUT) #gpio 6  - motor driver enable
gpio.setup(sh.mLeft, gpio.OUT) #gpio 13 - motor driver direction 1
gpio.setup(sh.mRight, gpio.OUT) #gpio 12 - motor driver direction 2

gpio.setup(sh.switch1, gpio.IN) #gpio 16  - three pole switch 1
gpio.setup(sh.switch2, gpio.IN) #gpio 18  - three pole switch 2

gpio.output(sh.mEnable, True) # Enable motor driver

# turn off other outputs:
gpio.output(sh.mLeft, False)
gpio.output(sh.mRight, False)

# returns the start time and the current song's playtime in ms
def playSongInBucket(bucket, mode, currSliderPos):
    songPos = randint(int(bucket*songsInABucket), int((bucket+1)*songsInABucket)-1)
    song = fn.getTrackByIndex(cur, mode, songPos)
    songURI = song[9]
    sp.start_playback(device_id = device_oloradio1, uris = [songURI])
    print("## now playing: " + song[2] + " - " + song[1] + ", time: tmp @ " + str(currSliderPos))
    res = sp.track(songURI)
    return song[0], current_milli_time(), int(res['duration_ms'])
    # return song[0], current_milli_time(), 10000;



def checkValues(isOn, isMoving, isPlaying, loopCount, currVolume, currSliderPos, currBucket, currSongTime, startTime, currMode, currSongTimestamp):
    print("##### total songs: {}, bucket size: {}".format(totalCount, songsInABucket))
    while (True):
        ### read values
        readValues();
        timeframe();
#        print(sh.values);
        pin_Volume = sh.values[4];
        pin_Touch = sh.values[6]
        pin_SliderPos = sh.values[7];
        pin_Mode = sh.timeframe

        # just turned on (plugged in) with volume on
        if (not isPlaying and isOn):
            print("@@ ON but not PLAYING!")
            currSliderPos = pin_SliderPos
            currMode = pin_Mode;
            print("pinMode: " + pin_Mode)
            print("currMode: " + currMode)
            # set the position
            currBucket = int(currSliderPos / 1024)
            currSongTimestamp, startTime, currSongTime = playSongInBucket(currBucket, currMode, currSliderPos)
            isPlaying = True;

        # - volume 0
        if (isOn and pin_Volume is 0):
#            print("@@ Turning OFF!")
            # TODO: check last update date, then update lastFM list once in a day
            isOn = False
            isPlaying = False
            # TODO: pause the song that was currently playing
            continue;
        # - volume +
        if (not isOn and pin_Volume > 0):
#            print("@@ Turning ON!")
            isOn = True
            currMode = pin_Mode;

        ### events
        # - volume change
        vol = int(pin_Volume/10)
        if (abs(currVolume - vol) > 2):
            currVolume = vol
            if (currVolume > 100):
                currVolume = 100;
            fn.setVolume(volume = currVolume)

        # - slider move - capacitive touch
        if (isOn and not isMoving and pin_Touch > 100):
            isMoving = True
        if (isOn and isMoving and pin_Touch < 100):
            # set loopCount to 0
            loopCount = 0;
            isMoving = False
            currSliderPos = pin_SliderPos
            # set the position
            currBucket = int(currSliderPos / 1024)
            currSongTimestamp, startTime, currSongTime = playSongInBucket(currBucket, currMode, currSliderPos)


        # - mode change
        # * no dot move slider when touched
        if (isOn and not isMoving and currMode != pin_Mode):
            if (pin_Mode == 'err'):
                continue;
            print('currSongTimestamp: ' + str(currSongTimestamp))
            print('{} -> {} '.format(currMode, pin_Mode))
            currMode = pin_Mode
            index = int(fn.findTrackIndex(cur, currMode, currSongTimestamp)[0])
            print("@@ new index: {}/{} = {}".format(index, songsInABucket, int(index/songsInABucket)))
            index = int(index/songsInABucket)
            currSliderPos = index*bucketSize # + bucketSize/2

            olo.moveslider(currSliderPos)

        # a song has ended
#        print("### time elapsed: " + str(current_milli_time() - startTime) + ", CST: " + str(currSongTime))
        if (isOn and isPlaying and (current_milli_time() - startTime) > currSongTime):
#            res = sp.current_playback()
#            isPlaying = res['is_playing']
            isPlaying = False;
            if (not isPlaying):
                # - loop
                if (loopCount < loopPerBucket):
                    print("@@ LOOP!! Loopcount: " + str(loopCount) + "/" + str(loopPerBucket))
                    loopCount += 1;
                # - song end -> next
                # error margin: 6, bucket size is 16; 64 buckets, but trim accordingly on both ends
                else:
                    print("@@ NO LOOP! Next song..")
                    loopCount = 0
                    # - go back to the beginning when slider hits the end
                    currSliderPos = (currSliderPos + sliderOffset) % 1024
                    currBucket = int(currSliderPos / 1024)
                    olo.moveslider(currSliderPos)
                currSongTimestamp, startTime, currSongTime = playSongInBucket(currBucket, currMode, currSliderPos)
                isPlaying = True


# -------------------------

try:
    print("### Main is starting..")
    checkValues(isOn, isMoving, isPlaying, loopCount, currVolume, currSliderPos, currBucket, currSongTime, startTime, currMode, currSongTimestamp)
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

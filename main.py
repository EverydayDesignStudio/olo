#!/usr/bin/env python3
#-*-coding:utf-8-*-

### TODO:

#   ** Use Linux Process Monitor (https://gist.github.com/connorjan/01f995511cfd0fee1cfae2387024b54a)
#   - run script on boot

#   - *** headless start to connect to wifi >> Making RPI as an Access Point ???

#   - fade-out when switching musics
#   - normalize volume control (https://mycurvefit.com/)

import dbtest as fn
import sh
sh.init()
import os.path, math, sys
import spotipy
import RPi.GPIO as gpio
import oloFunctions as olo
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from oloFunctions import *

current_milli_time = lambda: int(round(time.time() * 1000))

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

# STATUS VARIABLES
mode = 0  # Mode: 0 - life, 1 - year, 2 - day
volume = 0
currSliderPos = 0
sliderOffset = 15
bucketSize = 16

# currBucket
startTime = 0
currSongTime = 0
currSongTimestamp = 0
currVolume = None # [0, 100]
currBucket = 0 # [0, 63]
currMode = "" # ('life, 'year', 'day')

loopCount = 0
loopPerBucket = 1

isPlaying = False
isOn = False
isMoving = False

cur = fn.getDBCursor()
totalCount = fn.getTotalCount(cur);
totalBuckets = int(1024/bucketSize);
LIFEWINDOWSIZE = fn.getLifeWindowSize(cur);
BASELIFEOFFSET = fn.getBaseTimestamp(cur);
BUCKETWIDTH_LIFE = int(math.ceil(LIFEWINDOWSIZE/64))
BUCKETWIDTH_YEAR = 492750 # (86400*365)/64
BUCKETWIDTH_DAY = 1350 # 86400/64

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
def playSongInBucket(currBucket, mode, currSliderPos, bucketWidth, bucketCounter, offset):
    song = fn.getTrackFromBucket(cur, mode, offset+(currBucket*bucketWidth), bucketCounter[currBucket])
    songURI = song[9]
    sp.start_playback(device_id = device_oloradio1, uris = [songURI])
    print("## now playing: {} - {} ({}), at Bucket [{}]({}): {}".format(song[2], song[1], songURI, str(currBucket), str(currSliderPos), str(bucketCounter[currBucket])))
    res = sp.track(songURI)
    return song[0], current_milli_time(), int(res['duration_ms'])
    # return song[0], current_milli_time(), 10000;

def gotoNextNonEmptyBucket(bucketCounter, currMode, currBucket, songsInABucket, currSliderPos, offset, bucketWidth):
    reachedTheEnd = False;
    sPos = None;
    # there is no song in a bucket
    while (bucketCounter[currBucket] >= songsInABucket):
        # reset the current counter and proceed to the next bucket
        print("@@@@ Skipping a bucket!!")
        bucketCounter[currBucket] = 0
        currBucket += 1
        # simulate the behavior where the search hits to the end and goes back to the beginning
        if (currBucket == 64):
            reachedTheEnd = True
            sPos = currSliderPos
        currBucket = currBucket % 64;
        currSliderPos = (currBucket*bucketSize) + sliderOffset
        songsInABucket = fn.getBucketCount(cur, currMode, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth)
#        print("## currMode: {}, offset: {}, currBucket:{}, bucketWidth:{}, [{}, {}]".format(currMode, offset, currBucket, bucketWidth, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth))
        print("@@ Bucket[{}]: {} out of {} songs".format(str(currBucket), str(bucketCounter[currBucket]), str(songsInABucket)))
    print("@@ B[{}]: {} ({} ~ {}, offset: {})".format(str(currBucket), bucketCounter[currBucket], offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth, offset))
    if (reachedTheEnd and sPos is not None and sPos > 1010):
        olo.moveslider(1022)
    olo.moveslider(currSliderPos)
    return bucketCounter, currBucket, songsInABucket, currSliderPos

def checkValues(isOn, isMoving, isPlaying, loopCount, currVolume, currSliderPos, currBucket, currSongTime, startTime, currMode, currSongTimestamp):
    print("##### total songs: {}".format(totalCount))
    print("##### Life mode base value: {}".format(BASELIFEOFFSET))
    while (True):
        ### read values
        readValues();
        timeframe();
#        print(sh.values);
        pin_Volume = sh.values[4];
        pin_Touch = sh.values[6]
        pin_SliderPos = sh.values[7];
        pin_Mode = sh.timeframe
        bucketCounter = sh.bucketCounter;

        bucketWidth = 0
        offset = BASELIFEOFFSET
        bucketWidth = BUCKETWIDTH_LIFE
        if (pin_Mode is 'day'):
            offset = 0;
            if (totalCount > BUCKETWIDTH_DAY):
                bucketWidth = BUCKETWIDTH_DAY
        elif (pin_Mode is 'year'):
            offset = 0;
            if (totalCount > BUCKETWIDTH_YEAR):
                bucketWidth = BUCKETWIDTH_YEAR

        if (currVolume is None):
            currVolume = int(pin_Volume/10);

        # OLO is on but the music is not playing (either OLO is just turned on or a song has just finished)
        if (not isPlaying and isOn):
            print("@@ ON but not PLAYING!, Slider @ {}".format(pin_SliderPos))
            currSliderPos = pin_SliderPos
            currMode = pin_Mode;
            # set the position
            currBucket = int(math.floor(currSliderPos/16))
            songsInABucket = fn.getBucketCount(cur, currMode, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth)

#            currSongTimestamp, startTime, currSongTime = playSongInBucket(currBucket, currMode, currSliderPos, bucketWidth, bucketCounter)

            print("@@ Next song @ Bucket[{}]: {} out of {} songs".format(str(currBucket), str(bucketCounter[currBucket]), str(songsInABucket)))
            print("@@ mode: {}, volume: {}, bucketWidth: {}".format(pin_Mode, str(currVolume), bucketWidth))
            print("@@ B[{}]: {} (offset: {} ~ {})".format(str(currBucket), bucketCounter[currBucket], offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth))

            bucketCounter, currBucket, songsInABucket, currSliderPos = gotoNextNonEmptyBucket(bucketCounter, currMode, currBucket, songsInABucket, currSliderPos, offset, bucketWidth)
            bucketCounter[currBucket] += 1;
            currSongTimestamp, startTime, currSongTime = playSongInBucket(currBucket, currMode, currSliderPos, bucketWidth, bucketCounter, offset)

            isPlaying = True

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
            fn.setVolume(volume=currVolume, device=device_oloradio1, sp=sp)

        # - slider move - capacitive touch
        if (isOn and not isMoving and pin_Touch > 100):
            isMoving = True
        if (isOn and isMoving and pin_Touch < 100):
            # set loopCount to 0
            loopCount = 0;
            currSliderPos = pin_SliderPos
            # set the position
            newBucket = int(math.floor(currSliderPos/16))
            # do not skip the song if the slider is touched but not moved
            if (currBucket != newBucket):
                currBucket = newBucket
                songsInABucket = fn.getBucketCount(cur, currMode, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth)
                print("@@ Now playing song @ Bucket[{}]: {} out of {} songs".format(str(currBucket), str(bucketCounter[currBucket]), str(songsInABucket)))
                print("@@ mode: {}, volume: {}, bucketWidth: {}".format(pin_Mode, str(currVolume), bucketWidth))
                print("@@ B[{}]: {} (offset: {} ~ {})".format(str(currBucket), bucketCounter[currBucket], offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth))

                bucketCounter, currBucket, songsInABucket, currSliderPos = gotoNextNonEmptyBucket(bucketCounter, currMode, currBucket, songsInABucket, currSliderPos, offset, bucketWidth)
                bucketCounter[currBucket] += 1;
                currSongTimestamp, startTime, currSongTime = playSongInBucket(currBucket, currMode, currSliderPos, bucketWidth, bucketCounter, offset)

            isMoving = False

        # - mode change
        # * no dot move slider when touched
        if (isOn and not isMoving and currMode != pin_Mode):
            if (pin_Mode == 'err'):
                continue;

            print('currSongTimestamp: ' + str(currSongTimestamp))
            print('@@@ Mode Changed!! {} -> {} '.format(currMode, pin_Mode))

            # reset the bucketWidth
            if (pin_Mode is 'day'):
                offset = 0;
                bucketWidth = BUCKETWIDTH_DAY
            elif (pin_Mode is 'year'):
                offset = 0;
                bucketWidth = BUCKETWIDTH_YEAR
            else:
                offset = BASELIFEOFFSET
                bucketWidth = BUCKETWIDTH_LIFE
            currMode = pin_Mode
            index = int(fn.findTrackIndex(cur, currMode, currSongTimestamp)[0])-1 # index is 1 less than the order number
            currBucket = int(math.floor(index/bucketWidth))
#            bucketCounter[currBucket] = index - (currBucket*bucketWidth)

            songsInABucket = fn.getBucketCount(cur, currMode, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth)
            print("@@ new index: {} / {} in {} mode,, playing {} out of {} songs".format(str(index), str(totalCount), currMode, str(bucketCounter[currBucket]), str(songsInABucket)))

            currSliderPos = (currBucket*bucketSize) + sliderOffset
            olo.moveslider(currSliderPos)

        # a song has ended
#        print("### time elapsed: " + str(current_milli_time() - startTime) + ", CST: " + str(currSongTime))
        if (isOn and isPlaying and (current_milli_time() - startTime) > currSongTime):
#            res = sp.current_playback()
#            isPlaying = res['is_playing']

            isPlaying = False;


# -------------------------

try:
    print("### Main is starting..")
    checkValues(isOn, isMoving, isPlaying, loopCount, currVolume, currSliderPos, currBucket, currSongTime, startTime, currMode, currSongTimestamp)
except:
    raise


# for _ in range(5):
#     try:
#         print("### Main is starting..")
#         checkValues(isOn, isMoving, isPlaying, loopCount, currVolume, currSliderPos, currBucket, currSongTime, startTime, currMode, currSongTimestamp)
#     except (KeyboardInterrupt, SystemExit):
#         raise
#     except:
#         print("Unexpected error:", sys.exc_info()[0])
#         continue;

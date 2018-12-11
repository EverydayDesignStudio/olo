#-*-coding:utf-8-*-
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


sliderOffset = 15
bucketSize = 16
basepath = os.path.abspath(os.path.dirname(__file__))
dbpath = os.path.join(basepath, "./test.db")

#if (os.name == 'nt'):
username = '31r27sr4fzqqd24rbs65vntslaoq'
client_id = '3f77a1d68f404a7cb5e63614fca549e3'
client_secret = '966f425775d7403cbbd66b838b23a488'
device_desktop = '2358d9d7c020e03c0599e66bb3cb244347dfe392'
# device_oloradio1 = '1daca38d2ae160b6f1b8f4919655275043b2e5b4'
# else:
    # username = '9mgcb91qlhdu2kh4nwj83p165'
    # client_id = '86456db5c5364110aa9372794e146bf9'
    # client_secret = 'cd7177a48c3b4ea2a6139b88c1ca87f5'
    # device_oloradio1 = 'edstudio2018'
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

loopCount = 0
loopPerBucket = 1

isPlaying = False
isOn = False
isMoving = False

cur = fn.getDBCursor()
totalCount = fn.getTotalCount(cur);
songsInABucket = totalCount/bucketSize;

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


def playSongInBucket(bucket, currSliderPos, isPlaying=None):
    songPos = randint(int(bucket*songsInABucket), int((bucket+1)*songsInABucket)-1)
    modeStr = "";
    if (mode == 0):
        modeStr = 'life'
    elif (mode == 1):
        modeStr = 'year'
    elif (mode == 2):
        modeStr = 'day'
    song = fn.getTrackByIndex(cur, modeStr, songPos)
    songURI = song[9]
    currSongTimestamp = song[0]
#    res = sp.track(songURI)
#    currSongTime = int(res['duration_ms'])
    # sp.start_playback(uris = songURI)
    startTime = time.time()
    if (isPlaying is not None):
        isPlaying = True
    print("## now playing: " + song[2] + " - " + song[1] + ", time: tmp @ " + str(currSliderPos))


def checkValues(isOn, isMoving, isPlaying, currVolume, currSliderPos):
    while (True):
        ### read values
        readValues();
        timeframe();
#        print(sh.values);
        pin_Volume = sh.values[0];
        pin_SliderPos = sh.values[7];

        # just turned on (plugged in) with volume on
        if (isOn and not isPlaying):
            print("@@ ON but not PLAYING!")
            currSliderPos = pin_SliderPos
            # set the position
            currBucket = int(currSliderPos / 1024)
            playSongInBucket(currBucket, currSliderPos, isPlaying)

        # - volume 0
        if (isOn and pin_Volume is 0):
            print("@@ Turning OFF!")
            # TODO: check last update date, then update lastFM list once in a day
            isOn = False
            isPlaying = False
            # TODO: pause the song that was currently playing
            continue;
        # - volume +
        if (not isOn and pin_Volume > 0):
            print("@@ Turning ON!")
            isOn = True

        ### events
        # - volume change
        vol = int(pin_Volume/10)
        if (currVolume != vol):
            currVolume = vol
            fn.setVolume(volume = currVolume)

        # - slider move - capacitive touch
        touch = sh.values[6]
        if (isOn and not isMoving and touch > 400):
            isMoving = True
        if (isOn and isMoving and touch < 400):
            # set loopCount to 0
            loopCount = 0;
            currSliderPos = pin_SliderPos
            # set the position
            currBucket = int(currSliderPos / 1024)
            playSongInBucket(currBucket, currSliderPos)

        #
        # # - mode change
        # if (modeChange):
        #     mode = newMode
        #     index = (fn.findTrackIndex(cur, mode, currSongTimestamp)/songsInABucket)
        #     currSliderPos = index*bucketSize # + bucketSize/2
        #

        #
        # # a song has ended
        # if (time.time() - startTime > currSongTime):
        #     res = sp.current_playback()
        #     if (res['is_playing'] is False):
        #         # - loop
        #         if (loopCount < loopPerBucket):
        #             loopCount++;
        #             playSongInBucket(currBucket)
        #         # - song end -> next
        #         # error margin: 6, bucket size is 16; 64 buckets, but trim accordingly on both ends
        #         else:
        #             loopCount = 0
        #             # - go back to the beginning when slider hits the end
        #             currSliderPos = (currSliderPos + sliderOffset) % 1024
        #             olo.moveslider(currSliderPos)
        #

# -------------------------

try:
    print("### Main is starting..")
    checkValues(isOn, isMoving, isPlaying, currVolume, currSliderPos)
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

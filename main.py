#-*-coding:utf-8-*-
import dbtest as fn
import sh
sh.init()
import os.path
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


def playSongInBucket(bucket):
    songPos = random(bucket*songsInABucket, (bucket+1)*songsInABucket)
    song = fn.getTrackByIndex(cur, mode, songPos)
    songURI = song[9]
    currSongTimestamp = song[0]
    res = sp.track(songURI)
    currSongTime = int(res['duration_ms'])
    print("## now playing: " + song[2] + " - " + song[1] + ", time: " + currSongTime)
    # sp.start_playback(uris = songURI)
    startTime = time.time()

def checkValues(isOn, currVolume):
    while (True):
        ### read values
        readValues();
        timeframe();
        print(sh.values);
        pin_Volume = sh.values[0];

        # - volume 0
        if (isOn and pin_Volume is 0):
            #TODO: check last update date, then update lastFM list once in a day
            isOn = False
            continue;
        # - volume +
        elif (not isOn and pin_Volume > 0):
            isOn = True

        ### events
        # - volume change
        vol = int(pin_Volume/10)
        if (currVolume != vol):
            currVolume = vol
            fn.setVolume(volume = currVolume)

        # - slider move
        if (isOn and sliderMoves):
            # set loopCount to 0
            loopCount = 0;
            # set the position
            currBucket = int(sliderPos / 1024)
            playSongInBucket(currBucket)
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
    checkValues(isOn, currVolume)
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

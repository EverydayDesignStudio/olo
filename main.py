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
    sp.start_playback(uris = songURI)
    startTime = time.time()

def checkValues():
    while (True):
        ### read values
        readValues();
        timeframe();
        print(sh.values);

        #
        # ### events
        # # - volume change
        # if (volumeChange):
        #     fn.setVolume(pinVal/10)
        # # - slider move
        # if (isOn and sliderMoves):
        #     # set loopCount to 0
        #     loopCount = 0;
        #     # set the position
        #     currBucket = int(sliderPos / 1024)
        #     playSongInBucket(currBucket)
        #
        # # - mode change
        # if (modeChange):
        #     mode = newMode
        #     index = (fn.findTrackIndex(cur, mode, currSongTimestamp)/songsInABucket)
        #     currSliderPos = index*bucketSize # + bucketSize/2
        #
        # # - volume 0
        # if (isOn and volume_pin is 0):
        #     #TODO: check last update date, then update lastFM list once in a day
        #     continue;
        # # - volume +
        # elif (not isOn and volume_pin > 0):
        #     isOn = True
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
    checkValues()
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

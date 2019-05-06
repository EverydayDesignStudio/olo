#-*-coding:utf-8-*-

### TODO:
#   - fade-in/fade-out when turning on & switching musics
#   - *** headless start: edit wpa_supplicant.conf


import os
import traceback
import os.path, math, sys, time

import spotipy
import spotipy.util as util
import spotipy.oauth2 as oauth2

import dbFunctions as fn
from oloFunctions import *

import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import RPi.GPIO as gpio

import sh
sh.init()

############################### Initialize Global Variables ###############################
current_milli_time = lambda: int(round(time.time() * 1000))

# SPOTIFY AUTH
token = None
try:
    token = fn.refreshSpotifyAuthToken(spotifyUsername=sh.spotify_username, client_id=sh.spotify_client_id, client_secret=sh.spotify_client_secret, redirect_uri=sh.spotify_redirect_uri, scope=sh.spotify_scope)
except:
    token = fn.getSpotifyAuthToken(spotifyUsername=sh.spotify_username, scope=sh.spotify_scope, client_id=sh.spotify_client_id, client_secret=sh.spotify_client_secret, redirect_uri=sh.spotify_redirect_uri)
sp = spotipy.Spotify(auth=token)

# DB connection
conn = fn.getDBConn(sh.dbname)
cur = conn.cursor()

# Constants
TOTALCOUNT = fn.getTotalCount(cur);
BUCKETSIZE = 16
SLIDEROFFSET = 15
TOTALBUCKETS = int(1024/BUCKETSIZE);
LIFEWINDOWSIZE = fn.getLifeWindowSize(cur);
BASELIFEOFFSET = fn.getBaseTimestamp(cur); # smallest timestamp in DB; the timestamp of the first music listening entry
BUCKETWIDTH_DAY = 1350 # 86400/64
BUCKETWIDTH_YEAR = 492750 # (86400*365)/64
BUCKETWIDTH_LIFE = int(math.ceil(LIFEWINDOWSIZE/64))
RETRY_MAX = 3;

# Status Variables
currSliderPos = 0
startTime = 0
currSongTime = 0
currSongTimestamp = 0
currVolume = None # [0, 100]
currBucket = 0 # [0, 63]
currMode = "" # ('life, 'year', 'day')
isPlaying = False
isOn = False
isMoving = False
retry = 0
bucketWidth = 0
bucketCounter = []
songsInABucket = 0;
refVolume = 0
fadingOut = False

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
# create the cs (chip select)
if (sh.CS is 8):
    cs = digitalio.DigitalInOut(board.D8)
else:
    cs = digitalio.DigitalInOut(board.D5)
# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# GPIO configuration:
gpio.setmode(gpio.BCM)

gpio.setup(sh.onoff, gpio.IN, pull_up_down=gpio.PUD_DOWN) # pin 17 - on/off switch

gpio.setup(sh.mEnable, gpio.OUT) # pin 6  - motor driver enable
gpio.setup(sh.mLeft, gpio.OUT) # pin 13 - motor driver direction 1
gpio.setup(sh.mRight, gpio.OUT) # pin 12 - motor driver direction 2

gpio.setup(sh.switch1, gpio.IN) # pin 16  - three pole switch 1
gpio.setup(sh.switch2, gpio.IN) # pin 18  - three pole switch 2

gpio.output(sh.mEnable, True) # Enable motor driver

# turn off other outputs:
gpio.output(sh.mLeft, False)
gpio.output(sh.mRight, False)

############################### Helper Functions ###############################
def fadeout():
    global currVolume, fadingOut, refVolume
    refVolume = currVolume
    while (fadingOut is False and refVolume > 0):
        fadingOut = True;
        refVolume = int(refVolume/1.5)
        sp.volume(refVolume, device_id = device_oloradio1)

# returns the start time and the current song's playtime in ms
def playSongInBucket(offset):
    global currBucket, currMode, currSliderPos, bucketWidth, bucketCounter, currVolume, songsInABucket
    global currSongTimestamp, startTime, currSongTime

    song = fn.getTrackFromBucket(cur, currMode, offset+(currBucket*bucketWidth), bucketCounter[currBucket])
    songURI = song[9]
    res = sp.track(songURI)

    currSongTimestamp = song[0]
    startTime = current_milli_time()
    currSongTime = int(res['duration_ms'])

    sp.start_playback(device_id = sh.device_oloradio1, uris = [songURI])
    print("## Playing a song... volume: {}".format(str(currVolume)))
    sp.volume(int(currVolume), device_id=sh.device_oloradio1)
    print("## now playing: {} - {} ({}), at Bucket [{}]({} in {}~{}): {}".format(song[2], song[1], songURI, str(currBucket), str(currSliderPos), str(16*currBucket), str(16*(currBucket+1)-1), str(bucketCounter[currBucket])))

    bucketCounter[currBucket] += 1;
    fn.updateBucketCounters(cur, currBucket, bucketCounter[currBucket], currMode, conn=conn);

# Move the slider to the next non-empty buckets, updates currBucket, currSliderPos and songsInABucket
def gotoNextNonEmptyBucket(offset, reachedTheEnd=None, sPos=None):
    global bucketCounter, currMode, currBucket, currSliderPos, bucketWidth, songsInABucket
    reachedTheEnd = False
    sPos = None

    print("@@ Bucket[{}]: {} out of {} songs".format(str(currBucket), str(bucketCounter[currBucket]), str(songsInABucket)))


    # if a bucket is not empty, play the bucket
    if (songsInABucket is not 0 and bucketCounter[currBucket] <= songsInABucket):
        # empty if a bucket is full
        if (bucketCounter[currBucket] == songsInABucket):
            fn.updateBucketCounters(cur, currBucket, 0, currMode, conn=conn);
    # skip empty buckets
    else:
        # empty overflowing buckets
        if (bucketCounter[currBucket] > songsInABucket):
            fn.updateBucketCounters(cur, currBucket, 0, currMode, conn=conn);
        print("@@@@ Skipping a bucket!!")
        currBucket += 1;
        # simulate the behavior where the search hits to the end and goes back to the beginning
        if (currBucket == 64):
            reachedTheEnd = True
            sPos = currSliderPos
        currBucket = currBucket % 64;
        currSliderPos = (currBucket*BUCKETSIZE) + SLIDEROFFSET
        songsInABucket = fn.getBucketCount(cur, currMode, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth)


        reachedTheEnd, sPos = gotoNextNonEmptyBucket(offset, reachedTheEnd, sPos)


    print("@@ Bucket[{}]: playing a song at {}. ({} ~ {}, offset: {})".format(str(currBucket), bucketCounter[currBucket], offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth, offset))
    if (reachedTheEnd and sPos is not None and sPos > 1010):
        moveslider(1022)
    moveslider(currSliderPos)

    if (reachedTheEnd is True):
        return reachedTheEnd, sPos

    return reachedTheEnd, sPos;


def checkValues():
    print("##### total songs: {}".format(TOTALCOUNT))
    print("##### Life mode base value: {}".format(BASELIFEOFFSET))
    pause = False;

    global isOn, isMoving, isPlaying
    global currVolume, currSliderPos, currBucket, currSongTime, startTime, currMode, currSongTimestamp
    global bucketWidth, bucketCounter, songsInABucket
    global conn, cur

    while (True):
        ### read values
        readValues();
        timeframe();
        pin_Volume = sh.values[4];
        pin_Touch = sh.values[6]
        pin_SliderPos = sh.values[7];
        pin_Mode = sh.timeframe
        isOn = gpio.input(sh.onoff)


        # Set initial offset and bucket width
        # *** Offset is the life timestamp of the earliest entry in the entire listing history
        offset = BASELIFEOFFSET
        bucketWidth = BUCKETWIDTH_LIFE
        if (pin_Mode is 'day'):
            offset = 0;
            bucketWidth = BUCKETWIDTH_DAY
        elif (pin_Mode is 'year'):
            offset = 0;
            bucketWidth = BUCKETWIDTH_YEAR

        # load bucket counters
        bucketCounter = fn.getBucketCounters(cur, pin_Mode)

        # Initialize volume
        if (currVolume is None):
            currVolume = int(pin_Volume/10);

        # OLO is OFF
        if (not isOn):
            isPlaying = False
            sp.pause_playback(device_id = sh.device_oloradio1)

        # OLO is ON
        else:
            # OLO is on but the music is not playing (either OLO is just turned on or a song has just finished)
            if (not isPlaying):
                print("@@ ON but not PLAYING!, Slider @ {}".format(pin_SliderPos))
                currSliderPos = pin_SliderPos
                currMode = pin_Mode;
                # set the position
                currBucket = int(math.floor(currSliderPos/16))
                songsInABucket = fn.getBucketCount(cur, currMode, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth)
                if (bucketCounter[currBucket] == songsInABucket):
                    # empty a full bucket and proceed to the next bucket
                    fn.updateBucketCounters(cur, currBucket, 0, currMode, conn=conn);
                    currBucket += 1
                gotoNextNonEmptyBucket(offset)
                print("@@ Next song @ Bucket[{}]: {} out of {} songs".format(str(currBucket), str(bucketCounter[currBucket]), str(songsInABucket)))
                print("@@ mode: {}, volume: {}, bucketWidth: {}".format(pin_Mode, str(currVolume), bucketWidth))
                print("@@ B[{}]: {} (offset: {} ~ {})".format(str(currBucket), bucketCounter[currBucket], offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth))
                playSongInBucket(offset)
                isPlaying = True

            # Volume change
            vol = int(pin_Volume/10)
            if (abs(currVolume - vol) > 2):
                print("@@ Volume change! {} -> {}".format(currVolume, vol))
                currVolume = vol
                if (currVolume > 100):
                    currVolume = 100;
                sp.volume(int(currVolume), device_id=sh.device_oloradio1)

            # Slider is moved - capacitive touch
            if (not isMoving and pin_Touch > 100):
                print("@@ Slider touched..! Moving...")
                isMoving = True


#            if (isMoving and pin_SliderPos is not 0):
#                print("@@ Slider: {} -> {}".format(currSliderPos, pin_SliderPos))

            # fade out when switching songs
            if (isMoving and abs(pin_SliderPos - currSliderPos) > 5):
                fadeout();

            # Slider is released
            if (isMoving and pin_Touch < 100):
                currSliderPos = pin_SliderPos
                # set the position
                newBucket = int(math.floor(currSliderPos/16))
                # do not skip the song if the slider is touched but not moved
                if (currBucket != newBucket):
                    currBucket = newBucket
                    songsInABucket = fn.getBucketCount(cur, currMode, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth)
                    gotoNextNonEmptyBucket(offset)
                    print("@@ Now playing song @ Bucket[{}]: {} out of {} songs".format(str(currBucket), str(bucketCounter[currBucket]), str(songsInABucket)))
                    print("@@ mode: {}, volume: {}, bucketWidth: {}".format(pin_Mode, str(currVolume), bucketWidth))
                    print("@@ B[{}]: {} (offset: {} ~ {})".format(str(currBucket), bucketCounter[currBucket], offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth))
                    playSongInBucket(offset)


                isMoving = False

            # Mode change
            # * do not move slider when touched
            if (not isMoving and currMode != pin_Mode):
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
                bucketCounter = fn.getBucketCounters(cur, pin_Mode)

                # get the new index based on the mode
                indices = fn.findTrackIndex(cur, currMode, currSongTimestamp) # (INDEX, year, month, timeofday, month_offset, day_offset)
                if (currMode is 'day'):
                    index = indices[5]
                elif (currMode is 'year'):
                    index = indices[4]
                else:
                    index = currSongTimestamp - offset

                generalIndex = int(indices[0])-1 # index is 1 less than the order number
                currBucket = int(math.floor(index/bucketWidth))
                songsInABucket = fn.getBucketCount(cur, currMode, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth)
                print("@@ new index: {} / {} in {} mode,, playing {} out of {} songs".format(str(generalIndex), str(TOTALCOUNT), currMode, str(bucketCounter[currBucket]), str(songsInABucket)))

                currSliderPos = (currBucket*BUCKETSIZE) + SLIDEROFFSET
                moveslider(currSliderPos)

            # a song has ended
            if (isPlaying and (current_milli_time() - startTime) > currSongTime):
                print("@@ The song has ended!")
                isPlaying = False;
                currSongTime = sys.maxsize

def stop():
    sys.exit()

# -------------------------
def main():
    global retry
    while True:
        try:
            print("### Main is starting..")
            checkValues()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            print(traceback.format_exc())
            print("!! Sleeping for 5 seconds,, Retry: {}".format(retry))
            print("@@ acquiring new token,,")
            try:
                token = fn.refreshSpotifyAuthTOken(spotifyUsername=sh.spotify_username, client_id=sh.spotify_client_id, client_secret=sh.spotify_client_secret, redirect_uri=sh.spotify_redirect_uri, scope=sh.spotify_scope)
                sp = spotipy.Spotify(auth=token)
            except:
                print("@@@ Try restarting Raspotify,,");
                # restart raspotify just in case
                os.system("sudo systemctl restart raspotify")

                retry += 1;
                if (retry >= RETRY_MAX):
                    print("@@@@ Couldn't refresh token.. :()")
                    # restart the program
                    python = sys.executable
                    os.execl(python, python, * sys.argv)
                continue;

            isPlaying = False;
            isMoving = False;
            time.sleep(5)
            continue;

if __name__ == "__main__": main()

#-*-coding:utf-8-*-

### TODO:

#   ** Use Linux Process Monitor (https://gist.github.com/connorjan/01f995511cfd0fee1cfae2387024b54a)

#   - fade-in/fade-out when turning on & switching musics

#   - workaround without capacitive touch

#   - run the main script on boot
#   - run update script once a day

#   - *** headless start to connect to wifi >> Making RPI as an Access Point ???


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
# TODO: have separate bucket counters for each mode
bucketCounter = fn.getBucketCounters(cur)

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
gpio.setup(sh.mEnable, gpio.OUT) #gpio 6  - motor driver enable
gpio.setup(sh.mLeft, gpio.OUT) #gpio 13 - motor driver direction 1
gpio.setup(sh.mRight, gpio.OUT) #gpio 12 - motor driver direction 2

gpio.setup(sh.switch1, gpio.IN) #gpio 16  - three pole switch 1
gpio.setup(sh.switch2, gpio.IN) #gpio 18  - three pole switch 2

gpio.output(sh.mEnable, True) # Enable motor driver

# turn off other outputs:
gpio.output(sh.mLeft, False)
gpio.output(sh.mRight, False)

############################### Helper Functions ###############################
# returns the start time and the current song's playtime in ms
def playSongInBucket(songsInABucket, offset):
    global currBucket, currMode, currSliderPos, bucketWidth, bucketCounter, currVolume
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
    print("## now playing: {} - {} ({}), at Bucket [{}]({}): {}".format(song[2], song[1], songURI, str(currBucket), str(currSliderPos), str(bucketCounter[currBucket])))


# Move the slider to the next non-empty buckets, returns the total number of songs in the new bucket
def gotoNextNonEmptyBucket(songsInABucket, offset):
    global bucketCounter, currMode, currBucket, currSliderPos, bucketWidth

    reachedTheEnd = False;
    sPos = None;
    # there is no song in a bucket
    while (bucketCounter[currBucket] >= songsInABucket):
        # reset the current counter and proceed to the next bucket
        print("@@@@ Skipping a bucket!!")
        fn.updateBucketCounters(cur, currBucket, 0, conn=conn)
        currBucket += 1
        # simulate the behavior where the search hits to the end and goes back to the beginning
        if (currBucket == 64):
            reachedTheEnd = True
            sPos = currSliderPos
        currBucket = currBucket % 64;
        currSliderPos = (currBucket*BUCKETSIZE) + SLIDEROFFSET
        songsInABucket = fn.getBucketCount(cur, currMode, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth)
        print("@@ Bucket[{}]: {} out of {} songs".format(str(currBucket), str(bucketCounter[currBucket]), str(songsInABucket)))
    print("@@ B[{}]: {} ({} ~ {}, offset: {})".format(str(currBucket), bucketCounter[currBucket], offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth, offset))
    if (reachedTheEnd and sPos is not None and sPos > 1010):
        moveslider(1022)
    moveslider(currSliderPos)

    return songsInABucket

# def checkValues(isOn, isMoving, isPlaying, currVolume, currSliderPos, currBucket, currSongTime, startTime, currMode, currSongTimestamp):
def checkValues():
    print("##### total songs: {}".format(TOTALCOUNT))
    print("##### Life mode base value: {}".format(BASELIFEOFFSET))
    pause = False;

    global isOn, isMoving, isPlaying
    global currVolume, currSliderPos, currBucket, currSongTime, startTime, currMode, currSongTimestamp
    global bucketWidth, bucketCounter
    global conn, cur

    while (True):
        ### read values
        readValues();
        timeframe();
        pin_Volume = sh.values[4];
        pin_Touch = sh.values[6]
        pin_SliderPos = sh.values[7];
        pin_Mode = sh.timeframe

        ## TODO: pause the loop when volume is 0

        offset = BASELIFEOFFSET
        bucketWidth = BUCKETWIDTH_LIFE
        if (pin_Mode is 'day'):
            offset = 0;
            if (TOTALCOUNT > BUCKETWIDTH_DAY):
                bucketWidth = BUCKETWIDTH_DAY
        elif (pin_Mode is 'year'):
            offset = 0;
            if (TOTALCOUNT > BUCKETWIDTH_YEAR):
                bucketWidth = BUCKETWIDTH_YEAR

        if (currVolume is None):
            currVolume = int(pin_Volume/10);

        # TODO: get the OFF signal from PIN 17
        # Turn OLO off
        # if (not isOn and pin_Volume is 0):
        #     isOn = False;


        # Turn OLO on
        if (not isOn and pin_Volume > 0):
        #            print("@@ Turning ON!")
            isOn = True
            isPlaying = False
            currMode = pin_Mode;

        # TODO: when volume is 0, just set volume to 0
        if (isOn and pin_Volume is 0):
            isOn = False
            isPlaying = False
            # pause the song that was currently playing
            sp.pause_playback(device_id=sh.device_oloradio1);


        # OLO is on but the music is not playing (either OLO is just turned on or a song has just finished)
        if (isOn and not isPlaying):
            print("@@ ON but not PLAYING!, Slider @ {}".format(pin_SliderPos))
            currSliderPos = pin_SliderPos
            currMode = pin_Mode;
            # set the position
            currBucket = int(math.floor(currSliderPos/16))
            songsInABucket = fn.getBucketCount(cur, currMode, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth)

            print("@@ Next song @ Bucket[{}]: {} out of {} songs".format(str(currBucket), str(bucketCounter[currBucket]), str(songsInABucket)))
            print("@@ mode: {}, volume: {}, bucketWidth: {}".format(pin_Mode, str(currVolume), bucketWidth))
            print("@@ B[{}]: {} (offset: {} ~ {})".format(str(currBucket), bucketCounter[currBucket], offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth))

            songsInABucket = gotoNextNonEmptyBucket(songsInABucket, offset)
            playSongInBucket(songsInABucket, offset)
            bucketCounter[currBucket] =+ 1;
            fn.updateBucketCounters(cur, currBucket, bucketCounter[currBucket], conn=conn);
            isPlaying = True


        # Volume change
        if (isOn and pin_Volume > 0):
            vol = int(pin_Volume/10)
            if (abs(currVolume - vol) > 2):
                print("@@ Volume change! {} -> {}".format(currVolume, vol))
                currVolume = vol
                if (currVolume > 100):
                    currVolume = 100;
                sp.volume(int(currVolume), device_id=sh.device_oloradio1)

        # Slider Moved - capacitive touch
        if (isOn and not isMoving and pin_Touch > 100):
            print("@@ Slider touched..! Moving...")
            isMoving = True
        if (isOn and isMoving and pin_Touch < 100):
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

                songsInABucket = gotoNextNonEmptyBucket(songsInABucket, offset)
                playSongInBucket(songsInABucket, offset)
                bucketCounter[currBucket] =+ 1;
                fn.updateBucketCounters(cur, currBucket, bucketCounter[currBucket], conn=conn);
                
            isMoving = False


        # Mode Change
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
        if (isOn and isPlaying and (current_milli_time() - startTime) > currSongTime):
            print("@@ The song has ended!")
            isPlaying = False;
            currSongTime = sys.maxsize


# -------------------------
def main():
    global retry
    while True:
        try:
            print("### Main is starting..")
#            checkValues(isOn, isMoving, isPlaying, currVolume, currSliderPos, currBucket, currSongTime, startTime, currMode, currSongTimestamp)
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

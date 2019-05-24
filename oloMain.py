#-*-coding:utf-8-*-

### TODO:
#   - *** headless start: edit wpa_supplicant.conf

## BUGS AND IMPROVEMENTS:
#   - mode change to life when touched results in an infinite loop
#   - volume is not linearly increasing

import os, traceback, math, sys, time, datetime, logging
import queue
from statistics import mean

import spotipy
import spotipy.util as util
import spotipy.oauth2 as oauth2

import dbFunctions as fn
from oloFunctions import *

import busio, digitalio, board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import RPi.GPIO as gpio

import sh
sh.init()

################## Create Logger ##################
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger("Main Log")
logger.setLevel(logging.INFO)

if os.name == 'nt':
    log_file = "C:\tmp\main.log"
else:
    log_file = "/home/pi/Desktop/olo/log_main/main.log"
    directory = "/home/pi/Desktop/olo/log_main/"
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

open(log_file, 'a')

handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1)
logger.addHandler(handler)
###################################################


################################### Auxiliary Functions ###################################
current_milli_time = lambda: int(round(time.time() * 1000))
timenow = lambda: str(datetime.datetime.now()).split('.')[0]

############################### Initialize Global Variables ###############################
# SPOTIFY AUTH
token = None
sp = None
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
RETRY_MAX = 1;

# Status Variables
stablizeSliderPos = queue.Queue(maxsize=10) # average out 10 values - long window
stablizePinSliderPos = queue.Queue(maxsize=3) # average out 3 values - short window
currSliderPos = 0
currVolume = None # [0, 100]
currBucket = 0 # [0, 63]
currMode = None # ('life, 'year', 'day')
retry = 0
bucketWidth = 0
bucketCounter = []
songsInABucket = 0;
refVolume = 0
refBucket = None
refSliderPos = -1
refMode = None

# Timers
startTime = 0
currSongTime = 0
currSongTimestamp = 0
moveTimer = None;
changeModeTimer = None;

# Status Flags
isPlaying = False
isOn = False
isMoving = False
fadeoutFlag = False
switchSongFlag = False
pauseWhenOffFlag = False
changeModeFlag = False
skipBucketFlag = False

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
def formatMs(ms):
    sec = ms // 1000
    m = sec // 60
    s = sec % 60
    return str(m) + ":" + str(s)

def fadeout():
    global sp, currVolume, fadeoutFlag, refVolume
    refVolume = currVolume
    while (refVolume > 0):
        refVolume = int(refVolume/1.5)
        sp.volume(refVolume, device_id = sh.device_oloradio1)
    fadeoutFlag = False

# returns the start time and the current song's playtime in ms
def playSongInBucket(offset):
    global sp, currBucket, currMode, currSliderPos, bucketWidth, bucketCounter, currVolume, songsInABucket
    global currSongTimestamp, startTime, currSongTime, isPlaying

    song = fn.getTrackFromBucket(cur, currMode, offset+(currBucket*bucketWidth), bucketCounter[currBucket])
    songURI = song[9]
    res = sp.track(songURI)

    currSongTimestamp = song[0]
    currSongTime = int(res['duration_ms'])

    sp.start_playback(device_id = sh.device_oloradio1, uris = [songURI])
    sp.volume(int(currVolume), device_id=sh.device_oloradio1)
    bucketCounter[currBucket] += 1;
    fn.updateBucketCounters(cur, currBucket, bucketCounter[currBucket], currMode, conn=conn);
    isPlaying = True
    startTime = current_milli_time()

    print("[{}]: ######################################################################################################".format(timenow()))
    print("[{}]: ## Now playing: {} - {} ({})".format(timenow(), song[2], song[1], formatMs(currSongTime)))
    print("[{}]: ##    @ Bucket[{}]: {} out of {} songs".format(timenow(), currBucket, bucketCounter[currBucket], songsInABucket))
    print("[{}]: ##        Slider is at {} in [{} ~ {}] (BucketWidth: {}, Offset: {} ~ {})".format(timenow(), currSliderPos, 16*currBucket, 16*(currBucket+1)-1, bucketWidth, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth))
    print("[{}]: ##        Mode: {}, Volume: {}".format(timenow(), currMode, currVolume))
    print("[{}]: ######################################################################################################".format(timenow()))
    logger.info("[{}]: ######################################################################################################".format(timenow()))
    logger.info("[{}]: ## Now playing: {} - {} ({})".format(timenow(), song[2], song[1], formatMs(currSongTime)))
    logger.info("[{}]: ##    @ Bucket[{}]: {} out of {} songs".format(timenow(), currBucket, bucketCounter[currBucket], songsInABucket))
    logger.info("[{}]: ##        Slider is at {} in [{} ~ {}] (BucketWidth: {}, Offset: {} ~ {})".format(timenow(), currSliderPos, 16*currBucket, 16*(currBucket+1)-1, bucketWidth, offset + currBucket*bucketWidth, offset + (currBucket+1)*bucketWidth))
    logger.info("[{}]: ##        Mode: {}, Volume: {}".format(timenow(), currMode, currVolume))
    logger.info("[{}]: ######################################################################################################".format(timenow()))

# Move the slider to the next non-empty buckets, updates currBucket, currSliderPos and songsInABucket
def gotoNextNonEmptyBucket(offset):
    global bucketCounter, currMode, currBucket, currSliderPos, bucketWidth, songsInABucket, isMoving, moveTimer, skipBucketFlag
    blockedSliderFlag = False;

    bucketCounter = fn.getBucketCounters(cur, currMode)
    print("[{}]: @@   Scanning bucket[{}]: {} out of {} songs".format(timenow(), currBucket, bucketCounter[currBucket], songsInABucket))
    logger.info("[{}]: @@   Scanning bucket[{}]: {} out of {} songs".format(timenow(), currBucket, bucketCounter[currBucket], songsInABucket))

    tmpBucket = int(math.floor(currSliderPos/16))
    tmpSongsInABucket = fn.getBucketCount(cur, currMode, offset + tmpBucket*bucketWidth, offset + (tmpBucket+1)*bucketWidth)
    tmpSliderPos = None;

    # placeholder for previous values for recovery when stuck
    prevBucket = tmpBucket
    prevSliderPos = currSliderPos
    prevSongsInABucket = tmpSongsInABucket

    stuckPosBucket = None
    stuckSliderPos = None

    # iterate to find non-empty bucket while skipping empty buckets
    while (tmpSongsInABucket is 0 or bucketCounter[tmpBucket] > tmpSongsInABucket):
        # empty overflowing buckets
        if (bucketCounter[tmpBucket] > tmpSongsInABucket):
            fn.updateBucketCounters(cur, tmpBucket, 0, currMode, conn=conn);

        print("[{}]: @@     Skipping bucket[{}]!!".format(timenow(), tmpBucket))
        logger.info("[{}]: @@     Skipping bucket[{}]!!".format(timenow(), tmpBucket))

        tmpBucket += 1;
        tmpBucket = tmpBucket % 64;
        tmpSliderPos = (tmpBucket*BUCKETSIZE) + SLIDEROFFSET
        tmpSongsInABucket = fn.getBucketCount(cur, currMode, offset + tmpBucket*bucketWidth, offset + (tmpBucket+1)*bucketWidth)

    # if a bucket is not empty, play the bucket
    if (bucketCounter[tmpBucket] == tmpSongsInABucket):
        fn.updateBucketCounters(cur, tmpBucket, 0, currMode, conn=conn);

    if (tmpBucket != currBucket and tmpSliderPos is not None):
        isMoving = True
        skipBucketFlag = True
        moveTimer = current_milli_time()
        res = moveslider(tmpSliderPos)
        if (res < 0):
            # read raw pin value at the stuck position
            stuckSliderPos = sh.values[7]
            stuckPosBucket = int(math.floor(stuckSliderPos/16))
            stuckSongsInABucket = fn.getBucketCount(cur, currMode, offset + stuckPosBucket*bucketWidth, offset + (stuckPosBucket+1)*bucketWidth)

            print("@@ Slider got stuck at @{} (B[{}] has {} songs)!!".format(stuckSliderPos, stuckPosBucket, stuckSongsInABucket))

            # if the slider is stuck at a non-empty bucket, play that bucket
            if (stuckSongsInABucket > 0):
                print("@@@@ stuck at a NON-EMPTY bucket; just play this bucket,,")
                tmpBucket = stuckPosBucket
                songsInABucket = stuckSongsInABucket
            # if the slider is stuck at an empty bucket, recover to the previous position
            else:
                print("@@@@ stuck at an EMPTY bucket..!! recovering the position...")
                tmpbucket = prevBucket
                songsInABucket = prevSongsInABucket
                blockedSliderFlag = True

    currBucket = tmpBucket
    songsInABucket = tmpSongsInABucket

    # go back to the original non-empty bucket
    if (blockedSliderFlag):
        blockedSliderFlag = False
        moveslider(prevSliderPos)


def checkValues():
    print("[{}]: ##### total songs: {}".format(timenow(), TOTALCOUNT))
    print("[{}]: ##### Life mode base value: {}".format(timenow(), BASELIFEOFFSET))
    logger.info("[{}]: ##### total songs: {}".format(timenow(), TOTALCOUNT))
    logger.info("[{}]: ##### Life mode base value: {}".format(timenow(), BASELIFEOFFSET))

    global isOn, isMoving, isPlaying, fadeoutFlag, moveTimer, switchSongFlag, pauseWhenOffFlag, changeModeFlag, changeModeTimer, skipBucketFlag
    global currVolume, currSliderPos, currBucket, currSongTime, startTime, currMode, currSongTimestamp
    global bucketWidth, bucketCounter, songsInABucket, stablizeSliderPos, stablizePinSliderPos, refBucket, refSliderPos, refMode
    global conn, cur, sp

    if (conn is None):
        conn = fn.getDBConn(sh.dbname)
    if (cur is None):
        cur = conn.cursor()

    while (True):
        ### read values
        readValues();
        timeframe();

        pin_Volume = sh.values[4];
        pin_Touch = sh.values[6]
        pin_Mode = sh.timeframe
        pin_SliderPos = sh.values[7]
        isOn = gpio.input(sh.onoff)

        # average values to get stablized slider position
        if (pin_Touch < 100):
            # long window
            if (stablizeSliderPos.full()):
                stablizeSliderPos.get()
            stablizeSliderPos.put(pin_SliderPos)
            avgPos = int(mean(list(stablizeSliderPos.queue)))

            # short window
            if (stablizePinSliderPos.full()):
                stablizePinSliderPos.get()
            stablizePinSliderPos.put(pin_SliderPos)
            avgPinPos = int(mean(list(stablizePinSliderPos.queue)))

        currSliderPos = avgPos;
        currBucket = int(math.floor(currSliderPos/16))

        if (refSliderPos < 0):
            refSliderPos = currSliderPos

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

        if (pin_Touch < 100):
            tmpSliderPos = avgPinPos
            tmpBucket = int(math.floor(tmpSliderPos/16))
            tmpVolume = int(pin_Volume/10)


        # OLO is OFF
        if (not isOn):
            isPlaying = False

            # gently turn off
            if (currVolume > 0):
                fadeoutFlag = True
            if (fadeoutFlag):
                fadeout()

            if (pauseWhenOffFlag):
                sp.pause_playback(device_id = sh.device_oloradio1)
                pauseWhenOffFlag = False

        # OLO is ON
        else:
            if (pauseWhenOffFlag is False):
                pauseWhenOffFlag = True

            if (currMode is None):
                currMode = pin_Mode

            if (isMoving):
                if (abs(refSliderPos - tmpSliderPos) > 12 and refBucket != tmpBucket):
                    print("[{}]: @@       Keep moving.. reset moveTimer: currPos: {}, tmpPos: {}".format(timenow(), currSliderPos, tmpSliderPos))
                    logger.info("[{}]: @@       Keep moving.. reset moveTimer: currPos: {}, tmpPos: {}".format(timenow(), currSliderPos, tmpSliderPos))
                    moveTimer = current_milli_time()
                    refBucket = tmpBucket;
                    refSliderPos = tmpSliderPos;
                # the slider is stopped at a fixed position for more than a second
                if (abs(refSliderPos - tmpSliderPos) < 12 and refBucket == tmpBucket and (current_milli_time() - moveTimer) > 1000):
                        print("[{}]: @@ Movement stopped!".format(timenow()))
                        logger.info("[{}]: @@ Movement stopped!".format(timenow()))
                        isMoving = False

                        if (not changeModeFlag):
                            switchSongFlag = True
                        else:
                            changeModeFlag = False
                            changeModeTimer = None

                        if (skipBucketFlag):
                            skipBucketFlag = False

                        moveTimer = None
                        refBucket = currBucket
                        refSliderPos = currSliderPos
                        currBucket = tmpBucket
                        print("[{}]: @@ Slider stopped at {} in bucket {}, currSliderPos: {}, refPos: {}".format(timenow(), pin_SliderPos, tmpBucket, currSliderPos, refSliderPos))
                        logger.info("[{}]: @@ Slider stopped at {} in bucket {}, currSliderPos: {}, refPos: {}".format(timenow(), pin_SliderPos, tmpBucket, currSliderPos, refSliderPos))


            # OLO is on but the music is not playing (either OLO is just turned on or a song has just finished)
            if (not isPlaying):

                currMode = pin_Mode;
                gotoNextNonEmptyBucket(offset)

                # do not start playing while skipping buckets
                if (not skipBucketFlag):
                    playSongInBucket(offset)
                    switchSongFlag = False

            # OLO is playing a song
            else:

                # Observe if the slider is moved. Must satisfy BOTH conditions to be considered as "moved".
                # The slider is..
                #       i) moved more than the threshold of 12
                #           AND
                #       ii) moved to a different bucket
                if (not isMoving and abs(currSliderPos - tmpSliderPos) > 12 and currBucket != tmpBucket):
                    print("[{}]: @@ Movement detected: currPos: {}, tmpPos: {}".format(timenow(), currSliderPos, tmpSliderPos))
                    logger.info("[{}]: @@ Movement detected: currPos: {}, tmpPos: {}".format(timenow(), currSliderPos, tmpSliderPos))

                    isMoving = True
                    refBucket = currBucket
                    refSliderPos = currSliderPos
                    if (moveTimer is None):
                        print("[{}]: @@@@ Setting a moveTimer".format(timenow()))
                        logger.info("[{}]: @@@@ Setting a moveTimer".format(timenow()))
                        moveTimer = current_milli_time()
                        if (not changeModeFlag):
                            fadeoutFlag = True
                    if (fadeoutFlag):
                        print("[{}]: @@@@    fading out...".format(timenow()))
                        logger.info("[{}]: @@@@    fading out...".format(timenow()))
                        fadeout();

                # Slider is not moving or finished moving
                if (not isMoving):

                    # Volume change
                    if (abs(currVolume - tmpVolume) > 2):
                        print("[{}]: @@ Volume change! {} -> {}".format(timenow(), currVolume, tmpVolume))
                        logger.info("[{}]: @@ Volume change! {} -> {}".format(timenow(), currVolume, tmpVolume))
                        currVolume = tmpVolume
                        if (currVolume > 100):
                            currVolume = 100;
                        sp.volume(int(currVolume), device_id=sh.device_oloradio1)

                    if (switchSongFlag):
                        currMode = pin_Mode     # silently update the mode when changed while moving
                        gotoNextNonEmptyBucket(offset)
                        # do not start playing while skipping buckets
                        if (not skipBucketFlag):
                            playSongInBucket(offset)
                            switchSongFlag = False

                    # Mode change
                    # * do not change the mode when touched
                    if (pin_Touch < 100 and currMode != pin_Mode):
                        changeModeFlag = True
                        refMode = pin_Mode
                        if (changeModeTimer is None):
                            print('[{}]: @@@ Mode Changed detected {} -> {}. Setting the timer!'.format(timenow(), refMode, pin_Mode))
                            logger.info('[{}]: @@@ Mode Changed detected {} -> {}. Setting the timer!'.format(timenow(), refMode, pin_Mode))
                            changeModeTimer = current_milli_time()

                        if (pin_Mode == 'err'):
                            continue;

                    # detect mode change
                    if (pin_Mode is not None and refMode != pin_Mode):
                        print('[{}]: @@@ Another mode changed detected {} -> {}. Reset the timer!'.format(timenow(), refMode, pin_Mode))
                        logger.info('[{}]: @@@ Another mode changed detected {} -> {}. Reset the timer!'.format(timenow(), refMode, pin_Mode))
                        changeModeTimer = current_milli_time()
                        refMode = pin_Mode

                    # wait for 0.7s in case of rapid multiple mode changes
                    if (changeModeFlag and changeModeTimer is not None and (current_milli_time() - changeModeTimer > 700)):
                        print('[{}]: @@@ Mode Changed!! {} -> {} '.format(timenow(), currMode, pin_Mode))
                        logger.info('[{}]: @@@ Mode Changed!! {} -> {} '.format(timenow(), currMode, pin_Mode))

                        prevMode = currMode
                        currMode = pin_Mode
                        refMode = pin_Mode
                        # reset the bucketWidth
                        if (currMode is 'day'):
                            offset = 0;
                            bucketWidth = BUCKETWIDTH_DAY
                        elif (currMode is 'year'):
                            offset = 0;
                            bucketWidth = BUCKETWIDTH_YEAR
                        else:
                            offset = BASELIFEOFFSET
                            bucketWidth = BUCKETWIDTH_LIFE
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
                        currSliderPos = (currBucket*BUCKETSIZE) + SLIDEROFFSET
                        res = moveslider(currSliderPos)

                        # slider got stuck while changing mode
                        if (res < 0):
                            stuckSliderPos = sh.values[7]
                            stuckPosBucket = int(math.floor(stuckSliderPos/16))
                            stuckSongsInABucket = fn.getBucketCount(cur, currMode, offset + stuckPosBucket*bucketWidth, offset + (stuckPosBucket+1)*bucketWidth)

                            print("[{}]: WARNING!! Slider got stuck @{} while changing mode {} -> {}".format(timenow(), stuckSliderPos, prevMode, currMode))
                            logger.info("[{}]: WARNING!! Slider got stuck @{} while changing mode {} -> {}".format(timenow(), stuckSliderPos, prevMode, currMode))

                            # update bucket index and depth at the stuck position
                            currBucket = stuckPosBucket
                            songsInABucket = stuckSongsInABucket

                            print("[{}]: @@ Stuck at B[{}] in {} mode!! Playing {} out of {} songs".format(timenow(), stuckPosBucket, currMode, bucketCounter[currBucket], songsInABucket))
                            logger.info("[{}]: @@ Stuck at B[{}] in {} mode!! Playing {} out of {} songs".format(timenow(), stuckPosBucket, currMode, bucketCounter[currBucket], songsInABucket))

                        else:
                            print("[{}]: @@ New index: {} / {} in {} mode,, playing {} out of {} songs".format(timenow(), generalIndex, TOTALCOUNT, currMode, bucketCounter[currBucket], songsInABucket))
                            logger.info("[{}]: @@ New index: {} / {} in {} mode,, playing {} out of {} songs".format(timenow(), generalIndex, TOTALCOUNT, currMode, bucketCounter[currBucket], songsInABucket))


                    # a song has ended
                    # wait 2 seconds to compensate processing time
                    if ((current_milli_time() - startTime) > currSongTime + 2000):
                        print("[{}]: @@ The song has ended!".format(timenow()))
                        logger.info("[{}]: @@ The song has ended!".format(timenow()))
                        isPlaying = False;
                        currSongTime = sys.maxsize

def stop():
    sys.exit()

# -------------------------
def main():
    global retry, conn, cur, isPlaying, isMoving, sp
    while True:
        try:
            print("[{}]: ### Main is starting..".format(timenow()))
            logger.info("[{}]: ### Main is starting..".format(timenow()))
            checkValues()
        except (KeyboardInterrupt, SystemExit):
            hardstop()
            conn.close()
            raise
        except:
            print(traceback.format_exc())
            print("[{}]: !! Acquiring new token,,".format(timenow()))
            logger.info(traceback.format_exc())
            logger.info("[{}]: !! Acquiring new token,,".format(timenow()))
            try:
                token = fn.refreshSpotifyAuthTOken(spotifyUsername=sh.spotify_username, client_id=sh.spotify_client_id, client_secret=sh.spotify_client_secret, redirect_uri=sh.spotify_redirect_uri, scope=sh.spotify_scope)
                sp = spotipy.Spotify(auth=token)
            except:
                print("[{}]: !!   Try restarting Raspotify, Sleeping for 1 second..".format(timenow()));
                logger.info("[{}]: !!   Try restarting Raspotify, Sleeping for 1 second..".format(timenow()))
                # restart raspotify just in case
                os.system("sudo systemctl restart raspotify")
                time.sleep(1)

                retry += 1;
                if (retry >= RETRY_MAX):
                    print("[{}]: !!!!   Couldn't refresh token,, restarting the script..".format(timenow()))
                    logger.info("[{}]: !!!!   Couldn't refresh token,, restarting the script..".format(timenow()))
                    # restart the program
                    python = sys.executable
                    os.execl(python, python, * sys.argv)
                continue;
            conn.close()
            conn = None
            cur = None
            isPlaying = False;
            isMoving = False;

            print("[{}]: !! Sleeping for 3 seconds,, Retry: {}".format(timenow(), retry))
            logger.info("[{}]: !! Sleeping for 3 seconds,, Retry: {}".format(timenow(), retry))
            time.sleep(3)
            continue;

if __name__ == "__main__": main()

#-*-coding:utf-8-*-
import dbtest as fn
import spotipyTest
import oloFunctions
import sh

sh.init()

sliderOffset = 15
bucketSize = 16
dbpath = os.path.join(basepath, "./test.db")

token = fn.getSpotifyAuthToken()
sp = spotipy.Spotify(auth=token)

# TODO: save and load from a file
lastUpdatedDate

# STATUS VARIABLES
mode  # Mode: 0 - life, 1 - year, 2 - day
volume
currSliderPos

# currBucket
startTime
currSongTime
currSongTimestamp


loopCount = 0
loopPerBucket = 3

isPlaying = False
isOn = False

totalCount = fn.getTotalCount(cur);
songsInABucket = totalCount/bucketSize;

### TODO: enble pins

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

        ### events
        # - volume change
        if (volumeChange):
            fn.setVolume(pinVal/10)
        # - slider move
        if (isOn and sliderMoves):
            # set loopCount to 0
            loopCount = 0;
            # set the position
            currBucket = int(sliderPos / 1024)
            playSongInBucket(currBucket)

        # - mode change
        if (modeChange):
            mode = newMode
            index = (fn.findTrackIndex(cur, mode, currSongTimestamp)/songsInABucket)
            currSliderPos = index*bucketSize # + bucketSize/2

        # - volume 0
        if (isOn and volume_pin is 0):
            #TODO: check last update date, then update lastFM list once in a day
            continue;
        # - volume +
        elif (not isOn and volume_pin > 0):
            isOn = True

        # a song has ended
        if (time.time() - startTime > currSongTime):
            res = sp.current_playback()
            if (res['is_playing'] is False):
                # - loop
                if (loopCount < loopPerBucket):
                    loopCount++;
                    playSongInBucket(currBucket)
                # - song end -> next
                # error margin: 6, bucket size is 16; 64 buckets, but trim accordingly on both ends
                else:
                    loopCount = 0
                    # - go back to the beginning when slider hits the end
                    currSliderPos = (currSliderPos + sliderOffset) % 1024


# -------------------------

try:
    checkValues()
except:
    print("Unexpected error:", sys.exc_info()[0])
    raise

#!/usr/bin/env python3
### THIS FILE MUST BE RUN WITH PYTHON 3.
### RUNNING WITH PYTHON 2 WILL CAUSE AN ERROR.

#-*-coding:utf-8-*-

import os.path, time, urllib, json, pprint, datetime
import sh
sh.init()

import pylast

import sqlite3

import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util


## for the testing purpose, mock all datas to speed up the process!
TESTING = False
DEBUGGING = False

token = None

timenow = lambda: str(datetime.datetime.now()).split('.')[0]

############################################################
##                                                        ##
##         FUNCTIONS OVER API (LastFM & Spotipy)          ##
##                                                        ##
############################################################

def getSpotifyAuthToken(spotifyUsername, scope, client_id, client_secret, redirect_uri):
    token = util.prompt_for_user_token(username=spotifyUsername, scope=scope, client_id = client_id, client_secret = client_secret, redirect_uri = redirect_uri)
    return token

# returns a fresh token
def refreshSpotifyAuthToken(spotifyUsername, client_id, client_secret, redirect_uri, scope):
    cache_path = ".cache-" + spotifyUsername
    sp_oauth = oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope, cache_path=cache_path)
    token_info = sp_oauth.get_cached_token()
    token = token_info['access_token']
    return token;

def buildSearchQuery(title, artist, album=None):
    if (album is None):
        return '''"{}" artist:{}'''.format(title, artist)
    else:
        return '''"{}" artist:{} album:{}'''.format(title, artist, album)

def jsonToDict(filename):
   with open(filename, encoding='utf-8') as f_in:
       return(json.load(f_in))

def getLastFmHistroy(username, limit = None):
    conn_pylast = pylast.LastFMNetwork(api_key=sh.PYLAST_API_KEY, username=username)
    user = conn_pylast.get_user(username)
    tracks = user.get_recent_tracks(limit = limit)
    res = list()
    for track in tracks:
        res.append([track.timestamp, track[0].artist.name, track[0].title, track.album]);
    return res;

def setVolume(volume, device=None, sp=None):
    if (device is None):
        device = sh.device_oloradio1

    if (token is None):
        try:
            token = getSpotifyAuthToken(sh.spotify_username, sh.spotify_scope, sh.spotify_client_id, sh.spotify_client_secret, sh.spotify_redirect_uri)
        except:
            token = refreshSpotifyAuthToken(sh.spotify_username, sh.spotify_client_id, sh.spotify_client_secret, sh.spotify_redirect_uri, sh.spotify_scope)

    if (sp is None):
        sp = spotipy.Spotify(auth=token)
    sp.volume(volume, device_id=device)


############################################################
##                                                        ##
##                       DB HANDLING                      ##
##                                                        ##
############################################################

basepath = os.path.abspath(os.path.dirname(__file__))

def dbPath(dbName):
    dbfile = "./" + dbName + ".db"
    return os.path.join(basepath, dbfile)

def getDBConn(dbName):
    conn = sqlite3.connect(dbPath(dbName));
    return conn;

def getDBCursor(dbName):
    conn = sqlite3.connect(dbPath(dbName));
    cur = conn.cursor()
    return cur;

# sample file for testing
filepath = os.path.join(basepath, "exported_tracks.txt")
lines = [line.rstrip('\n') for line in open(filepath, encoding='utf-8')]


############################################################
##                                                        ##
##                      DB FUNCTIONS                      ##
##                                                        ##
############################################################

def createTable(cur):
    # Create table
    # create life, year, day mode columns and offsets
    cur.execute('''CREATE TABLE IF NOT EXISTS musics (
                 time integer primary key,
                 song text not null,
                 artist text not null,
                 album text not null,
                 year integer not null,
                 month integer not null,
                 timeofday integer not null,
                 month_offset integer not null,
                 day_offset integer not null,
                 song_uri text not null
                 )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS uris (
                 song_info text primary key,
                 song_uri text
                 )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS lastUpdatedTimestamp (
                 placeholder integer primary key,
                 timestamp datetime not null
                 )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS bucketCounters (
                 idx integer primary key,
                 counter integer not null
                 )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS dailyStats (
                 date datetime primary key,
                 life text not null,
                 year text not null,
                 day text not null
                 )''')

def isNonExistingEntry(trackTimestamp, lastUpdatedTimestamp, update=None):
    if (update is not None and update is True):
        # update new entries only
        return trackTimestamp > lastUpdatedTimestamp;
    else:
        # this is when creating initial DB
        # the process has interrupted in the middle and resuming; keep inserting older entries
        return not trackTimestamp < lastUpdatedTimestamp;

def insertTracks(cur, logger, file=None, limit=None, username=None, conn=None, update=None, tracksToInsert=None, token=None):
    if (file is not None and tracksToInsert is not None):
        print("[{}]: ## ERROR: Provide tracks OR a file, not both! Exiting..".format(timenow()))
        logger.info("[{}]: ## ERROR: Provide tracks OR a file, not both! Exiting..".format(timenow()))
        return;

    if (token is None):
        try:
            token = getSpotifyAuthToken(sh.spotify_username, sh.spotify_scope, sh.spotify_client_id, sh.spotify_client_secret, sh.spotify_redirect_uri)
        except:
            token = refreshSpotifyAuthToken(sh.spotify_username, sh.spotify_client_id, sh.spotify_client_secret, sh.spotify_redirect_uri, sh.spotify_scope)

    count = 0
    hit = 0
    if not (TESTING):
        sp = spotipy.Spotify(auth=token)
        print("[{}]: @@ got the token.".format(timenow()))
        logger.info("[{}]: @@ got the token.".format(timenow()))
    else:
        sp = None

    if (update is True):
        ### update track list for the deployment
        lastUpdatedTimestamp = getLatestTimestamp(cur);
    else:
        # for the initial db setup - to insert all entries
        lastUpdatedTimestamp = 0

    # provide csv file for listen history -- test only
    if (file is not None and tracksToInsert is None):
        tracksToInsert = map(lambda l: l.split('\t'), lines)


    # if it takes too long, access token expires, but we still want to move on
    # retry max 5 times
    for _ in range(int(5)):
        try:
            for track in tracksToInsert:
                if (TESTING):
                    song_uri = "tmp"
                else:
                    song_uri = None

                # create a dictionary key that associates (artist, track name)
                key = track[1] + " - " + track[2];

                # after this iterations are already inserted rows; skip all the remaining runs
                if (int(track[0]) == lastUpdatedTimestamp):
                    break;

                # get newer entries than lastUpdatedTimestamp from the Lastfm playlist
                if (isNonExistingEntry(int(track[0]), lastUpdatedTimestamp, update)):
                    # check if the song uri has been already searched from Spotify
                    song_uri = getSongURI(cur, key)
                    #print("@count: {} - uri: {}, key: ".format(str(count), song_uri, ))
                    # if not in the dictionary, check if the song exists on Spotify
                    if (song_uri is None):
                        if (token is not None):
                            query = buildSearchQuery(title=track[2], artist=track[1], album=track[3])
                            result = sp.search(q=query, type="track")
                            tracks = result['tracks'];
                            # if (DEBUGGING):
                            #     pprint.pprint(tracks)
                            # try again with out album name
                            if (tracks['total'] == 0):
                                #if (DEBUGGING):
                                    #print("### count:{}, Found no track, Retrying..".format(count))

                                query = buildSearchQuery(title=track[2], artist=track[1])
                                result = sp.search(q=query, type="track")
                                tracks = result['tracks'];
                                # if (DEBUGGING):
                                #     pprint.pprint(tracks)
                            for item in tracks['items']:
                                song_uri = item['uri']
                                # get the first matching song uri only
                                break;
                                #if (DEBUGGING):
                                    #print(item['name'], item['uri']);

                    # add songs to database that are found in Spotify
                    if (song_uri is not None):
                        # add a new entry in the dictionary
                        updateSongURI(cur, key, song_uri)
                        count += 1
                        hit += 1
                        track[0] = int(track[0])
                    #    print(time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime(l[0])));
                        trackTime = time.localtime(track[0])
                        trackTime_year = trackTime[0]
                        # month offset from the beginning of the year (tracktime - Jan 00:00:00 of the same year)
                        _yt = int(time.mktime(time.strptime(str(trackTime_year), '%Y')))
                        trackTime_month = trackTime[1]
                        trackTime_month_offset = track[0] - _yt
                        # use total minute as time in a day (= hour*60 + min)
                        trackTime_day = trackTime[3]*60 + trackTime[4]
                        # total seconds from 00:00 (= hour*3600 + min*60 + sec)
                        trackTime_day_offset = trackTime[3]*3600 + trackTime[4]*60 + trackTime[5]
                        track.extend([trackTime_year, trackTime_month, trackTime_day, trackTime_month_offset, trackTime_day_offset, song_uri]);
                        # swap song title and artist because of the db design
                        tmp = track[1]
                        track[1] = track[2]
                        track[2] = tmp;
                        cur.execute("INSERT OR IGNORE INTO musics VALUES(?,?,?,?,?,?,?,?,?,?)", track);
                    else:
                        # song not found on spotify
                        #print("@count: {} () NOT FOUND, skipping,,".format(str(count), ))
                        count += 1

                if (conn is not None and count % 500 == 0):
                    print("[{}]: @@ checkpoint at count: {}".format(timenow(), count))
                    logger.info("[{}]: @@ checkpoint at count: {}".format(timenow(), count))
                    conn.commit();

                if (limit is not None and count > limit):
                    break;

        except:
            print("[{}]: Exception while cross-checking..!!".format(timenow()))
            print(traceback.format_exc())
            logger.info("[{}]: Exception while cross-checking..!!".format(timenow()))
            logger.info(traceback.format_exc())
            print("[{}]: @@@ Getting a new token..".format(timenow()))
            logger.info("[{}]: @@@ Getting a new token..".format(timenow()))
            token = refreshSpotifyAuthToken(spotifyUsername=sh.spotify_username, client_id=sh.spotify_client_id, client_secret=sh.spotify_client_secret, redirect_uri=sh.spotify_redirect_uri, scope=sh.spotify_scope)
            sp = spotipy.Spotify(auth=token)
            continue;

    print("[{}]: @@ got {} tracks".format(timenow(), len(tracksToInsert)))
    print("[{}]: @@@ scanned {} songs, found {} songs on Spotify, exiting..".format(timenow(), count, hit))
    logger.info("[{}]: @@ got {} tracks".format(timenow(), len(tracksToInsert)))
    logger.info("[{}]: @@@ scanned {} songs, found {} songs on Spotify, exiting..".format(timenow(), count, hit))

def clearTable(cur, tableName):
    sql = "DELETE FROM {}".format(tableName)
    cur.execute(sql)

# this should be called once after the table is cleared
def vacuumTable(cur):
    cur.execute("VACUUM")

def dropTable(cur, tableName):
    sql = "DROP TABLE {}".format(tableName)
    cur.execute(sql)

def select_all(cur):
    i = 0
    cur.execute("SELECT * FROM musics")
    rows = cur.fetchall()
    for row in rows:
        i += 1
    print(i)

### Fetches all songs within one "bucket" in the given mode.
### Mode is one of: (life, year, day)
### Values must be an integer
### int value in day mode represents the hour
### The value of day could be a string of "HH:MM:SS" form
def getTracksRange(cur, mode, val):
    orig = val # this val is for the testing purpose - can be removed later
    i = 0;
    sql = "SELECT * FROM musics WHERE [arg] BETWEEN ? AND ?"
    if (mode == 'life'):
        fromYear = int(time.mktime(time.strptime(str(val), '%Y')))
        toYear = int(time.mktime(time.strptime(str(val+1), '%Y')))
        sql = sql.replace("[arg]", "time")
        val = (fromYear, toYear)
    elif (mode == 'year'):
        baseTimeStamp = int(time.mktime(time.strptime("00", '%y')))
        fromMonth = int(time.mktime(time.strptime("01 {} 00".format(str(val)), '%d %m %y')))
        if (val == 12):
            toMonth = int(time.mktime(time.strptime("01 01 01", '%d %m %y')))
        else:
            toMonth = int(time.mktime(time.strptime("01 {} 00".format(str(val+1)), '%d %m %y')))
        fromMonth -= baseTimeStamp
        toMonth -= baseTimeStamp
        sql = sql.replace("[arg]", "month_offset")
        val = (fromMonth, toMonth)
    elif (mode == 'day'):
        sql = sql.replace("[arg]", "day_offset")
        if (isinstance(val, str)):
            h,m,s = val.split(':')
            fromDay = int(h)*3600 + int(m)*60 + int(s)
            # do not go over the midnight
            if (int(h) == 23 and (int(m) > 0 or int(s) > 0)):
                toDay = 23*3600 + 59*60 + 59
            else:
                toDay = (int(h)+1)*3600 + int(m)*60 + int(s)
        else:
            fromDay = val
            toDay = val + 3600 # next hour
        val = (fromDay, toDay)
    if (DEBUGGING):
        print("mode:",mode,", val:",orig,", from:",time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime(val[0])),"(",val[0],") - to:",time.strftime("%Y/%m/%d, %H:%M:%S", time.localtime(val[1])),"(",val[1],")")
    cur.execute(sql, val)
    rows = cur.fetchall()
    for row in rows:
        # print(row)
        i += 1
    print(i)
    return rows

# find the track by a given index in a specified mode
def getTrackByIndex(cur, mode, idx):
    sql = '''SELECT * FROM musics
             ORDER BY [arg]
             LIMIT 1 OFFSET ?'''
    if (mode == 'life'):
        sql = sql.replace("[arg]", "time")
    elif (mode == 'year'):
        sql = sql.replace("[arg]", "month_offset, time")
    elif (mode == 'day'):
        sql = sql.replace("[arg]", "day_offset, time")
#    print(sql)
    cur.execute(sql, (idx-1,))
    row = cur.fetchall()
#    print(row)
    return row[0]

# find a track by its timestamp (unique ID)
def getTrackByTimestamp(cur, timestamp):
    cur.execute("SELECT * FROM musics WHERE time=?", (int(timestamp),));
    row = cur.fetchall();
#    print(row);
    return row[0]

# find the track by a given index in a specified mode
def getTrackFromBucket(cur, mode, bucket, offset):
    sql = '''SELECT * FROM musics
             WHERE [arg1] >= ?
             ORDER BY [arg2]
             LIMIT 1 OFFSET ?'''
    if (mode == 'life'):
        sql = sql.replace("[arg1]", "time")
        sql = sql.replace("[arg2]", "time")
    elif (mode == 'year'):
        sql = sql.replace("[arg1]", "month_offset")
        sql = sql.replace("[arg2]", "month_offset, time")
    else:
        sql = sql.replace("[arg1]", "day_offset")
        sql = sql.replace("[arg2]", "day_offset, time")
#    print(sql)
    cur.execute(sql, (bucket, offset))
    row = cur.fetchall()
#    print(row)
    return row[0]

# find the index of a track in a specified mode - return the absolute index as the life timestamp in the first argument
def findTrackIndex(cur, mode, timestamp):
    track = getTrackByTimestamp(cur, timestamp)
    sql = '''SELECT
              (SELECT COUNT(*) FROM musics AS t2
              WHERE (t2.[arg1] < [arg2]) OR ((t2.[arg1] == [arg2]) AND t2.time <= ?)
              )
             FROM musics AS t1
             ORDER BY [arg1], time
             LIMIT 1
             '''
    if (mode == 'life'):
        sql = sql.replace("[arg1]", "time")
        sql = sql.replace("[arg2]", str(timestamp))
    elif (mode == 'year'):
        sql = sql.replace("[arg1]", "month_offset")
        sql = sql.replace("[arg2]", str(track[7]))
    else:
        sql = sql.replace("[arg1]", "day_offset")
        sql = sql.replace("[arg2]", str(track[8]))
    if (DEBUGGING):
        print("query: ",sql)
    cur.execute(sql, (timestamp,));
    res = cur.fetchall()
    res = (res[0][0], track[4], track[5], track[6], track[7], track[8]) # (INDEX, year, month, timeofday, month_offset, day_offset)
    if (DEBUGGING):
        print("## ", res)
    return res;

def getLatestTimestamp(cur):
    sql = 'SELECT * FROM musics ORDER BY time DESC LIMIT 1'
    cur.execute(sql)
    res = cur.fetchall()
    return res[0][0];

def getBaseTimestamp(cur):
    sql = 'SELECT * FROM musics LIMIT 1'
    cur.execute(sql)
    res = cur.fetchall()
    return res[0][0];

def getTotalCount(cur):
    sql = 'SELECT COUNT(*) FROM musics'
    cur.execute(sql)
    res = cur.fetchall()
    return res[0][0];

def getBucketCount(cur, mode, lo, hi):
    sql = 'SELECT COUNT(*) FROM musics WHERE [arg] >= ? AND [arg] < ?'
    if (mode == 'life'):
        sql = sql.replace("[arg]", "time")
    elif (mode == 'year'):
        sql = sql.replace("[arg]", "month_offset")
    else:
        sql = sql.replace("[arg]", "day_offset")
    cur.execute(sql, (lo, hi))
    res = cur.fetchall()
    return res[0][0];

def getSongURI(cur, key):
    cur.execute("SELECT song_uri FROM uris WHERE song_info=? AND song_uri IS NOT NULL", (key,));
    res = cur.fetchall()
    #print("songURI: {}".format(res))
    if not res:
        return None;
    else:
        return res[0][0];

def updateSongURI(cur, key, uri):
    cur.execute("INSERT OR IGNORE INTO uris VALUES(?,?)", (key,uri));

def getLifeWindowSize(cur):
    cur.execute("SELECT time FROM musics ORDER BY TIME DESC LIMIT 1");
    res = cur.fetchall()
    max = int(res[0][0])
    cur.execute("SELECT time FROM musics LIMIT 1");
    res = cur.fetchall()
    min = int(res[0][0])
    return max - min

# manage bucket counters in DB
def getBucketCounters(cur, mode):
    cur.execute("SELECT * FROM bucketCounters")
    res = cur.fetchall()
    ret = [0]*64

    # life  - 0 (0,0)
    # day   - 1 (0,1)
    # year  - 2 (1,0)
    # *** life is the default offset
    offset = 0
    if (mode is 'day'):
        offset = 1
    elif (mode is 'year'):
        offset = 2

    i = 0
    for _ in range(64*offset, 64*(offset+1)):
        ret[i] = res[_][1]
        i += 1

    return ret

def updateBucketCounters(cur, idx, val, mode, conn):
    offset = 0
    if (mode is 'day'):
        offset = 1
    elif (mode is 'year'):
        offset = 2

    idx = idx + 64*offset
    cur.execute("UPDATE bucketCounters SET counter=? WHERE idx=?", (val, idx));

    conn.commit();

def initBucketCounters(cur, conn):
    # do upsert
    # have separate bucket counters for each mode; 64 buckets * 3 modes
    for _ in range(192):
        cur.execute("UPDATE bucketCounters SET counter=? WHERE idx=?", (0,_));
        if (cur.rowcount == 0):
            cur.execute("INSERT INTO bucketCounters VALUES (?,?)", (_,0));
    conn.commit();

def addDailyStats(cur, conn, date):
    cur.execute("SELECT * FROM bucketCounters")
    res = cur.fetchall()
    life = ""
    year = ""
    day = ""
    for _ in range(0, 192):
        if (_ < 64):
            life = life + str(res[_][1]) + " "
        elif (_ < 128):
            day = day + str(res[_][1]) + " "
        else:
            year = year + str(res[_][1]) + " "
    life = life.strip()
    year = year.strip()
    day = day.strip()
    cur.execute("INSERT OR REPLACE INTO dailyStats VALUES(?,?,?,?)", (date, life, year, day));
    conn.commit();
# ---------------------------------------------------------------------------

def test():
    start_time = time.time();
    # trackURIs = dict()
    #
    # if (os.path.isfile(uriFileName)):
    #     trackURIs = jsonToDict(uriFileName);

    # create a database connection and a cursor that navigates/retrieves the data
    conn = sqlite3.connect(dbpath);
    cur = conn.cursor()

#    createTable(cur);

    # getTotalCount(cur)

    ### PERFORMANCE TESTS
    insertTracks(cur, lines, 2000);
    # print(getLatestTimestamp(cur));

    # getTracksRange(cur, "life", 2016);
    # getTracksRange(cur, "year", 12)
    # getTracksRange(cur, 'day', "23:21:00")

    # getTrackByTimestamp(cur, 1466565074);

    # getTrackByIndex(cur, "year", 82385)

    # findTrackIndex(cur, 'day', 1486454402);
    # findTrackIndex(cur, 'day', 1365231604);

    # findTrackIndex(cur, 'day', 1472367600);
    # getTrackByIndex(cur, "day", 1)
    # findTrackIndex(cur, 'year', 1472367600);
    # getTrackByIndex(cur, "year", 75087)
    # findTrackIndex(cur, 'life', 1472367600);
    # getTrackByIndex(cur, "life", 89567)


    # # clear the data in the table
    # clearTable(cur, "musics");
    # vacuumTable(cur);

    # # drop the table
    # dropTable(cur, "musics");


    # Save (commit) the changes to the database
    conn.commit()

    # We can also close the connection if we are done with it.
    # Just be sure any changes have been committed or they will be lost.
    conn.close()

    # with open(uriFileName, 'w') as fp:
    #     json.dump(trackURIs, fp)

    print("--- ### Executed in [%s] seconds ---" % (time.time() - start_time));

# test()

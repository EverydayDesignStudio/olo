### THIS FILE MUST BE RUN WITH PYTHON 3.
### RUNNING WITH PYTHON 2 WILL CAUSE AN ERROR.

# https://developer.spotify.com/documentation/general/guides/scopes/
#-*-coding:utf-8-*-

import os.path, time, urllib, json, pprint, argparse, csv, ast

import socket
import sys
import traceback
from threading import Thread

import pylast

import sqlite3

import spotipy
import spotipy.oauth2 as oauth2
import spotipy.util as util


## for the testing purpose, mock all datas to speed up the process!
TESTING = False
DEBUGGING = True

############################################################
##                                                        ##
##                  API AUTHENTICATION                    ##
##                                                     s   ##
############################################################

### Spotify Auth

# a dictionary that saves track-uri pair to reduce spotify API calls on duplicate entries
trackURIs = dict()
if (TESTING):
    uriFileName = 'trackURIs_tmp.json'
else:
    if (os.name is 'nt'):
        uriFileName = 'trackURIs.json'
    else:
        uriFileName = '/home/pi/oloradio/trackURIs.json'

# spotify scope that runs the Spotify API
scope = 'user-modify-playback-state'

### get an auth for the app
### TODO: replace this with OLO Account ID
#if (os.name == 'nt'):
username = '31r27sr4fzqqd24rbs65vntslaoq'
client_id = '3f77a1d68f404a7cb5e63614fca549e3'
client_secret = '966f425775d7403cbbd66b838b23a488'
device_desktop = '2358d9d7c020e03c0599e66bb3cb244347dfe392'
device_oloradio1 = '1daca38d2ae160b6f1b8f4919655275043b2e5b4'
# else:
#     username = '9mgcb91qlhdu2kh4nwj83p165'
#     client_id = '86456db5c5364110aa9372794e146bf9'
#     client_secret = 'cd7177a48c3b4ea2a6139b88c1ca87f5'
#     device_oloradio1 = ''
### getting the device name is just a one-time thing
### or maybe ignore this to automatically connect to the active device
# spotify = spotipy.Spotify(auth=token)
# response = spotify.devices();
# pprint.pprint(response)


redirect_uri = 'https://example.com/callback/'
if (TESTING):
    token = None
else:
    token = util.prompt_for_user_token(username, scope, client_id = client_id, client_secret = client_secret, redirect_uri = redirect_uri)

if (DEBUGGING):
    print(token);

### TODO: what to do if an auth token expires?
# sp_oauth = oauth2.SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri=redirect_uri,scope=scopes)
# token_info = sp_oauth.get_cached_token()
# if sp_oauth.is_token_expired(token_info):
#     token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
#     token = token_info['access_token']
#     sp = spotipy.Spotify(auth=token)


### pylast
PYLAST_API_KEY = 'e38cc7822bd7476fe4083e36ee69748e'
### TODO: get the username and replace it accordingly
PYLAST_USER_NAME = 'username'


############################################################
##                                                        ##
##                   FUNCTIONS OVER API                   ##
##                                                        ##
############################################################

def buildSearchQuery(songTitle, artist, album=None):
    if (album is None):
        return '''"{}" artist:{}'''.format(songTitle, artist)
    else:
        return '''"{}" artist:{} album:{}'''.format(songTitle, artist, album)

def jsonToDict(filename):
   with open(filename, encoding='utf-8') as f_in:
       return(json.load(f_in))

def getLastFmHistroy(limit = None):
    conn_pylast = pylast.LastFMNetwork(api_key=PYLAST_API_KEY, username=PYLAST_USER_NAME)
    user = conn_pylast.get_user(PYLAST_USER_NAME)
    tracks = user.get_recent_tracks(limit = limit)
    res = list()
    for track in tracks:
        res.append([track.timestamp, track[0].artist.name, track[0].title, track.album]);
    return res;

############################################################
##                                                        ##
##                      FILE HANDLING                     ##
##                                                        ##
############################################################

### TODO: update the timestamp once in a day, save it to a file for further reference
lastUpdatedTimestamp = 0;

basepath = os.path.abspath(os.path.dirname(__file__))
if (os.name == 'nt'):
    ### WINDOWS
    # filepath = os.path.join(basepath, "tracks\\list.txt")
    filepath = os.path.join(basepath, "exported_tracks.txt")
else:
    ### LINUX
    # filepath = os.path.join(basepath, "./tracks/list.txt")
    filepath = os.path.join(basepath, "exported_tracks.txt")

dbpath = os.path.join(basepath, "./test.db")
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

def insertTracks(cur, file = None, limit = None):
    i = 0
    if not (TESTING):
        sp = spotipy.Spotify(auth=token)
        print("@@ got the token.")
    else:
        sp = None
    if (file is not None):
        tracks = map(lambda l: l.split('\t'), lines)
    else:
        tracks = getLastFmHistroy();  ### !! may have performance issue - calculate how many songs in DB, get only the offset amount from the Lastfm

    # lastUpdatedTimestamp = getLatestTimestamp(cur);
    lastUpdatedTimestamp = 0

    for track in tracks:
        if (TESTING):
            song_uri = "tmp"
        else:
            song_uri = None
        # skip already inserted rows
        if (int(track[0]) < lastUpdatedTimestamp):
            continue;
        # create a dictionary key that associates track name and artist
        key = track[1] + " - " + track[2];
        # check if the song uri has been already searched from Spotify
        song_uri = trackURIs.get(key)
        print("@i: {} - uri: {}".format(str(i), song_uri))
        # if not in the dictionary, check if the song exists on Spotify
        if (song_uri is None):
            if (token is not None):
                query = buildSearchQuery(track[1], track[2], track[3])
                result = sp.search(q=query, type="track")
                tracks = result['tracks'];
                # if (DEBUGGING):
                #     pprint.pprint(tracks)
                # try again with out album name
                if (tracks['total'] == 0):
                    if (DEBUGGING):
                        print("### i:{}, Found no track, Retrying..".format(i))
                    query = buildSearchQuery(track[1], track[2])
                    result = sp.search(q=query, type="track")
                    tracks = result['tracks'];
                    # if (DEBUGGING):
                    #     pprint.pprint(tracks)
                for item in tracks['items']:
                    song_uri = item['uri']
                    # get the first matching song uri only
                    break;
                    if (DEBUGGING):
                        print(item['name'], item['uri']);
            else:
                ### TODO: what do we do if the auth token is expired?
                pass
        # add songs to database that are found in Spotify
        if (song_uri is not None):
            # add a new entry in the dictionary
            trackURIs[key] = song_uri
#            print("@@@ found a track!, i: " + str(i))
            i += 1
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
            cur.execute("INSERT OR IGNORE INTO musics VALUES(?,?,?,?,?,?,?,?,?,?)", track);

        ## for testing only
        ## inserting 10 entries took 6 seconds and
        ## inserting ~1500 entries took ~12 minutes
        # if (TESTING and i >= 100):
        if (limit is not None and i >= limit):
            print("@@@ scanned {} songs, found {} songs on Spotify, exiting..".format(str(i), len(trackURIs)))
            break;

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

# life mode is equivalent to the original list
def orderBy_lifeMode(cur):
    i = 0
    cur.execute("SELECT * FROM musics")
    rows = cur.fetchall()
    for row in rows:
        i += 1
    print(i)

# year mode uses the month_offset of each track
def orderBy_yearMode(cur):
    i = 0;
    cur.execute("SELECT * from musics ORDER BY month_offset ASC, time ASC")
    rows = cur.fetchall()
    for row in rows:
        i += 1
    print(i)

# day mode uses the day_offset of each track
def orderBy_dayMode(cur):
    i = 0;
    cur.execute("SELECT * from musics ORDER BY day_offset ASC, time ASC")
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
    print(sql)
    cur.execute(sql, (idx-1,))
    row = cur.fetchall()
    print(row)
    return row

# find a track by its timestamp (unique ID)
def getTrackByTimestamp(cur, timestamp):
    cur.execute("SELECT * FROM musics WHERE time=?", (int(timestamp),));
    row = cur.fetchall();
    print(row);
    return row

# find the index of a track in a specified mode
def findTrackIndex(cur, mode, timestamp):
    track = getTrackByTimestamp(cur, timestamp)[0]
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
    elif (mode == 'day'):
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


############################################################
##                                                        ##
##                      ASYNC FUNCS                       ##
##                                                        ##
############################################################

### a producer template as below,,
# async def produce(queue):
#     while True:
#         # produce an item
#         # item = ... do something
#         item = input("what to do? ")
#
#         # put the item in the queue
#         await queue.put(item)

### starts the infinite loop
# async def run():
#     queue = asyncio.Queue()
#     # schedule the consumer
#     consumer = asyncio.ensure_future(consume(queue))
#     # run the producer and wait for completion
#     await produce(queue)
#     # wait until the consumer has processed all items
#     await queue.join()
#     # the consumer is still awaiting for an item, cancel it
#     consumer.cancel()

############################################################
# import asyncio, socket
#
# async def handle_client(reader, writer):
#     request = None
#     while request != 'quit':
#         request = (await reader.read(255)).decode('utf8')
#         response = str(eval(request)) + '\n'
#         print(response.encode('utf-8'))
#         writer.write(response.encode('utf8'))
#
# loop = asyncio.get_event_loop()
# loop.create_task(asyncio.start_server(handle_client, 'localhost', 15555))
# loop.run_forever()
#
# import asyncio
# from concurrent.futures import ThreadPoolExecutor
# from clientTest import produce
#
# def printItem(item):
#     print("I got '{}''".format(item))
#
# async def async_request(item, loop):
#     print("processing: {}".format(item))
#     """
#     This is a canonical way to turn a synchronized routine to async. event_loop.run_in_executor,
#     by default, takes a new thread from ThreadPool.
#     It is also possible to change the executor to ProcessPool.
#     """
#     ret = await loop.run_in_executor(ThreadPoolExecutor(), printItem, item)
#
#
# async def consume(queue, loop):
#     while True:
#         item = await queue.get()
#         if item is None:
#             break
#
#         await async_request(item, loop)
#         queue.task_done()
#
#     # with open('output.txt', 'w', encoding='utf-8') as f:
#     #
#     #     def write_to_file(url, ret):
#     #         f.write(url + "|" + ret + "\n")
#     #
#     #     while True:
#     #         item = await queue.get() # coroutine will be blocked if queue is empty
#     #
#     #         if item is None: # if poison pill is detected, exit the loop
#     #             break
#     #
#     #         await async_request(item, loop, write_to_file)
#     #         # signal that the current task from the queue is done
#     #         # and decrease the queue counter by one
#     #         queue.task_done()
#
# loop = asyncio.get_event_loop()
# queue = asyncio.Queue(loop=loop)
# producer_coro = produce(queue)
# consumer_coro = consume(queue, loop)
# loop.run_until_complete(asyncio.gather(producer_coro, consumer_coro))
# loop.close()
#
# exit()

# ----------------------------

start_time = time.time();

if (os.path.isfile(uriFileName)):
    trackURIs = jsonToDict(uriFileName);

# create a database connection and a cursor that navigates/retrieves the data
conn = sqlite3.connect(dbpath);
cur = conn.cursor()

# createTable(cur);


### PERFORMANCE TESTS
insertTracks(cur, lines, 350);
# print(getLatestTimestamp(cur));

# ### test the performance of re-ordering tables by mode
# tmp_time = time.time();
# orderBy_lifeMode(cur)
# print("--- order by year took [%s] seconds ---" % (time.time() - tmp_time));
# tmp_time = time.time();
# orderBy_yearMode(cur);
# print("--- order by month took [%s] seconds ---" % (time.time() - tmp_time));
# tmp_time = time.time();
# orderBy_dayMode(cur);
# print("--- order by timeOfDay took [%s] seconds ---" % (time.time() - tmp_time));

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

with open('trackURIs.json', 'w') as fp:
    json.dump(trackURIs, fp)

print("--- ### Executed in [%s] seconds ---" % (time.time() - start_time));

### TODO: write __main__

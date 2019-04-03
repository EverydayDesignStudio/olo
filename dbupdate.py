#!/usr/bin/env python3
#-*-coding:utf-8-*-

### TODO: make sure this file runs once in a day - https://www.raspberrypi.org/documentation/linux/usage/cron.md

import traceback
import dbFunctions as fn
import os.path, time, datetime
import traceback
import sqlite3
import sh
sh.init()

retry = 5;

print("@@ Running DB update at: {}".format(datetime.datetime.now()))
start_time = time.time();

# create a database connection and a cursor that navigates/retrieves the data
conn = sqlite3.connect(fn.dbPath(sh.dbname));
cur = conn.cursor()

cur.execute("SELECT * FROM lastUpdatedTimestamp");
res = cur.fetchone()

lastUpdatedDate = datetime.datetime.strptime(res[1], "%Y-%m-%d %H:%M:%S.%f")

if (datetime.datetime.now() - lastUpdatedDate) > datetime.timedelta(1):
    # do not run the script if the last updated date is within a day

    tracks = None
    for _ in range(int(retry)):
        try:
            tracks = getLastFmHistroy(username=sh.lastFM_username);
        except:
            print("@@ Caught an exception while getting LastFM Histroy,,")
            print(traceback.format_exc())
            print("retrying.. {} out of {}".format(str(_+1), str(retry)))
            continue;

    if (tracks is not None):
        for _ in range(int(retry)):
            try:
                # insert tracks
                fn.insertTracks(cur, username=sh.lastFM_username, conn=conn, update=True, tracks=tracks);
            except:
                print("@@ Caught an exception while initializing DB,,")
                print(traceback.format_exc())
                print("@@  retrying.. {} out of {}".format(str(_+1), str(retry)))
                print(traceback.format_exc())
                continue;

            # reset bucket counters
            fn.initBucketCounters(cur, conn=conn);

            # insert a timestamp
            cur.execute("INSERT OR REPLACE INTO lastUpdatedTimestamp VALUES(?,?)", (1,datetime.datetime.now()));
            conn.commit();
            break;

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()

# print("--- ### Executed in [%s] seconds ---" % (time.time() - start_time));

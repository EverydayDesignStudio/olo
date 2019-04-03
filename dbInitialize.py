#!/usr/bin/env python3
#-*-coding:utf-8-*-

# https://github.com/pylast/pylast/issues/296

import traceback
import dbFunctions as fn
import os.path, time, datetime
import sqlite3
import sh
sh.init()

retry = 5;

print("@@ Initializing DB at: {}".format(datetime.datetime.now()))
start_time = time.time();

# create a database connection and a cursor that navigates/retrieves the data
conn = sqlite3.connect(fn.dbPath(sh.dbname));
cur = conn.cursor()

# Create tables if not exists
fn.createTable(cur);

# initialize bucket counters
fn.initBucketCounters(cur, conn);

tracks = None

for _ in range(int(retry)):
    try:
        tracks = fn.getLastFmHistroy(username=sh.lastFM_username);
    except:
        print("@@ Caught an exception while getting LastFM Histroy,,")
        print(traceback.format_exc())
        print("retrying.. {} out of {}".format(str(_+1), str(retry)))
        continue;

if (tracks is not None):
    for _ in range(int(retry)):
        try:
            # insert tracks
            fn.insertTracks(cur, username=sh.lastFM_username, conn=conn, tracks=tracks);
        except:
            print("@@ Caught an exception while initializing DB,,")
            print(traceback.format_exc())
            print("retrying.. {} out of {}".format(str(_+1), str(retry)))
            continue;

        cur.execute("INSERT OR REPLACE INTO lastUpdatedTimestamp VALUES(?,?)", (1,datetime.datetime.now()));
        conn.commit();

        break;

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


print("--- ### Executed in [%s] seconds ---" % (time.time() - start_time));

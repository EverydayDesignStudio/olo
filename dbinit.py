#!/usr/bin/env python3
#-*-coding:utf-8-*-

import dbFunctions as fn
import os.path, time, datetime
import sqlite3
import sh
sh.init()

retry = 10;

print("@@ Initializing DB at: {}".format(datetime.datetime.now()))
start_time = time.time();

# create a database connection and a cursor that navigates/retrieves the data
conn = sqlite3.connect(fn.dbPath(sh.dbname));
cur = conn.cursor()

# Create tables if not exists
fn.createTable(cur);

# initialize bucket counters
fn.initBucketCounters(cur);

for _ in range(int(retry)):
    try:
        # insert tracks
        fn.insertTracks(cur, username=sh.lastFM_username, conn=conn);
    except:
        print("@@ Caught an exception, retrying.. {} out of {}".format(str(_), str(retry)))
        retry += 1;
        continue;
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

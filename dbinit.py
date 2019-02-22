#!/usr/bin/env python3
#-*-coding:utf-8-*-

### Usage
#   python dbinit username [-c] [-n 1000] [-db dbname]
#       * n is the number of entries to fetch.
#       * Without n, it will fetch the entire history in Last.fm

### TODO: arg handling

import dbtest as fn
import os.path, time, urllib, json, argparse
import sqlite3
import sh
sh.init()

start_time = time.time();
# trackURIs = dict()
#
# if (os.path.isfile(fn.uriFileName)):
#     uriDict = fn.jsonToDict(fn.uriFileName);

# create a database connection and a cursor that navigates/retrieves the data
conn = sqlite3.connect(fn.dbPath(sh.dbname));
cur = conn.cursor()

### TODO: arg '-c' to create table
# fn.createTable(cur);

### PERFORMANCE TESTS
# fn.insertTracks(cur, fn.lines, 500, trackURIs=trackURIs, username = 'yoomy1203');
fn.insertTracks(cur, username=sh.username, conn=conn);

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

# with open(fn.uriFileName, 'w') as fp:
#     json.dump(trackURIs, fp)

print("--- ### Executed in [%s] seconds ---" % (time.time() - start_time));

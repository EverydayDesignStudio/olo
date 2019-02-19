#!/usr/bin/env python3
#-*-coding:utf-8-*-

### TODO: make sure this file runs once in a day - https://www.raspberrypi.org/documentation/linux/usage/cron.md

import dbtest as fn
import os.path, time, urllib, json, argparse
import sqlite3
import sh
sh.init()

start_time = time.time();

# create a database connection and a cursor that navigates/retrieves the data
# TODO: move db name to the config file
conn = sqlite3.connect(fn.dbPath(sh.dbname));
cur = conn.cursor()

### PERFORMANCE TESTS
fn.insertTracks(cur, username=sh.username, conn=conn, update=True);

# reset counters
sh.bucketCounter = [0] * 64

conn.commit()

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()

# print("--- ### Executed in [%s] seconds ---" % (time.time() - start_time));

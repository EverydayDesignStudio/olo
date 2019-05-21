#!/usr/bin/env python3
#-*-coding:utf-8-*-

# https://github.com/pylast/pylast/issues/296

import dbFunctions as fn
import traceback, sqlite3, os.path, time, datetime, logging, os
import sh
sh.init()

today = lambda: str(datetime.datetime.now()).split(' ')[0]
timenow = lambda: str(datetime.datetime.now()).split('.')[0]

retry = 10;

################## Create Logger ##################
logger = logging.getLogger("Initialize Log")
logger.setLevel(logging.INFO)

if os.name == 'nt':
    log_file = r"C:\tmp\initialize-{}.log".format(today())
else:
    log_file = "/home/pi/Desktop/olo/log_initialize/initialize-{}.log".format(today())
    directory = "/home/pi/Desktop/olo/log_initialize/"
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

open(log_file, 'a')

handler = logging.FileHandler(log_file)
logger.addHandler(handler)
###################################################


print("[{}]: @@ Initializing DB at: {}".format(timenow(), datetime.datetime.now()))
logger.info("[{}]: @@ Initializing DB at: {}".format(timenow(), datetime.datetime.now()))

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
        print("[{}]: ## Get Tracks".format(timenow()))
        logger.info("[{}]: ## Get Tracks".format(timenow()))
        tracks = fn.getLastFmHistroy(username=sh.lastFM_username);

    except KeyboardInterrupt:
        quit()

    except:
        print("[{}]: @@ Caught an exception while getting LastFM Histroy,,".format(timenow()))
        print(traceback.format_exc())
        print("[{}]: retrying.. {} out of {}".format(timenow(), str(_+1), str(retry)))
        logger.info("[{}]: @@ Caught an exception while getting LastFM Histroy,,".format(timenow()))
        logger.info(traceback.format_exc())
        logger.info("[{}]: retrying.. {} out of {}".format(timenow(), str(_+1), str(retry)))

        continue;

if (tracks is not None):
    print("[{}]: !! Got {} LastFM tracks".format(timenow(), len(tracks)))
    logger.info("[{}]: !! Got {} LastFM tracks".format(timenow(), len(tracks)))

    for _ in range(int(retry)):
        try:
            # insert tracks
            print("[{}]: ## Inserting Tracks..".format(timenow()))
            logger.info("[{}]: ## Inserting Tracks..".format(timenow()))

            fn.insertTracks(cur, username=sh.lastFM_username, conn=conn, logger=logger, tracksToInsert=tracks);

        except KeyboardInterrupt:
            quit()

        except:
            print("[{}]: @@ Caught an exception while initializing DB,,".format(timenow()))
            print(traceback.format_exc())
            print("[{}]: retrying.. {} out of {}".format(timenow(), str(_+1), str(retry)))
            logger.info("[{}]: @@ Caught an exception while initializing DB,,".format(timenow()))
            logger.info(traceback.format_exc())
            logger.info("[{}]: retrying.. {} out of {}".format(timenow(), str(_+1), str(retry)))

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


print("[{}]: --- ### Executed in [{}] seconds ---".format(timenow(), time.time() - start_time));
logger.info("[{}]: --- ### Executed in [{}] seconds ---".format(timenow(), time.time() - start_time))

#!/usr/bin/env python3
#-*-coding:utf-8-*-

import dbFunctions as fn
import os.path, traceback, time, datetime, logging, os
import sqlite3
import sh
sh.init()

retry = 10;
baseScale = 100
today = lambda: str(datetime.datetime.now()).split(' ')[0]
timenow = lambda: str(datetime.datetime.now()).split('.')[0]

################## Create Logger ##################
logger = logging.getLogger("Update Log")
logger.setLevel(logging.INFO)

if os.name == 'nt':
    log_file = r"C:\tmp\dbupdate-{}.log".format(today())
else:
    log_file = "/home/pi/Desktop/olo/log_dbupdate/dbupdate-{}.log".format(today())
    directory = "/home/pi/Desktop/olo/log_dbupdate/"
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

open(log_file, 'a')

handler = logging.FileHandler(log_file)
logger.addHandler(handler)
###################################################

startTime = datetime.datetime.now()
print("[{}]: @@ Running DB update at: {}".format(timenow(), startTime))
logger.info("[{}]: @@ Running DB update at: {}".format(timenow(), startTime))

start_time = time.time();

# create a database connection and a cursor that navigates/retrieves the data
conn = sqlite3.connect(fn.dbPath(sh.dbname_eds));
cur = conn.cursor()

fn.addDailyStats(cur, conn, startTime)

cur.execute("SELECT * FROM lastUpdatedTimestamp");
res = cur.fetchone()

lastUpdatedDate = datetime.datetime.strptime(res[1], "%Y-%m-%d %H:%M:%S.%f")
tracks_dict = {};

# do not run the script if the last updated date is within a day
timeDiff = (startTime - lastUpdatedDate)
timeDiff_mins = int(timeDiff.total_seconds()/60)
logger.info("[{}]: ** Time difference in minutes is {}".format(timenow(), timeDiff_mins))
# allow max 10 minutes of update time when checking freshness
if (timeDiff_mins > 1430):
    print("[{}]: @@ DB is outdated. Starts updating..".format(timenow()))
    logger.info("[{}]: @@ DB is outdated. Starts updating..".format(timenow()))

    limitScale = timeDiff.days * baseScale * 1.5
    if (limitScale > 1000):
        limitScale = 1000

    if (sh.OLO_ID != 1):
        tracks = None
        for _ in range(int(retry)):
            try:
                tracks = fn.getLastFmHistroy(username=sh.lastFM_username, limit=limitScale);

            except KeyboardInterrupt:
                exit()

            except:
                print("[{}]: @@ Caught an exception while getting LastFM Histroy,,".format(timenow()))
                print(traceback.format_exc())
                print("[{}]: retrying.. {} out of {}".format(timenow(), str(_+1), str(retry)))
                logger.info("[{}]: @@ Caught an exception while getting LastFM Histroy,,".format(timenow()))
                logger.info(traceback.format_exc())
                logger.info("[{}]: retrying.. {} out of {}".format(timenow(), str(_+1), str(retry)))
                continue;

    else:
        c = 0;
        for _ in range(int(retry)):
            try:
                print("[{}]: ## Getting Tracks from {}".format(timenow(), sh.lastFM_username_eds[c]))
                logger.info("[{}]: ## Getting Tracks from {}".format(timenow(), sh.lastFM_username_eds[c]))
                # tracks = fn.getLastFmHistroy(username=sh.lastFM_username);
                tracks = fn.getLastFmHistroy(username = sh.lastFM_username_eds[c], limit=limitScale)
            except KeyboardInterrupt:
                quit()

            except:
                _ += 1;
                print("[{}]: @@ Caught an exception while getting LastFM Histroy,,".format(timenow()))
                print(traceback.format_exc())
                print("[{}]: retrying.. {}".format(timenow(), _))
                logger.info("[{}]: @@ Caught an exception while getting LastFM Histroy,,".format(timenow()))
                logger.info(traceback.format_exc())
                logger.info("[{}]: retrying.. {}".format(timenow(), _))

                continue;

            if (tracks is not None):
                print("[{}]: @@ got {} tracks from {}".format(timenow(), len(tracks), sh.lastFM_username_eds[c]))
                logger.info("[{}]: @@ got {} tracks from {}".format(timenow(), len(tracks), sh.lastFM_username_eds[c]))
                for track in tracks:
                    skip = False;
                    key = int(track[0])
                    # if another entry is found at the same timestamp
                    if key in tracks_dict:
                        # try searching for an empty timestamp for the next 5 slots
                        skip = True
                        for i in range(6):
                            # if an empty slot is found, update the timestamp
                            if (key+i) not in tracks_dict:
                                key = key+i
                                track[0] = str(key)
                                skip = False
                                break;
                    if (not skip):
                        tracks_dict[key] = track
                tracks = None
                c += 1;

            if (c >= len(sh.lastFM_username_eds)):
                break;

    if (sh.OLO_ID == 1):
        print("\nTotal dictionary size: {}".format(len(tracks_dict)))
        logger.info("\nTotal dictionary size: {}".format(len(tracks_dict)))
        tracks = list(sorted(tracks_dict.values(), key=lambda x: int(x[0]), reverse=True))

    print("Total tracks length: {}".format(len(tracks)))
    logger.info("Total tracks length: {}".format(len(tracks)))

    if (tracks is not None):
        print("[{}]: ### tracks: {}, length: {}".format(timenow(), type(tracks), len(tracks)))
        logger.info("[{}]: ### tracks: {}, length: {}".format(timenow(), type(tracks), len(tracks)))
        for _ in range(int(retry)):
            try:
                # insert tracks
                fn.insertTracks(cur, username=sh.lastFM_username, conn=conn, logger=logger, update=True, tracksToInsert=tracks);

            except KeyboardInterrupt:
                exit()

            except:
                print("[{}]: @@ Caught an exception while initializing DB,,".format(timenow()))
                print(traceback.format_exc())
                print("[{}]: @@  retrying.. {} out of {}".format(timenow(), str(_+1), str(retry)))
                logger.info("[{}]: @@ Caught an exception while initializing DB,,".format(timenow()))
                logger.info(traceback.format_exc())
                logger.info("[{}]: retrying.. {} out of {}".format(timenow(), str(_+1), str(retry)))
                continue;

            # insert a timestamp
            cur.execute("INSERT OR REPLACE INTO lastUpdatedTimestamp VALUES(?,?)", (1, datetime.datetime.now()));
            conn.commit();
            break;

else:
    print("[{}]: @@ DB is still fresh!".format(timenow()))
    logger.info("[{}]: @@ DB is still fresh!".format(timenow()))

# save and reset bucket counters
fn.initBucketCounters(cur, conn=conn, update=True);

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()

print("[{}]: --- ### Executed in [{}] seconds ---".format(timenow(), time.time() - start_time));
logger.info("[{}]: --- ### Executed in [{}] seconds ---".format(timenow(), time.time() - start_time))

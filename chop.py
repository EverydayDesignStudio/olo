

import csv
import time
import datetime
import sh

segments = 100


def convertTimestamp(tstamp):
    print datetime.datetime.fromtimestamp(int(tstamp))

convertTimestamp(time.time())



import csv
import datetime
"""
import time

import sh

segments = 100



def convertTimestamp(tstamp):
    print datetime.datetime.fromtimestamp(int(tstamp))

convertTimestamp(time.time())
"""


"""
f = open(adresse,"r")
reader = csv.reader(f,delimiter = ",")
data = [l for l in reader]


print row_count

"""

with open('tracks/exported_tracks.txt','rb') as f:
    reader = csv.reader(f, delimiter = '\t' )
    row_count = sum(1 for row in reader)

    index = 0
    fileName = str(index) + '_life.csv'
    for row in range(row_count):
        print(reader.row[1])

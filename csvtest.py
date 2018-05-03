import csv
import datetime
import calendar
import time

class col:
    prp = '\033[95m'
    vio = '\033[94m'
    gre = '\033[92m'
    yel = '\033[93m'
    ora = '\033[91m'
    none = '\033[0m'
    red = '\033[1m'
    und = '\033[4m'



def convertTimestamp(tstamp):

    _dt = datetime.datetime.fromtimestamp(int(tstamp))
    return _dt

def yearTimestamp(tstamp):
    #print 'tstamp: ' + str(tstamp)
    tstamp = int(tstamp)
    year = datetime.datetime.fromtimestamp(tstamp).strftime('%Y')
    _yt = int(time.mktime(time.strptime(year, '%Y')))# epoch time of Jan 1st 00:00 of the year of the song
    _dt = datetime.datetime.fromtimestamp(int(tstamp - _yt))
    return _dt

def dayTimestamp(tstamp):
    #print 'tstamp: ' + str(tstamp)
    tstamp = int(tstamp)
    pattern = '%Y %m %d'
    day = datetime.datetime.fromtimestamp(tstamp).strftime(pattern)
    _dayt = int(time.mktime(time.strptime(day + ' 00 : 00 : 00', pattern + ' %H : %M : %S' ))) # epoch time since beginning of the day
    _dt = datetime.datetime.fromtimestamp(int(tstamp - _dayt))
    return _dt


then = time.time()
lifetime = 0
yeartime = 0
daytime = 0

filename = 'tracks/exported_tracks.txt'
with open(filename,'rb') as f:
    reader = csv.reader(f, delimiter = '\t' )
    print 'ok, now sorting...'


    # sort by life
    # =====================================================
    lifename = str.split(filename, '.txt')[0] + '_life.txt'
    f.seek(0)
    with open(lifename, 'w') as wl:
        writer = csv.writer(wl, delimiter = '\t')
        data = sorted(f, key = lambda row: str.split(row, '\t')[0])
        #print data
        print 'sorted!'
        sortedreader = csv.reader(data, delimiter='\t')
        for row in sortedreader:
            print row[0]
            print 'datetime: ' + str(convertTimestamp(row[0]))
            print row[1] + '  -  ' + row[2]
            print col.gre + '- - - - - - - - - - - - - - -' + col.none
            writer.writerow([convertTimestamp(row[0])] + row)
    lifetime = time.time() - then


    # sort by year
    # =====================================================
    now = time.time()
    yearname = str.split(filename, '.txt')[0] + '_year.txt'
    f.seek(0)
    with open(yearname, 'w') as wl:
        writer = csv.writer(wl, delimiter = '\t')
        data = sorted(f, key = lambda row: yearTimestamp(str.split(row, '\t')[0]))
        #print data
        print 'sorted!'
        sortedreader = csv.reader(data, delimiter='\t')
        for row in sortedreader:
            print row[0]
            print 'datetime: ' + str(convertTimestamp(row[0]))
            print row[1] + '  -  ' + row[2]
            print col.prp + '- - - - - - - - - - - - - - -' + col.none
            writer.writerow([convertTimestamp(row[0])] + row)
    yeartime = time.time() - now


    # sort by day
    # =====================================================
    now = time.time()
    dayname = str.split(filename, '.txt')[0] + '_day.txt'
    f.seek(0)
    with open(dayname, 'w') as wl:
        writer = csv.writer(wl, delimiter = '\t')
        data = sorted(f, key = lambda row: dayTimestamp(str.split(row, '\t')[0]))
        #print data
        print 'sorted!'
        sortedreader = csv.reader(data, delimiter='\t')
        for row in sortedreader:
            print row[0]
            print 'dayTimestamp: ' + str(dayTimestamp(row[0]))
            print 'datetime: ' + str(convertTimestamp(row[0]))
            print row[1] + '  -  ' + row[2]
            print col.red + '- - - - - - - - - - - - - - -' + col.none
            writer.writerow([convertTimestamp(row[0])] + row)
    daytime = time.time() - now
print 'total sorting time: ' + str(time.time() - then)
print 'life: ' + lifetime
print 'year: ' + yeartime
print 'day: ' + daytime

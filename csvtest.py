import csv
import datetime
import calendar
import time

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
    _dayt = int(time.mktime(time.strptime(day + '00 : 00 : 00', pattern + '%H : %M : %S' ))) # epoch time since beginning of the day
    _dt = datetime.datetime.fromtimestamp(int(tstamp - _dayt))
    return _dt

filename = 'tracks/exported_tracks.txt'
with open(filename,'rb') as f:
    reader = csv.reader(f, delimiter = '\t' )
    for row in reader:
        print 'datetime: ' + str(convertTimestamp(row[0]))
        print row[1] + '  -  ' + row[2]
        print row
        print 'O R I G I N A L - - - - - - - - - - -'
    print 'ok, now sorting...'
    time.sleep(1)



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
            print 'datetime: ' + str(convertTimestamp(row[0]))
            print row[1] + '  -  ' + row[2]
            print 'L I F E - - - - - - - - - - - - - - -'
            writer.writerow(row)


    # sort by year
    # =====================================================
    yearname = str.split(filename, '.txt')[0] + '_year.txt'
    f.seek(0)
    with open(yearname, 'w') as wl:
        writer = csv.writer(wl, delimiter = '\t')
        data = sorted(f, key = lambda row: yearTimestamp(str.split(row, '\t')[0]))
        #print data
        print 'sorted!'
        sortedreader = csv.reader(data, delimiter='\t')
        for row in sortedreader:
            print 'datetime: ' + str(convertTimestamp(row[0]))
            print row[1] + '  -  ' + row[2]
            print 'Y E A R - - - - - - - - - - - - - - -'
            writer.writerow(row)

    # sort by day
    # =====================================================
    dayname = str.split(filename, '.txt')[0] + '_day.txt'
    f.seek(0)
    with open(dayname, 'w') as wl:
        writer = csv.writer(wl, delimiter = '\t')
        data = sorted(f, key = lambda row: dayTimestamp(str.split(row, '\t')[0]))
        #print data
        print 'sorted!'
        sortedreader = csv.reader(data, delimiter='\t')
        for row in sortedreader:
            print 'datetime: ' + str(convertTimestamp(row[0]))
            print row[1] + '  -  ' + row[2]
            print 'D A Y - - - - - - - - - - - - - - -'
            writer.writerow(row)

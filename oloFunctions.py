try:
    import Adafruit_MCP3008
    import RPi.GPIO as gpio
except:
    pass
import time
import sh
import datetime

class col:
    prp = '\033[95m'
    vio = '\033[94m'
    gre = '\033[92m'
    yel = '\033[93m'
    ora = '\033[91m'
    none = '\033[0m'
    red = '\033[1m'
    und = '\033[4m'

# Software SPI configuration:
try:
    mcp = Adafruit_MCP3008.MCP3008(clk = sh.CLK, cs = sh.CS, miso = sh.MISO, mosi = sh.MOSI)

    gpio.setup(17, gpio.IN) #gpio 16  - three pole switch 1
    gpio.setup(18, gpio.IN) #gpio 18  - three pole switch 2
except:
    pass

def convertTimestamp(tstamp):
    _dt = datetime.datetime.fromtimestamp(int(tstamp))
    return _dt

def yearTimestamp(tstamp):
    #print 'tstamp: ' + str(tstamp)
    tstamp = int(tstamp)
    year = datetime.datetime.fromtimestamp(tstamp).strftime('%Y')
    _yt = int(time.mktime(time.strptime(year, '%Y')))# epoch time of Jan 1st 00:00 of the year of the song
    _dt = datetime.datetime.fromtimestamp(int(tstamp - _yt))
    return _dt, int(tstamp - _yt)

def dayTimestamp(tstamp):
    #print 'tstamp: ' + str(tstamp)
    tstamp = int(tstamp)
    pattern = '%Y %m %d'
    day = datetime.datetime.fromtimestamp(tstamp).strftime(pattern)
    # print 'DAY DAY DAY ', day
    _dayt = int(time.mktime(time.strptime(day + ' 00 : 00 : 00', pattern + ' %H : %M : %S' ))) # epoch time since beginning of the day
    _dt = datetime.datetime.fromtimestamp(int(tstamp - _dayt + (25200))) # account for time zone
    return _dt, int(tstamp - _dayt + 0) #(25200))


def timeframe():
    def checksame():
        if sh.timeframe == sh.prevtimeframe:
            return 1
        else:
            return 0

    sh.prevtimeframe = sh.timeframe
    if sh.values[2] < 10:
        if sh.values[3] < 10:
            # (0, 0)
            sh.timeframe = 'life'
            if sh.timeframe == sh.prevtimeframe:
                return 1
            else:
                return 0
        else:
            # (0, 1)
            sh.timeframe = 'year'
            if sh.timeframe == sh.prevtimeframe:
                return 1
            else:
                return 0
    else:
        if sh.values[3] < 10:
            # (1, 0)
            sh.timeframe = 'day '
            if sh.timeframe == sh.prevtimeframe:
                return 1
            else:
                return 0
        else:
            # (1, 1)
            sh.timeframe = 'err  '
            return -1
    sh.timeframe = 'unkn '
    return -2

def readValues():
    # Read all the ADC channel values in a list.
    sh.values = [0]*8
    for i in range(8):
        # The read_adc function will get the value of the specified channel (0-7).
        sh.values[i] = mcp.read_adc_difference(i)
        # values[2] = gpio.input(sh.switch1) #when 3pole switch <--> GPIO 23
        # values[3] = gpio.input(sh.switch2) #when 3pole switch <--> GPIO 24
    return sh.values



def printValues(vals):
    newVals = [0] * 8
    for i in range(8):
        newVals[i] = vals[i]
    print(newVals[0])
    # Pause for half a second.
    #time.sleep(0.5)

def moveslider(_target):
    prev = '<>'
    touch = 0
    while (distance(_target) > 10):
        #print('motor loop')
        if (sh.values[sh.touch_ch] > 1): # if capacitive touch is touched
            touch = touch + 1
            if (touch > 2):
                print 'motor touched, waiting...'
                for t in range(5):
                    gpio.output(sh.mLeft, True)
                    gpio.output(sh.mRight, True)
                gpio.output(sh.mLeft, False)
                gpio.output(sh.mRight, False)
                prev = 0
        else:
            touch = 0
            if sh.values[sh.slider_ch] > _target:
                if prev == 1:
                    while(distance(_target)>150):
                        print('==pwmleft')
                        duty = 0.005
                        gpio.output(sh.mLeft, True)
                        time.sleep(duty)
                        gpio.output(sh.mLeft, False)
                        time.sleep(0.01 - duty)
                else:
                    gpio.output(sh.mRight, False)
                    if distance(_target) > 10:
                        print(col.yel + 'tar: ' + col.none + str(_target) + col.yel + '  cur: ' + col.none  + str(sh.values[sh.slider_ch]) + col.gre + ' ---o>>' + col.none)
                        gpio.output(sh.mLeft, True)
                    else:
                        while(distance(_target)>150):
                            print('==pwmleft')
                            duty = 0.005
                            gpio.output(sh.mLeft, True)
                            time.sleep(duty)
                            gpio.output(sh.mLeft, False)
                            time.sleep(0.01 - duty)
                    prev = 1
            if sh.values[sh.slider_ch] < _target:
                if prev == 2:
                    while(distance(_target)>150):
                        print('==pwmleft')
                        duty = 0.005
                        gpio.output(sh.mRight, True)
                        time.sleep(duty)
                        gpio.output(sh.mRight, False)
                        time.sleep(0.01 - duty)
                else:
                    gpio.output(sh.mLeft, False)
                    if distance(_target) > 10:
                        print(col.yel +'tar: '+ col.none + str(_target) + col.yel +'  cur: '+ col.none + str(sh.values[sh.slider_ch]) + col.red + ' <<o---' + col.none)
                        gpio.output(sh.mRight, True)
                    else:
                        while(distance(_target)>150):
                            print('==pwmleft')
                            duty = 0.005
                            gpio.output(sh.mRight, True)
                            time.sleep(duty)
                            gpio.output(sh.mRight, False)
                            time.sleep(0.01 - duty)
                    prev = 2

            #time.sleep(1)
        readValues()
    # turn off motor and print location
    print 'hard stop'
    gpio.output(sh.mLeft, False)
    gpio.output(sh.mRight, False)
    readValues()
    print 'motor move complete: '
    print 'position: ' + str(sh.values[sh.slider_ch])

def distance(_target):
    readValues()
    return abs(sh.values[sh.slider_ch] - _target)

# def moveslider(_target):
#     prev = '<>'
#     sh.values = readValues()
#     wi_channel = 4
#     while (abs(sh.values[wi_channel] - _target) > 5):
#         #print('motor loop')
#         if (sh.values[1] > 1): # if capacitive touch is touched
#             touch = touch + 1
#             if (touch > 2):
#                 print 'motor touched, waiting...'
#                 gpio.output(sh.mLeft, False)
#                 gpio.output(sh.mRight, False)
#                 prev = 0
#         else:
#             touch = 0
#             if sh.values[wi_channel] > _target:
#                 print(col.yel + 'tar: ' + col.none + str(_target) + col.yel + '  cur: ' + col.none  + str(sh.values[0]) + col.gre + ' ---o>>' + col.none)
#                 if prev == 1:
#                     pass
#                 else:
#                     gpio.output(sh.mLeft, True)
#                     gpio.output(sh.mRight, False)
#                     prev = 1
#             if sh.values[wi_channel] < _target:
#                 print(col.yel +'tar: '+ col.none + str(_target) + col.yel +'  cur: '+ col.none + str(sh.values[0]) + col.red + ' <<o---' + col.none)
#                 if prev == 2:
#                     pass
#                 else:
#                     prev = 2
#                     gpio.output(sh.mLeft, False)
#                     gpio.output(sh.mRight, True)
#             #time.sleep(1)
#         readValues()
#     # turn of motor and print location
#     gpio.output(sh.mLeft, False)
#     gpio.output(sh.mRight, False)
#     readValues()
#     print 'motor move complete: '
#     print 'position: ' + str(sh.values[0])

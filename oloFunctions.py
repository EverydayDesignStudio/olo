import Adafruit_MCP3008
import RPi.GPIO as gpio
import time
import sh

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
mcp = Adafruit_MCP3008.MCP3008(clk = sh.CLK, cs = sh.CS, miso = sh.MISO, mosi = sh.MOSI)

gpio.setup(17, gpio.IN) #gpio 16  - three pole switch 1
gpio.setup(18, gpio.IN) #gpio 18  - three pole switch 2

# def readhistory(timeframe, segment):

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
            sh.timeframe = 'life '
            return checksame()
        else:
            # (0, 1)
            sh.timeframe = 'year '
            return checksame()
    else:
        if sh.values[3] < 10:
            # (1, 0)
            sh.timeframe = 'day  '
            return checksame()
        else:
            # (1, 1)
            sh.timeframe = 'err  '
            return -1
    sh.timeframe = 'unkn '
    return -2

def readValues():
    # Read all the ADC channel values in a list.
    sh.values = [0]*8
    for i in range(7):
        # The read_adc function will get the value of the specified channel (0-7).
        sh.values[i] = mcp.read_adc_difference(i)
        # values[2] = gpio.input(sh.switch1) #when 3pole switch <--> GPIO 23
        # values[3] = gpio.input(sh.switch2) #when 3pole switch <--> GPIO 24
    return sh.values


def printValues(vals):
    print(col.red + sh.timeframe + col.none + str('=' * 24))
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} |'.format(*sh.labels))
    #print('-' * 29)
    newVals = [0] * 4
    for i in range(4):
        newVals[i] = vals[i]
    newVals[0] = vals[4]
    #print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*vals))
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} |'.format(*newVals))
    # Pause for half a second.
    time.sleep(0.5)

def moveslider(_target):
    prev = '<>'
    sh.values = readValues()
    while (abs(sh.values[wi_channel] - _target) > 5):
        #print('motor loop')
        if (sh.values[1] > 1): # if capacitive touch is touched
            touch = touch + 1
            if (touch > 2):
                print 'motor touched, waiting...'
                gpio.output(sh.mLeft, False)
                gpio.output(sh.mRight, False)
                prev = 0
        else:
            touch = 0
            if sh.values[wi_channel] > _target:
                print(col.yel + 'tar: ' + col.none + str(_target) + col.yel + '  cur: ' + col.none  + str(sh.values[0]) + col.gre + ' ---o>>' + col.none)
                if prev == 1:
                    pass
                else:
                    gpio.output(sh.mLeft, True)
                    gpio.output(sh.mRight, False)
                    prev = 1
            if sh.values[wi_channel] < _target:
                print(col.yel +'tar: '+ col.none + str(_target) + col.yel +'  cur: '+ col.none + str(sh.values[0]) + col.red + ' <<o---' + col.none)
                if prev == 2:
                    pass
                else:
                    prev = 2
                    gpio.output(sh.mLeft, False)
                    gpio.output(sh.mRight, True)
            #time.sleep(1)
        readValues()
    # turn of motor and print location
    gpio.output(sh.mLeft, False)
    gpio.output(sh.mRight, False)
    readValues()
    print 'motor move complete: '
    print 'position: ' + str(sh.values[0])

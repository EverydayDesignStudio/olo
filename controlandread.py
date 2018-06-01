"""
#     CONTROL AND READ TEST
# ==============================================================
#      ---   Exploring metadata as a design material   ---
# ==============================================================


"""
#              _____
#  ______________  /____  _________
#  __  ___/  _ \  __/  / / /__  __ \
#  _(__  )/  __/ /_ / /_/ /__  /_/ /
#  /____/ \___/\__/ \__,_/ _  .___/
#  ========================/_/====
import time
import RPi.GPIO as gpio
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import csv
import sh
sh.init()
from oloFunctions import *


resolution = int(raw_input('res? '))
wi_channel = 4 # channel on MCP3008 the swiper is attached to
currentsublist = ''
currenttrack = ''
move = False

class col:
    prp = '\033[95m'
    vio = '\033[94m'
    gre = '\033[92m'
    yel = '\033[93m'
    ora = '\033[91m'
    none = '\033[0m'
    red = '\033[1m'
    und = '\033[4m'

def segment(_pos):
    segsize = 1024 / resolution
    seg = _pos / segsize
    return seg


# Initialise pins
gpio.setup(sh.mEnable, gpio.OUT) #gpio 6  - motor driver enable
gpio.setup(sh.mLeft, gpio.OUT) #gpio 13 - motor driver direction 1
gpio.setup(sh.mRight, gpio.OUT) #gpio 12 - motor driver direction 2

gpio.setup(sh.switch1, gpio.IN) #gpio 16  - three pole switch 1
gpio.setup(sh.switch2, gpio.IN) #gpio 18  - three pole switch 2

gpio.output(sh.mEnable, True) # Enable motor driver

# turn off other outputs:
gpio.output(sh.mLeft, False)
gpio.output(sh.mRight, False)


#  ______
#  ___  /___________________
#  __  /_  __ \  __ \__  __ \
#  _  / / /_/ / /_/ /_  /_/ /
#  /_/  \____/\____/_  .___/
# ===================/_/===

while(True):
    readValues() # Read all the ADC values
    #print('pos: ' + str(sh.values[wi_channel]))

    if timeframe() is 0: # if the timeframe changed
        path = 'tracks/' + sh.timeframe + '/' # update path
        move = True
        currentsublist = path + 'sl_' + sh.timeframe + '_' + str(seg) + '.txt'

    if seg is not segment(sh.values[wi_channel]): #if the segment changed
        seg = segment(sh.values[wi_channel])
        print 'seg: ' + str(seg)
        currentsublist = path + 'sl_' + sh.timeframe + '_' + str(seg) + '.txt'

    if currentsublist is not '':
        with open(currentsublist, 'r') as sl:
            reader = csv.reader(sl, delimiter='\t')
            currenttrack = reader.next()
            print(currenttrack)

    #if the timeframe has changed and the slider has to move
    if move:
        timestamp = currenttrack[0] # get the timestamp
        #based on the timeframe, get a target position from the songs timestamp
        if sh.timeframe == 'life':
            pass
            # dont know how to efficiently get this position back
        if sh.timeframe == 'year':
            pass
            # dont know how to efficiently get this position back
        if sh.timeframe == 'day':
            pass
            # dont know how to efficiently get this position back

    # target = int(raw_input(col.vio + "where to, captain? " + col.none))
    # if target < 0:
    #     readValues()
    #     print sh.values[wi_channel]
    # else:
    #     # move slider to target position
    #     moveslider(target)

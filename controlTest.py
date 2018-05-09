"""
#             _           _   _____       _
#  __ ___ _ _| |_ _ _ ___| | |_   _|__ __| |_
# / _/ _ \ ' \  _| '_/ _ \ |   | |/ -_|_-<  _|
# \__\___/_||_\__|_| \___/_|   |_|\___/__/\__|
#
# ==============================================================
#      ---   Exploring metadata as a design material   ---
# ==============================================================


# because slider value drops to zero when capacitive touch is active,
# the slider thinks it is at '0' position, which can disturb the program
# if the 0 position is actually the target.
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
import sh
sh.init()
from oloFunctions import *
wi_channel = 5 # channel on MCP3008 the swiper is attached to


class col:
    prp = '\033[95m'
    vio = '\033[94m'
    gre = '\033[92m'
    yel = '\033[93m'
    ora = '\033[91m'
    none = '\033[0m'
    red = '\033[1m'
    und = '\033[4m'

def moveslider(_target):
    prev = '<>'
    sh.values = readValues()
    while (abs(sh.values[wi_channel] - _target) > 5):
        #print('motor loop')
        if (sh.values[1] > 1): # if capacitive touch is touched
            print 'motor touched, waiting...'
            gpio.output(sh.mLeft, False)
            gpio.output(sh.mRight, False)
            prev = 0
        else:
            if sh.values[0] > _target:
                print(col.yel + 'tar: ' + col.none + str(_target) + col.yel + '  cur: ' + col.none  + str(sh.values[0]) + col.gre + ' ---o>>' + col.none)
                if prev == 1:
                    pass
                else:
                    gpio.output(sh.mLeft, True)
                    gpio.output(sh.mRight, False)
                    prev = 1
            if sh.values[0] < _target:
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
    # Read all the ADC channel values in a list.
    readValues()

    #values[6] = gpio.input(16)
    #values[7] = gpio.input(18)
    # Print the ADC values.
    print('pos: ' + str(sh.values[0]))
    target = int(raw_input(col.vio + "where to, captain? " + col.none))
    if target < 0:
        readValues()
        print sh.values[0]
    else:


        # move slider to target position
        moveslider(target)

"""
#             _           _   _____       _
#  __ ___ _ _| |_ _ _ ___| | |_   _|__ __| |_
# / _/ _ \ ' \  _| '_/ _ \ |   | |/ -_|_-<  _|
# \__\___/_||_\__|_| \___/_|   |_|\___/__/\__|
#
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
#import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import sh
sh.init()
from oloFunctions import *
slider_ch = 7 # channel on MCP3008 the swiper is attached to
touch_ch = 6

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
    touch = 0
    sh.values = readValues()
    while (abs(sh.values[slider_ch] - _target) > 5):
        #print('motor loop')
        if (sh.values[touch_ch] > 1): # if capacitive touch is touched
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
            if sh.values[slider_ch] > _target:
                print(col.yel + 'tar: ' + col.none + str(_target) + col.yel + '  cur: ' + col.none  + str(sh.values[slider_ch]) + col.gre + ' ---o>>' + col.none)
                if prev == 1:
                    pass
                else:
                    gpio.output(sh.mLeft, True)
                    gpio.output(sh.mRight, False)
                    prev = 1
            if sh.values[slider_ch] < _target:
                print(col.yel +'tar: '+ col.none + str(_target) + col.yel +'  cur: '+ col.none + str(sh.values[slider_ch]) + col.red + ' <<o---' + col.none)
                if prev == 2:
                    pass
                else:
                    prev = 2
                    gpio.output(sh.mLeft, False)
                    gpio.output(sh.mRight, True)
            #time.sleep(1)
        readValues()
    # turn off motor and print location
    gpio.output(sh.mLeft, False)
    gpio.output(sh.mRight, False)
    readValues()
    print 'motor move complete: '
    print 'position: ' + str(sh.values[0])



# Initialise pins
gpio.setup(sh.mEnable, gpio.OUT) #gpio 6  - motor driver enable
gpio.setup(sh.mLeft, gpio.OUT) #gpio 13 - motor driver direction 1
gpio.setup(sh.mRight, gpio.OUT) #gpio 12 - motor driver direction 2

leftpwm = gpio.PWM(sh.mLeft, 10)
rightpwm = gpio.PWM(sh.mRight, 10)

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
    print('pos: ' + str(sh.values[slider_ch]))
    target = int(raw_input(col.vio + "where to, captain? " + col.none))
    if target < 0:
        readValues()
        print sh.values[slider_ch]
    if target > 2000:
        for dc in range(0, 101, 1):      # Loop from 0 to 100 stepping dc up by 5 each loop
            leftpwm.ChangeDutyCycle(dc)
            time.sleep(0.05)               # wait for .05 seconds at current LED brightness level
            print(dc)
    else:
        # move slider to target position
        moveslider(target)

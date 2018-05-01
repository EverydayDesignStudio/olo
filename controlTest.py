"""
#        _                       _ _
#   ___ | | ___    _ __ __ _  __| (_) ___
#  / _ \| |/ _ \  | '__/ _` |/ _` | |/ _ \
# | (_) | | (_) | | | | (_| | (_| | | (_) |
#  \___/|_|\___/  |_|  \__,_|\__,_|_|\___/
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
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import sh
sh.init()
from oloFunctions import *

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

    target = int(raw_input("where to, captain? "))
    prev = '<>'
    sh.values = readValues()

    # move slider to target position
    while (abs(sh.values[0] - target) > 20):
        #print('motor loop')
        if (sh.values[1] > 1):
            print 'motor touched, waiting...'
            gpio.output(sh.mLeft, False)
            gpio.output(sh.mRight, False)
        else:
            if sh.values[0] > target:
                print('tar: ' + str(target) + '  cur: ' + str(sh.values[0]) + ' ---o>>')
                if prev == '>>>':
                    pass
                else:
                    gpio.output(sh.mLeft, True)
                    gpio.output(sh.mRight, False)
                    prev = '>>>'
            if sh.values[0] < target:
                print('tar: ' + str(target) + '  cur: ' + str(sh.values[0]) + ' <<o---')
                if prev == '<<<':
                    pass
                else:
                    prev = '<<<'
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

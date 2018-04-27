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

Tickets
- check board mode, redo pin number if necessary
- slider speed, investigate proper pwm method
-
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
from oloFunctions import *

# Initialise pins
mEnable = 6
mLeft = 13
mRight = 12
gpio.setup(mEnable, gpio.OUT) #gpio 6  - motor driver enable
gpio.setup(mLeft, gpio.OUT) #gpio 13 - motor driver direction 1
gpio.setup(12, gpio.OUT) #gpio 12 - motor driver direction 2

gpio.setup(17, gpio.IN) #gpio 16  - three pole switch 1
gpio.setup(18, gpio.IN) #gpio 18  - three pole switch 2

gpio.output(mEnable, True) # Enable motor driver

# turn off other outputs:
gpio.output(mLeft, False)
gpio.output(mRight, False)


#  ______
#  ___  /___________________
#  __  /_  __ \  __ \__  __ \
#  _  / / /_/ / /_/ /_  /_/ /
#  /_/  \____/\____/_  .___/
# ===================/_/===

while(True):
    # Read all the ADC channel values in a list.
    values = readValues()

    #values[6] = gpio.input(16)
    #values[7] = gpio.input(18)
    # Print the ADC values.
    printValues(values)

    target = int(raw_input("where to, captain? "))
    prev = '<>'
    values = readValues()

    # move slider to target position
    while (abs(values[0] - target) > 5):
        print('motor loop')
        print('target: ' + str(target) + '  current: ' + str(values[0]))
        print ('difference:' + str(abs(values[0] - target)))
        if (values[1] == 1):
            print 'motor touched, waiting...'
            gpio.output(mLeft, False)
            gpio.output(mRight, False)
        else:
            if values[0] > target:
                print('>>>  >>  >')
                if prev == '>>>':
                    pass
                else:
                    gpio.output(mLeft, True)
                    gpio.output(mRight, False)
                    prev = '>>>'
            if values[0] < target:
                print('<  <<  <<<')
                if prev == '<<<':
                    pass
                else:
                    prev = '<<<'
                    gpio.output(mLeft, False)
                    gpio.output(mRight, True)
            #time.sleep(1)
        values = readValues()
    # turn of motor and print location
    gpio.output(mLeft, False)
    gpio.output(mRight, False)
    values = readValues()
    print 'motor move complete: '
    print 'position: ' + str(values[0])

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

from oloFunctions import *


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



# GPIO configuration:
#gpio.setmode(gpio.BOARD)

# check board mode -> correct gpio pin numbers
print 'BOARD MODE IS: ' + str(gpio.getmode())
print '========================='
time.sleep(4)

gpio.setup(6, gpio.OUT) #gpio 6  - motor driver enable
gpio.setup(13, gpio.OUT) #gpio 13 - motor driver direction 1
gpio.setup(12, gpio.OUT) #gpio 12 - motor driver direction 2

gpio.setup(16, gpio.IN) #gpio 16  - three pole switch 1
gpio.setup(18, gpio.IN) #gpio 18  - three pole switch 2



gpio.output(6, True) # Enable motor driver

# turn off other outputs:
gpio.output(13, False)
gpio.output(12, False)

"""
print('Reading MCP3008 values, press Ctrl-C to quit...')
# Print nice channel column headers.
print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*range(8)))
print('-' * 57)
"""



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
        if values[0] > target:
            print('>>>')
            if prev == '>>>':
                pass
            else:
                gpio.output(13, True)
                gpio.output(12, False)
                prev = '>>>'
        if values[0] < target:
            print('<<<')
            if prev == '<<<':
                pass
            else:
                prev = '<<<'
                gpio.output(13, False)
                gpio.output(12, True)
        #time.sleep(1)
        values = readValues()
    # turn of motor and print location
    print 'motor move complete: '
    print 'position: ' + str(values[0]) + '  disabling motor...'
    gpio.output(13, False)
    gpio.output(12, False)
    values = readValues()
    print 'motor move complete: '
    print 'position: ' + str(values[0])

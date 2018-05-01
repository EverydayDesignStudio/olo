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
- try reading values from MCP without other GPIO pins configured

"""
#from oloFunctions import *
#              _____
#  ______________  /____  _________
#  __  ___/  _ \  __/  / / /__  __ \
#  _(__  )/  __/ /_ / /_/ /__  /_/ /
#  /____/ \___/\__/ \__,_/ _  .___/
#  ========================/_/====

import sh
sh.init()
import time
import RPi.GPIO as gpio
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from oloFunctions import *

def exectime(then):
    now = time.time()
    extime = now - then
    return "{0:.2f}".format(round(extime,7))

print sh.CLK
mcp = Adafruit_MCP3008.MCP3008(clk=sh.CLK, cs=sh.CS, miso=sh.MISO, mosi=sh.MOSI)

# GPIO configuration:
gpio.setup(sh.switch1, gpio.IN) #gpio 16  - three pole switch 1
gpio.setup(sh.switch2, gpio.IN) #gpio 18  - three pole switch 2

print('Reading MCP3008 values, press Ctrl-C to quit...')

#  ______
#  ___  /___________________
#  __  /_  __ \  __ \__  __ \
#  _  / / /_/ / /_/ /_  /_/ /
#  /_/  \____/\____/_  .___/
# ===================/_/===

while(True):
    # Read all the ADC channel values in a list.
    then = time.time()
    readValues()
    print('readvals exec time: ' + str(exectime(then)))
    # Print the ADC values.
    then = time.time()
    printValues(sh.values)
    print('printvals exec time: ' + str(exectime(then)))
    """
    print('=' * 57)
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*range(8)))
    print('-' * 57)
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*values))
    """
    # Pause for half a second.
    #time.sleep(0.5)

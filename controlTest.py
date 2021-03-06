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
import sh
sh.init()
import oloFunctions as olo

import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import RPi.GPIO as gpio

class col:
    prp = '\033[95m'
    vio = '\033[94m'
    gre = '\033[92m'
    yel = '\033[93m'
    ora = '\033[91m'
    none = '\033[0m'
    red = '\033[1m'
    und = '\033[4m'


# Initialise pins
gpio.setmode(gpio.BCM)
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
    try:
        # Read all the ADC channel values in a list.
        olo.readValues()

        #values[6] = gpio.input(16)
        #values[7] = gpio.input(18)
        # Print the ADC values.
        print('pos: ' + str(sh.values[sh.slider_ch]))
        target = int(input(col.vio + "where to, captain? " + col.none))
        if target < 0:
            olo.readValues()
            print (sh.values[sh.slider_ch])
        else:
            if target == 5000:
                for i in range(20):
                    print (sh.values[sh.slider_ch])
                    olo.hardstop()
                    olo.readValues()
            else:
                # move slider to target position
                olo.moveslider(target)
    except KeyboardInterrupt:
        print("@@ Keyboard Interrupt - exiting the test..")
        olo.hardstop()
        exit();

#   .----. .-.    .----.
#  /  {}  \| |   /  {}  \
#  \      /| `--.\      /
#   `----' `----' `----'
#  .----.   .--.  .----. .-. .----.
#  | {}  } / {} \ | {}  \| |/  {}  \
#  | .-. \/  /\  \|     /| |\      /
#  `-' `-'`-'  `-'`----' `-' `----'
# ==================================
# script to check motor-fader function
# by Henry & Tal


import RPi.GPIO as gpio
import time
import sh
sh.init()
import oloFunctions as olo
import Adafruit_MCP3008
count = 0
mode = 1

gpio.cleanup()
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

#while(True):


print('start')
while(True):

    print('16: ' + str( gpio.input(16)) + ' 18: ' + str( gpio.input(18)) )
    if mode:
        distance = 1000 - olo.readValues()[7]
        print distance
    else:
        print('lol')



    # if(gpio.input(16)):
    #     print('16')
    #     gpio.output(32, True)
    #     gpio.output(33, False)
    # elif(gpio.input(18)):
    #     print('18')
    #     gpio.output(33, True)
    #     gpio.output(32, False)
    # else:
    #     print '32 high'
    #     for i in range(100):
    #         gpio.output(32, True)
    #         time.sleep(0.01)
    #         gpio.output(32, False)
    #         time.sleep(0.01)
    #     gpio.output(32, True)
    #     time.sleep(0.1)
    #     gpio.output(32, False)
    #     time.sleep(0.1)
    #     gpio.output(33, True)
    #     print '33 high'
    #     time.sleep(0.1)
    #     gpio.output(33, False)
    #     time.sleep(0.1)
"""
for t in range(2):
    for p in range(2):
        gpio.output(32, True)
        time.sleep(0.5)
        gpio.output(32, False)
        time.sleep(1)
        gpio.output(33, True)
        time.sleep(0.5)
        gpio.output(33, False)
        time.sleep(1)

print('done')
gpio.output(33, False)
"""

#gpio.cleanup()


def leftover():
    gpio.output(33, True)
    time.sleep(0.1)
    gpio.output(33, False)
    time.sleep(1)
    gpio.output(32, True)
    time.sleep(1)
    gpio.output(32, False)
    time.sleep(1)

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

count = 0
mode = 1
gpio.cleanup()
gpio.setmode(gpio.BOARD)

gpio.setup(31, gpio.OUT) #gpio 6
gpio.setup(33, gpio.OUT) #gpio 13
gpio.setup(32, gpio.OUT) #gpio 12

gpio.setup(16, gpio.IN) #gpio 12
gpio.setup(18, gpio.IN) #gpio 12

# Enable motor driver
gpio.output(31, True)

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

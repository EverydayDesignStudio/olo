import time
import RPi.GPIO as gpio
gpio.setmode(gpio.BOARD)
gpio.setup(37, gpio.IN)

while(True):
    print(gpio.input(37))
    time.sleep(0.4)
    print('-')

import time
import RPi.GPIO as gpio
gpio.setmode(gpio.BOARD)
gpio.setup(26, gpio.IN)

while(True):
    print(gpio.input(26))
    time.sleep(0.4)
    print('-')

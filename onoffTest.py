import RPi.GPIO as gpio
import time

gpio.setmode(gpio.BCM)
gpio.setup(17, gpio.IN, pull_up_down=gpio.PUD_DOWN)

while True:
    print(gpio.input(17))
    time.sleep(0.5)

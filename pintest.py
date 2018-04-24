import time
import RPi.GPIO as gpio

gpio.setup(26, gpio.IN) #gpio 16  - three pole switch 1

while(True):
    print(gpio.input(26))
    time.sleep(0.4)
    print('-')

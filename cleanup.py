import RPi.GPIO as gpio

gpio.setmode(gpio.BOARD)

gpio.setup(31, gpio.OUT) #gpio 6  - motor driver enable 
gpio.setup(33, gpio.OUT) #gpio 13 - motor driver direction 1
gpio.setup(32, gpio.OUT) #gpio 12 - motor driver direction 2
gpio.output(32, False)
gpio.output(33, False)
gpio.cleanup()


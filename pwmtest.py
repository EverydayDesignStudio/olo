import time
import RPi.GPIO as gpio
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from oloFunctions import *
from RPIO import PWM

# Initialise pins
mEnable = 6
mLeft = 13
mRight = 12
gpio.setup(mEnable, gpio.OUT) #gpio 6  - motor driver enable
gpio.setup(mLeft, gpio.OUT) #gpio 13 - motor driver direction 1
gpio.setup(12, gpio.OUT) #gpio 12 - motor driver direction 2

gpio.output(mEnable, True) # Enable motor driver

# turn off other outputs:
gpio.output(mLeft, False)
gpio.output(mRight, False)

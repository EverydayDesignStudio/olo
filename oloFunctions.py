import Adafruit_MCP3008
import RPi.GPIO as gpio
import time
import sh

# Software SPI configuration:
mcp = Adafruit_MCP3008.MCP3008(clk=sh.CLK, cs=sh.CS, miso=sh.MISO, mosi=sh.MOSI)

gpio.setup(17, gpio.IN) #gpio 16  - three pole switch 1
gpio.setup(18, gpio.IN) #gpio 18  - three pole switch 2


def readValues():
    # Read all the ADC channel values in a list.
    sh.values = [0]*8
    for i in range(7):
        # The read_adc function will get the value of the specified channel (0-7).
        sh.values[i] = mcp.read_adc_difference(i)
        # values[2] = gpio.input(sh.switch1) #when 3pole switch <--> GPIO 23
        # values[3] = gpio.input(sh.switch2) #when 3pole switch <--> GPIO 24
    return sh.values


def printValues(vals):
    print('=' * 29)
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} |'.format(*sh.labels))
    #print('-' * 29)
    newVals = [0] * 4
    for i in range(4):
        newVals[i] = vals[i]
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} |'.format(*newVals))
    # Pause for half a second.
    time.sleep(0.5)

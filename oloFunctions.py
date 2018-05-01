import Adafruit_MCP3008
import RPi.GPIO as gpio
import time

# Software SPI configuration:
CLK  = 11
MISO = 9
MOSI = 10
CS   = 8
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

gpio.setup(17, gpio.IN) #gpio 16  - three pole switch 1
gpio.setup(18, gpio.IN) #gpio 18  - three pole switch 2


def readValues():
    # Read all the ADC channel values in a list.
    values = [0]*8
    for i in range(5):
        # The read_adc function will get the value of the specified channel (0-7).
        values[i] = mcp.read_adc_difference(i)
        #print('3pole 0: ' + str(gpio.input(17)))
        #print('3pole 1: ' + str(gpio.input(18)))
    return values


def printValues(vals):
    labels = ['swi', 'cap', 'sw1', 'sw2']
    print('=' * 57)
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} |'.format(*labels))
    print('-' * 57)
    newVals = [0] * 4
    for i in range(4):
        newVals[i] = vals[i]
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} |'.format(*newVals))
    # Pause for half a second.
    time.sleep(0.5)

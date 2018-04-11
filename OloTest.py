#  _____________ _______   ________       _____________
#  __  __ \__  / __  __ \  ___  __ \_____ ______  /__(_)_____
#  _  / / /_  /  _  / / /  __  /_/ /  __ `/  __  /__  /_  __ \
#  / /_/ /_  /___/ /_/ /   _  _, _// /_/ // /_/ / _  / / /_/ /
#  \____/ /_____/\____/    /_/ |_| \__,_/ \__,_/  /_/  \____/
#
# ==============================================================
#      ---   Exploring metadata as a design material   ---
#
# Code by Tal Amram
# HEY HENRY HOWS IT GOING
# HEY HEY HEY

#              _____
#  ______________  /____  _________
#  __  ___/  _ \  __/  / / /__  __ \
#  _(__  )/  __/ /_ / /_/ /__  /_/ /
#  /____/ \___/\__/ \__,_/ _  .___/
#  ========================/_/====
import time

# Import Raspberry pi GPIO library
import RPi.GPIO as gpio


# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

# Software SPI configuration:
CLK  = 11
MISO = 9
MOSI = 10
CS   = 8
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

gpio.setup(31, gpio.OUT) #gpio 6  - motor driver enable
gpio.setup(33, gpio.OUT) #gpio 13 - motor driver direction 1
gpio.setup(32, gpio.OUT) #gpio 12 - motor driver direction 2

gpio.setup(16, gpio.IN) #gpio 16  - three pole switch 1
gpio.setup(18, gpio.IN) #gpio 18  - three pole switch 2

# Enable motor driver
gpio.output(31, True)
gpio.output(32, False)
gpio.output(33, False)


print('Reading MCP3008 values, press Ctrl-C to quit...')
# Print nice channel column headers.
print('| {p:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*range(8)))
print('-' * 57)




#  ______
#  ___  /___________________
#  __  /_  __ \  __ \__  __ \
#  _  / / /_/ / /_/ /_  /_/ /
#  /_/  \____/\____/_  .___/
#                   /_/

while(True):
    # Read all the ADC channel values in a list.
    values = [0]*8
    for i in range(5):
        # The read_adc function will get the value of the specified channel (0-7).
        values[i] = mcp.read_adc_difference(i)
    values[6] = gpio.input(16)
    values[7] = gpio.input(18)
    # Print the ADC values.
    print('-' * 57)
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*range(8)))
    print('-' * 57)
    print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*values))
    # Pause for half a second.
    time.sleep(0.5)

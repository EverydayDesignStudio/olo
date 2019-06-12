try: # try importing libraries that only run locally on RPi. While testing on desktop, these are not available nor required.
    # import Adafruit_MCP3008
    import busio
    import digitalio
    import board
    import adafruit_mcp3xxx.mcp3008 as MCP
    from adafruit_mcp3xxx.analog_in import AnalogIn
    import RPi.GPIO as gpio

except:
    pass
import time
import sh
import datetime
import math

class col:
    prp = '\033[95m'
    vio = '\033[94m'
    gre = '\033[92m'
    yel = '\033[93m'
    ora = '\033[91m'
    none = '\033[0m'
    red = '\033[1m'
    und = '\033[4m'

current_milli_time = lambda: int(round(time.time() * 1000))

# Software SPI configuration:
try:
    # mcp = Adafruit_MCP3008.MCP3008(clk = sh.CLK, cs = sh.CS, miso = sh.MISO, mosi = sh.MOSI)
    # gpio.setup(17, gpio.IN) #gpio 17  - three pole switch 1
    # gpio.setup(18, gpio.IN) #gpio 18  - three pole switch 2

    # create the spi bus
    spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

    # create the cs (chip select)
    if (sh.CS == 8):
        cs = digitalio.DigitalInOut(board.D8)
    else:
        cs = digitalio.DigitalInOut(board.D5)

    # create the mcp object
    mcp = MCP.MCP3008(spi, cs)
except:
    pass

def linearlizeVolume(vol):
    a = -96.7
    b = 138.1224

    try:
        res = round(a + b*math.log(vol))
    except ValueError:
        return vol

    if (res < 0):
        return vol
    else:
        return res

def convertTimestamp(tstamp):
    _dt = datetime.datetime.fromtimestamp(int(tstamp))
    return _dt

def yearTimestamp(tstamp):
    tstamp = int(tstamp)
    year = datetime.datetime.fromtimestamp(tstamp).strftime('%Y')
    _yt = int(time.mktime(time.strptime(year, '%Y')))# epoch time of Jan 1st 00:00 of the year of the song
    _dt = datetime.datetime.fromtimestamp(int(tstamp - _yt))
    return _dt, int(tstamp - _yt)

def dayTimestamp(tstamp):
    tstamp = int(tstamp)
    pattern = '%Y %m %d'
    day = datetime.datetime.fromtimestamp(tstamp).strftime(pattern)
    _dayt = int(time.mktime(time.strptime(day + ' 00 : 00 : 00', pattern + ' %H : %M : %S' ))) # epoch time since beginning of the day
    _dt = datetime.datetime.fromtimestamp(int(tstamp - _dayt + (25200))) # account for time zone
    return _dt, int(tstamp - _dayt + 0) #(25200))


def timeframe():
    # function that updates sh.timeframe
    def checksame():
        if sh.timeframe == sh.prevtimeframe:
            return 1
        else:
            return 0
    sh.prevtimeframe = sh.timeframe
    # (sh.values[1], sh.values[2])
    if sh.values[1] < 10:
        if sh.values[2] < 10:
            if (sh.OLO_ID == 2):
                # Day: (0, 0) - 0
                sh.timeframe = "day"
            else:
                ### OLO 1, 3, 4, 5, 6
                # Life: (0, 0) - 0
                sh.timeframe = 'year'
                
            if sh.timeframe == sh.prevtimeframe:
                return 1
            else:
                return 0
        else:
            if (sh.OLO_ID == 2):
                # Life: (0, 1) - 1
                sh.timeframe = 'life'
            else:
                ### OLO 1, 3, 4, 5, 6
                # Day: (0, 1) - 1
                sh.timeframe = 'day'

            if sh.timeframe == sh.prevtimeframe:
                return 1
            else:
                return 0
    else:
        if sh.values[2] < 10:
            if (sh.OLO_ID == 2):
                # Year: (1, 0) - 2
                sh.timeframe = 'year'
            else:
                # Year: (1, 0) - 2
                sh.timeframe = 'life'

            if sh.timeframe == sh.prevtimeframe:
                return 1
            else:
                return 0
        else:
            # (1, 1)
            sh.timeframe = 'err'
            return -1
    sh.timeframe = 'unkn'
    return -2

def readValues():
    # Read all the ADC channel values in a list.
    sh.values = [0]*8

    # The read_adc function will get the value of the specified channel (0-7).
    ch0 = AnalogIn(mcp, MCP.P0, MCP.P1)
    ch1 = AnalogIn(mcp, MCP.P1, MCP.P0)
    ch2 = AnalogIn(mcp, MCP.P2, MCP.P3)
    ch3 = AnalogIn(mcp, MCP.P3, MCP.P2)
    ch4 = AnalogIn(mcp, MCP.P4, MCP.P5)
    ch5 = AnalogIn(mcp, MCP.P5, MCP.P4)
    ch6 = AnalogIn(mcp, MCP.P6, MCP.P7)
    ch7 = AnalogIn(mcp, MCP.P7, MCP.P6)

    # shift values down by 6 bits
    # https://github.com/adafruit/Adafruit_CircuitPython_MCP3xxx/issues/12
    sh.values[0] = ch0.value >> 6
    sh.values[1] = ch1.value >> 6
    sh.values[2] = ch2.value >> 6
    sh.values[3] = ch3.value >> 6
    sh.values[4] = ch4.value >> 6
    sh.values[5] = ch5.value >> 6
    sh.values[6] = ch6.value >> 6
    sh.values[7] = ch7.value >> 6

    return sh.values


def printValues(vals):
    # Function that prints the values from all 8 channels of the ADC to screen
    newVals = [0] * 8
    for i in range(8):
        newVals[i] = vals[i]
    print(newVals[0])
    # Pause for half a second.
    #time.sleep(0.5)


def moveslider(_target):
    # Function that moves the slider to a specified position (0 - 1024)
    touch = 0
    errormargin = 7 # makes the width of 14 which is close to the slowest movement
    slowrange = 70

    prevPos = -1
    holdCount = 0;
    stuckTimestamp = None
    dist = -1;
    prev = 0;
    duty = 0;

    if (_target >= 0 and _target <= 1024):
        while (distance(_target) > errormargin):

            if (abs(prevPos - sh.values[sh.slider_ch]) > int(1024*0.01)):
                prevPos = sh.values[sh.slider_ch]
                holdCount = 0
                stuckCount = 0
                stuckTimestamp = None
            else:
                holdCount += 1

            # if the slider is wandering within the 1% range of the position for 7 counts
            # stop both motors and give up
            if (holdCount > 7):
                hardstop()
                readValues()
                return -1;

            # if capacitive touch is touched
            if (sh.values[sh.touch_ch] > 1):
                print ('motor touched, waiting...')
                hardstop()
                if (stuckTimestamp is None):
                    stuckTimestamp = current_milli_time()
                # the slider got stuck for more than 5 secs
                elif (current_milli_time() - stuckTimestamp > 10000):
                    readValues()
                    return -2;
            else:
                if (dist < 0):
                    dist = distance(_target)
                    print("## distance left: {}".format(dist))
                else:
                    prev = dist
                    dist = distance(_target)
                    print("## distance left: {}., {} units moved".format(dist, (prev - dist)))

                # calculate duty according to the distance Left
                # value is estimated by a best-fit curve, y = 1764.5*x^2 + 2932.05*x - 34.8.
                if (dist < 8):
                    duty = 0.005
                elif (dist > 1000):
                    duty = 0.274
                elif (dist > 900):
                    duty = 0.248
                elif (dist > 800):
                    duty = 0.221
                elif (dist > 700):
                    duty = 0.194
                elif (dist > 600):
                    duty = 0.166
                elif (dist > 500):
                    duty = 0.137
                elif (dist > 400):
                    duty = 0.1073
                elif (dist > 300):
                    duty = 0.0766
                elif (dist > 200):
                    duty = 0.05
                elif (dist > 100):
                    duty = 0.03
                else:
                    duty = 0.01

                # to the Left
                if sh.values[sh.slider_ch] > _target:
                    print(col.yel + 'tar: ' + col.none + str(_target) + col.yel + '  cur: ' + col.none  + str(sh.values[sh.slider_ch]) + col.vio + ' <<o-  ' + col.none)
                    gpio.output(sh.mLeft, True)
                    time.sleep(duty)
                    gpio.output(sh.mLeft, False)
                # to the Right
                else:
                    print(col.yel + 'tar: ' + col.none + str(_target) + col.yel + '  cur: ' + col.none  + str(sh.values[sh.slider_ch]) + col.ora + '   -o>>' + col.none)
                    gpio.output(sh.mRight, True)
                    time.sleep(duty)
                    gpio.output(sh.mRight, False)
            readValues()

        # turn off motor and print location
        hardstop()
        readValues()
        print ('motor move complete: ')
        print ('position: ' + str(sh.values[sh.slider_ch]))
    else:
        print ('[moveSlider] improper value given!')

    return 0;


def hardstop():
    # Function to stop the slider from moving
    for t in range(5):
        gpio.output(sh.mLeft, True)
        gpio.output(sh.mRight, True)
    gpio.output(sh.mLeft, False)
    gpio.output(sh.mRight, False)
    print('hard stop')


def distance(_target):
    # Function to calculate the distance between the current position of the slider knob
    # and an inputted value '_target'
    readValues()
    return abs(sh.values[sh.slider_ch] - _target)

# oloGlobals

def init():
    # pin configuration
    global switch1 = 23
    global switch2 = 24
    global mEnable = 6
    global mLeft = 12
    global mRight = 13

    # Software SPI configuration:
    global CLK  = 11
    global MISO = 9
    global MOSI = 10
    global CS   = 8

    # pretty labels
    global labels = ['swi', 'cap', 'sw1', 'sw2']

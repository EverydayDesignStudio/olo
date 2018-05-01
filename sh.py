# oloGlobals

def init():
    # pin configuration
    global switch1
    switch1 = 23
    global switch2
    switch2 = 24
    global mEnable
    mEnable = 6
    global mLeft
    mLeft = 12
    global mRight
    mRight = 13

    # Software SPI configuration:
    global CLK  = 11
    global MISO = 9
    global MOSI = 10
    global CS   = 8

    # Pretty labels
    global labels = ['swi', 'cap', 'sw1', 'sw2']

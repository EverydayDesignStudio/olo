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
    global CLK
    CLK  = 11
    global MISO
    MISO = 9
    global MOSI
    MOSI = 10
    global CS
    CS   = 8

    global values
    
    # Pretty labels
    global labels
    labels = ['swi', 'cap', 'sw1', 'sw2']

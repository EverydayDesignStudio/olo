def init():
    # pin configuration
    global slider_ch
    slider_ch = 7 # channel on MCP3008 the slider is attached to
    global touch_ch
    touch_ch = 6 # channel on MCP3008 the touch signal is attached to
    global switch1
    switch1 = 23
    global switch2
    switch2 = 24
    global mEnable
    mEnable = 6
    global mLeft
    mLeft = 13
    global mRight
    mRight = 12
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
    global timeframe
    timeframe = ''
    global prevtimeframe
    prevtimeframe = ''
    # Pretty labels
    global labels
    labels = ['swi', 'cap', 'sw1', 'sw2']

    ## TODO: Update DB name and Last FM Username for deployment
    global dbname
    # dbname = "sample"
    dbname = "doenjaoogjes"
    global lastFM_username
    lastFM_username = "doenjaoogjes"
    # lastFM_username = "yoomy1203"

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

    global spotify_scope
    spotify_scope = 'user-modify-playback-state'
    global spotify_client_id
    spotify_client_id = '86456db5c5364110aa9372794e146bf9'
    global spotify_client_secret
    spotify_client_secret = 'cd7177a48c3b4ea2a6139b88c1ca87f5'
    global spotify_redirect_uri
    spotify_redirect_uri = 'https://example.com/callback/'
    global PYLAST_API_KEY
    PYLAST_API_KEY = 'e38cc7822bd7476fe4083e36ee69748e'

    ## TODO: change this accordingly to match to a correct spotify account for each OLO
    global spotify_username
    spotify_username = "9mgcb91qlhdu2kh4nwj83p165"
    global device_oloradio1
    device_oloradio1 = '98bb0735e28656bac098d927d410c3138a4b5bca'

    ## TODO: Update DB name and Last FM Username for deployment
    global dbname
    # dbname = "sample"
    dbname = "doenjaoogjes"
    global lastFM_username
    # lastFM_username = "yoomy1203"
    lastFM_username = "doenjaoogjes"

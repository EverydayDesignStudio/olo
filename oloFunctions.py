def readValues():
    # Read all the ADC channel values in a list.
    values = [0]*8
    for i in range(5):
        # The read_adc function will get the value of the specified channel (0-7).
        values[i] = mcp.read_adc_difference(i)
    return values

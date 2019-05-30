import RPi.GPIO as gpio

ipt = None;
pin = None;
state = None;
gpio.setmode(gpio.BCM)

# gpio.setup(17, gpio.IN, pull_up_down=gpio.PUD_DOWN)
gpio.output(12, gpio.HIGH)
gpio.output(12, gpio.LOW)

while(True):
    try:
        # Print the ADC values.
        print("Current GPIO: {}, ")
        ipt = int(input("Mode: BCM. Enter GPIO number [0, 27] or set the current GPIO to [high] or [low]: "))
        if (ipt >= 0 and ipt <= 27):
            print("@@ Turning off GPIO {}..".format(pin))
            pin = ipt
            gpio.cleanup()
            gpio.setup(pin, gpio.OUT)
            print("@@ GPIO {} is not set to OUT".format(pin))

        else:
            print("@@ Value error; out of range. [1, 29]")
    except ValueError:
        if (pin is not None and ipt is 'high'):
            gpio.output(pin, gpio.HIGH)
            print("@@ GPIO {} is now HIGH".format(pin))
        elif (pin is not None and ipt is 'low'):
            gpio.output(pin, gpio.LOW)
            print("@@ GPIO {} is now LOW".format(pin))
        else:
            print("@@ Value error! Must enter either 'high' or 'low'.")

    except KeyboardInterrupt:
        print("@@ Keyboard Interrupt - exiting the test..")
        gpio.cleanup()
        exit();

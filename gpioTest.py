import RPi.GPIO as gpio

val = None;
pin = None;
state = None;
gpio.setmode(gpio.BCM)

# gpio.setup(17, gpio.IN, pull_up_down=gpio.PUD_DOWN)
# gpio.output(12, gpio.HIGH)
# gpio.output(12, gpio.LOW)

while(True):
    try:
        val = input("\nMode: BCM. Enter GPIO number [0, 27] or set the current GPIO to [high] or [low]: ")
        isdigit()
        if (isdigit(val)):
            # Print the ADC values.
            print("Current GPIO: {}, state: {}".format(pin, state))
            pin_no = int(val)
            if (pin_no >= 0 and pin_no <= 27):
                if (pin is not None):
                    print("@@ Switching GPIO {} -> {}".format(pin, pin_no))

                pin = pin_no

                gpio.setup(pin, gpio.OUT)
                print("@@ GPIO {} is now set to OUT".format(pin))

            else:
                print("@@ Value error; out of range. [1, 29]")
        else:
            if (pin is not None and val is 'high'):
                state = 'high'
                gpio.output(pin, gpio.HIGH)
                print("@@ GPIO {} is now HIGH".format(pin))
            elif (pin is not None and val is 'low'):
                state = 'low'
                gpio.output(pin, gpio.LOW)
                print("@@ GPIO {} is now LOW".format(pin))
            else:
                print("@@ Value error! Must enter either 'high' or 'low'.")

    except KeyboardInterrupt:
        print("@@ Keyboard Interrupt - exiting the test..")
        gpio.cleanup()
        exit();

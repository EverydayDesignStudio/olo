import RPi.GPIO as gpio
import time
import oloMain as olo
import sh
sh.init()

current_milli_time = lambda: int(round(time.time() * 1000))

def main():
    gpio.setmode(gpio.BCM)
    gpio.setup(sh.onoff, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    countdownToShutdown = None

    while True:
        isOn = gpio.input(sh.onoff)
        try:

            if (not isOn):
                if (countdownToShutdown is None):
                    countdownToShutdown = current_milli_time()
                # if OLO is off for 3 minutes, quit the oloMain script
                if (current_milli_time() - countdownToShutdown > 10000): # 3 minutes in milliseconds: 180000
                    olo.stop()
            else:
                countdownToShutdown = None
                olo.main()

        # restart the script on exception
        except:
            python = sys.executable
            os.execl(python, python, * sys.argv)

if __name__ == "__main__": main()

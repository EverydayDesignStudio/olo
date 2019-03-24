Follow these instructions to setup a new OLO prototype:

## Format SD Card
Follow instructions [HERE](https://www.raspberrypi.org/documentation/installation/sdxc_formatting.md).


## Install OS
Choose one of two links below to install Raspbian OS. Set id/pw to `pi/oloradio`. You can change the password directly in Raspberry Pi configuration settings: `sudo raspi-config`.
 
* [NOOBS installer](https://www.raspberrypi.org/downloads/noobs/)

* [Raspbian-Lite released by HiFiBerry](https://www.hifiberry.com/build/download/)
	* Default id/pw is `pi/raspberry`, [change the password](https://vicpimakers.ca/tutorials/raspbian/change-the-raspbian-root-password/) to: `pi/oloradio`


## Install GUI (Raspbian Lite Only)
First, run `sudo df -h` to check the volume of the root partition. If it's less than 16.0 G, resize the partition volume. Follow the guide in the [EverydayDesignStudio's guide](https://github.com/EverydayDesignStudio/guides/blob/master/raspberry-advanced.md).

Once you confirm that you have enough space for the root partition, follow the article to [installing GUI on Raspbian Lite](https://www.raspberrypi.org/forums/viewtopic.php?t=133691). It will guide you through setting time zones, locales, keyboard settings and packages for GUI.

GUI is required for OLO to retrieve an authentication token for the Spotify Web API. 


## Set Alias

1. Open `sudo nano ~/.bashrc`
2. Add the following on the bottom:```alias python=python3```


## Create a Script
```TBA... ```
[temp](https://howchoo.com/g/mwnlytk3zmm/how-to-add-a-power-button-to-your-raspberry-pi)


## Download Source Code
`cd ~/Desktop | git clone https://github.com/EverydayDesignStudio/olo.git`

* If you get an error because you have not set up the Git or Github, see [Git guide](https://everydaydesignstudio.github.io/guides/git-github.html)


## Install Packages
Fresh Raspbian OS will have Python2, Python3 and Git installed by default


### Libraries

1. Update apt-get, Pi and Python

 `sudo apt-get update`

 `sudo apt-get install build-essential python-pip python3-pip python-dev git`
 
 `sudo apt-get install python-smbus`

 `sudo apt-get upgrade`

 `sudo pip3 install --upgrade setuptools`
 (if this doesn't work, try `sudo apt-get install python3-pip`)

2. Enable **[I2C](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c)** and **[SPI](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-spi)** channels

3. Install **Circuitpython Adafruit libraries**

 GPIO: `sudo pip3 install RPI.GPIO`

 Adafruit Blinka: `sudo pip3 install adafruit-blinka`

 Adafruit [MCP3008](https://learn.adafruit.com/mcp3008-spi-adc/python-circuitpython): `sudo pip3 install adafruit-circuitpython-mcp3xxx`

4. Packages for the back-end code

 * [sqlite3](https://www.tutorialspoint.com/sqlite/sqlite_installation.htm):
`sudo apt-get install sqlite3`

 * [raspotify](https://github.com/dtcooper/raspotify): `curl -sL https://dtcooper.github.io/raspotify/install.sh | sh`
 Need to [modify the config]((https://github.com/dtcooper/raspotify#Configuration)) and restart raspotify
						`sudo systemctl restart raspotify`

 * [spotipy](https://github.com/plamere/spotipy):
 `sudo python3 -m pip install spotipy`
`sudo python3 -m pip install git+https://github.com/plamere/spotipy.git --upgrade`

 * [pylast](https://github.com/pylast/pylast):
  `sudo python3 -m pip install pylast`


## Configure [Hifiberry](https://www.hifiberry.com/)
Follow the instructions [HERE](https://www.hifiberry.com/build/documentation/configuring-linux-3-18-x/).
Use "DAC+ standard/pro".

In `/boot/config.txt`,
> dtoverlay=hifiberry-dacplus


## Enable ssh for the remote control
- Top left menu > Config > check "Enable SSH"

- OR, run the following command:
 `sudo systemctl enable ssh | sudo systemctl start ssh`


## (Optional) Enable VNC
`sudo raspi-config` > "5. Interfacing options" > check "Enable VNC"

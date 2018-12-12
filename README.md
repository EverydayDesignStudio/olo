Setting up a new OLO prototype:

	1. Format SD Card
		https://www.raspberrypi.org/documentation/installation/sdxc_formatting.md

	2. Install OS
		* Set the password to be "oloradio"

		https://www.raspberrypi.org/downloads/noobs/

	3. Set the alias
		open "sudo nano ~/.bashrc"
		add the following on the bottom:
			alias python=python3
			echo Running on boot
			sudo python /home/pi/Desktop/olo/main.py

	4. Download codes from the git repo
		cd Desktop
		git clone https://github.com/EverydayDesignStudio/olo.git

	5. Install packages
		* Fresh Raspbian OS will have Python2, Python3 and Git installed

		a. Libraries

			1) Update apt-get
				- sudo apt-get update
				- sudo apt-get install build-essential python-pip python-dev python-smbus git

			2) Install Adafruit libraries
				- Adafruit GPIO (https://github.com/adafruit/Adafruit_Python_GPIO)
				- Adafruit MCP3008 (https://learn.adafruit.com/raspberry-pi-analog-to-digital-converters/mcp3008)
					
			3) Packages for the back-end code
				- sqlite3 
					sudo apt-get install sqlite3

				- raspotify	
					https://github.com/dtcooper/raspotify

					* need to change config file and re-start raspotify
						(https://github.com/dtcooper/raspotify#Configuration)

				- spotipy
					sudo python3 -m pip install spotipy
					sudo python3 -m pip install git+https://github.com/plamere/spotipy.git --upgrade

				- pylast 
					sudo python3 -m pip install pylast

	6. Configure Hifiberry
		https://support.hifiberry.com/hc/en-us/articles/205377651-Configuring-Linux-4-x-or-higher
		* use "DAC+ standard/pro"
			> dtoverlay=hifiberry-dacplus

	7. Enable ssh for the remote control
		- top left menu > config > enable SSH	
		- run the following two commands
			sudo systemctl enable ssh
			sudo systemctl start ssh

	8. (Optional) Enable VNC
		sudo raspi-config > 5 Interfacing options > Enable VNC


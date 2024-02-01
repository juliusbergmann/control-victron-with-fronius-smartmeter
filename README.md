# control-victron-with-fronius-smartmeter

This is made to run a battery storage with a victron inverter with an existing Fronius Smartmeter.
The value of the Fronius Smartmeter is read over the local network via Modbus TCP from the datamanager of the inverter.
The value is then used to control the victron inverter in mode 3.

everything can be run as a script on a machine (e.g. raspberrypi) in the local network.

## Installation
To use it, just change the IP-Addresses of the Fronius inverter and the Victron inverter in the param_init.py file.
Then run the script main.py on your machine.


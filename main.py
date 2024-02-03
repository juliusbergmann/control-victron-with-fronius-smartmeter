#!/usr/bin/env python3
# done by Julius Bergmann
# 24/03/2023

from read_fronius import read_power_from_fronius
from victron_mode3 import write_power_to_victron
import time
import datetime
import os
import my_logging
from my_logging import controller_logger
from param_init import CONTROL_INTERVALL, MAX_CHARGE_POWER, MAX_DISCHARGE_POWER
import tasmota_control
from tasmota_control import TasmotaDevice, MQTTClient

pool_pump_power = 275 #W
pool_pump_min_runtime = 5 * 60 #s
pool_heatpump_power = 840 #W
pool_heatpump_min_runtime = 10 * 60 #s

# init
power_root = 0
used_power_in_house = 0
current_set_point = 0
power_pool = 0
power_house = 0
power_house_and_pool = 0

def control_battery(current_set_point, power_root):
    # set the power that should be written to battery
    current_set_point -= power_root
    if current_set_point > MAX_CHARGE_POWER:
        controller_logger.info(f"current set point is at max {MAX_CHARGE_POWER}")
        current_set_point = MAX_CHARGE_POWER
    elif current_set_point < -MAX_DISCHARGE_POWER:
        controller_logger.info(f"current set point is at min {-MAX_DISCHARGE_POWER}")
        current_set_point = -MAX_DISCHARGE_POWER

    power_battery, battery_soc = write_power_to_victron(current_set_point)
    # TODO catch case, if write was not accomplished

    return power_battery, battery_soc

if __name__ == "__main__":
    # initialize the tasmota devices
    mqtt_client = MQTTClient("192.168.178.30", 1883, "mqtt-user", "mqtt-user")
    mqtt_client.client.on_message = mqtt_client.on_message

    pool_heatpump = TasmotaDevice("pool_heatpump", mqtt_client, pool_heatpump_power, pool_heatpump_min_runtime)
    pool_pump = TasmotaDevice("pool_pump", mqtt_client, pool_pump_power, pool_pump_min_runtime)

    # initialize the devices
    pool_heatpump.turn_off()
    pool_pump.turn_off()

    while True:
        # TODO: unsauber, weil intern auch 1 sekundenschleife ist (wenn es nicht verbindet)
        power_root, read_accomplished = read_power_from_fronius()
        

        if read_accomplished:
            # Data from fronius could be read
            power_battery, battery_soc = control_battery(current_set_point, power_root)
        else:
            # Data from fronius could not be read
            controller_logger.error("data from fronius could not be read: power setpoint not written")
        
        power_house = power_root - power_battery - power_pool
        controller_logger.info(f"power_root: {power_root:.2f}")
        controller_logger.info(f"power_battery: {power_battery:.2f}")
        controller_logger.info(f"power_pool: {power_pool:.2f}")
        controller_logger.info(f"power_house: {power_house:.2f}")

        # TODO: integrate this value over the min_runtime so that short peaks are not considered
        power_house_and_pool = power_root - power_battery

        if power_house_and_pool < 0:
            # there is power available in the house

            # check if pumps are on
            if not pool_pump.status_power_on:
                if power_house_and_pool + pool_pump.power <= 0:
                    # if poolpump turns on, there is still enough power in the house
                    pool_pump.turn_on()
                    # TODO: this does not work, if the pump won't turn on (because of min_runtime)
                    #power_pool += pool_pump.power
                else:
                    controller_logger.info(f"not enough power to turn on pool pump. power available: {power_house_and_pool:.2f}")
            else:
                controller_logger.info("pool pump is already on")
                if not pool_heatpump.status_power_on:
                    if power_house_and_pool + pool_heatpump.power <= 0:
                        # if poolheatpump turns on, there is still enough power in the house
                        pool_heatpump.turn_on()
                        #power_pool += pool_heatpump.power
                    else:
                        controller_logger.info(f"not enough power to turn on pool heatpump. power available: {power_house_and_pool:.2f}")
                else:
                    controller_logger.info("pool heatpump is already on")
        else:
            # there is no power available in the house
            if pool_heatpump.status_power_on:
                pool_heatpump.turn_off()
                #power_pool -= pool_heatpump.power
            else:
                controller_logger.info("pool heatpump is already off")
                if pool_pump.status_power_on:
                    pool_pump.turn_off()
                    #power_pool -= pool_pump.power
                else:
                    controller_logger.info("pool pump is already off")

        time.sleep(CONTROL_INTERVALL)       

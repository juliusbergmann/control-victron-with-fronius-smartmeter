#!/usr/bin/env python3

from read_fronius import read_power_from_fronius
from victron_mode3 import write_power_to_victron
import time
import datetime
import os
import my_logging
from my_logging import logger
from param_init import CONTROL_INTERVALL, MAX_CHARGE_POWER, MAX_DISCHARGE_POWER

# init
current_power_at_root = 0
used_power_in_house = 0
current_set_point = 0

if __name__ == "__main__":
    while True:
        # TODO: unsauber, weil intern auch 1 sekundenschleife ist (wenn es nicht verbindet)
        current_power_at_root, read_accomplished = read_power_from_fronius()
        if read_accomplished:
            # Data from fronius could be read

            # set the power that should be written to battery
            current_set_point -= current_power_at_root
            if current_set_point > MAX_CHARGE_POWER:
                logger.info(f"current set point is at max {MAX_CHARGE_POWER}")
                current_set_point = MAX_CHARGE_POWER
            elif current_set_point < -MAX_DISCHARGE_POWER:
                logger.info(f"current set point is at min {-MAX_DISCHARGE_POWER}")
                current_set_point = -MAX_DISCHARGE_POWER

            write_power_to_victron(current_set_point)
            # TODO catch case, if write was not accomplished
        else:
            # Data from fronius could not be read
            logger.error("data from fronius could not be read: power setpoint not written")
        time.sleep(CONTROL_INTERVALL)
            

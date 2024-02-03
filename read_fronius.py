#!/bin/python
# done by Julius Bergmann
# 08/03/2023

from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
import numpy as np
import time
from my_logging import fronius_logger
from param_init import FRONIUS_IP_ADDRESS, RECONNECT_INTERVAL

FRONIUS_PORT = 502

def ensure_connection(client):
    while not client.connect():
        SERVER_IP = client.host
        SERVER_PORT = client.port
        fronius_logger.warning(f"Unable to connect to the Modbus server at {SERVER_IP}:{SERVER_PORT}. Retrying...")
        time.sleep(RECONNECT_INTERVAL)
    return True

def read_power_from_fronius():
    read_accomplished = True

    # Verbindung zum Modbus-TCP-Slave-Gerät herstellen
    client = ModbusTcpClient(FRONIUS_IP_ADDRESS, port=FRONIUS_PORT)
    
    try:
        ensure_connection(client)
        # Geräte ID vom Smartmeter ist 240 laut Fronius Modbus TCP Doku Seite 49
        geraete_id = 240
        # 40098 und 4099 sind laut Meter_Register_Map die Register in denen die aktuelle Leistung drinnen steht
        start_adress = 40098
        # Register aus dem Slave-Gerät auslesen
        registers_data = client.read_holding_registers(address=start_adress-1, count=2, slave=geraete_id)
        # convert data in registers to float
        decoder = BinaryPayloadDecoder.fromRegisters(registers_data.registers, byteorder=Endian.Big)
        result = decoder.decode_32bit_float()

        # Verbindung zum Slave-Gerät trennen
        client.close()

        # Ergebnisse anzeigen
        #logger.info(f"the power that goes into the house is {round(result, 2)} Watt")
    except Exception as e:
        fronius_logger.error(f"Error while reading fronius: {e}")
        read_accomplished = False
        result = 0
    return result, read_accomplished

if __name__ == "__main__":
    read_power_from_fronius()
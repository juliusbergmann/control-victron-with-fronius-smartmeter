import time
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from my_logging import victron_logger
from param_init import VICTRON_IP_ADDRESS, RECONNECT_INTERVAL

# Configuration
VICTRON_PORT = 502
# Victron Setpoint Register Address
SETPOINT_REGISTER_ADDRESS = 37
SETPOINT_GERAETE_ID = 228

BATTERY_REGISTER_ADDRESS = 840
BATTERY_GERAETE_ID = 100

def ensure_connection(client):
    """
    Ensure that the client is connected to the Modbus server.
    If not, try to connect.
    :param client: Modbus client

    :return: True if connection is established, False otherwise
    """

    # TODO: implement timeout
    try:
        while not client.connect():
            victron_logger.warning(f"Unable to connect to the Modbus server at {VICTRON_IP_ADDRESS}:{VICTRON_PORT}. Retrying...")
            time.sleep(RECONNECT_INTERVAL)

        state = True
    except ModbusException as e:
        victron_logger.error(f"Modbus exception occurred: {e}")
        client.close()
        state = False
    except Exception as e:
        victron_logger.error(f"Unexpected exception occurred: {e}")
        client.close()
        state = False
    
    return state


def print_current_settings(registers_data):
    #print("Enables/Disables charge (0=enabled, 1=disabled):", registers_data.registers[1])
    #print("Enables/Disables feedback (0=enabled, 1=disabled):", registers_data.registers[2])
    #print("power setpoint:", registers_data.registers[0])
    #print("power L2 setpoint:", registers_data.registers[3])
    #print("power L3 setpoint:", registers_data.registers[4])
    victron_logger.info(f"current power setpoint: {registers_data.registers[0]}")


def write_power_to_victron(power):

    # Create Modbus client
    client = ModbusTcpClient(VICTRON_IP_ADDRESS, port=VICTRON_PORT)

    try:
        # Ensure connection is active before writing
        ensure_connection(client)
        victron_logger.info(f"Connected to the Modbus server at {VICTRON_IP_ADDRESS}:{VICTRON_PORT}")

        # TODO remove this (only for debugging)
        # read setpoint registers from victron
        setpoint_data = client.read_holding_registers(address=SETPOINT_REGISTER_ADDRESS, count=5, slave=SETPOINT_GERAETE_ID)
        if setpoint_data.isError():
            # TODO: handle error?
            victron_logger.error(f"Modbus Error while reading: {setpoint_data}")
        else:
            print_current_settings(setpoint_data)

        battery_data = client.read_holding_registers(address=BATTERY_REGISTER_ADDRESS, count=7, slave=BATTERY_GERAETE_ID)
        if battery_data.isError():
            victron_logger.error(f"Modbus Error while reading: {battery_data}")
            battery_power = 0
            battery_soc = 0
        else:
            victron_logger.info(f"current battery power: {battery_data.registers[2]} W")
            victron_logger.info(f"current battery soc: {battery_data.registers[3]} %")
            battery_power = battery_data.registers[2]
            battery_soc = battery_data.registers[3]

        
        # convert power to int16
        value = int(power)
        if 0 > value > -32768:
            value = 65536 + value
        elif value < 32767:
            value = value
        else:
            victron_logger.error("Power is not in range of int16!")
            value = 0

        # write data into the victron power setpoint register
        result = client.write_register(address=SETPOINT_REGISTER_ADDRESS, value=value, slave=SETPOINT_GERAETE_ID)

        if not result.isError():
            victron_logger.info(f"Successfully wrote value {value} to register {SETPOINT_REGISTER_ADDRESS}")
        else:
            victron_logger.error(f"Error writing value {value} to register {SETPOINT_REGISTER_ADDRESS}")
        
    except KeyboardInterrupt:
        victron_logger.info("Keyboard interrupt received.")
    except ModbusException as e:
        victron_logger.error(f"Modbus exception occurred: {e}")
    except Exception as e:
        victron_logger.error(f"Unexpected exception occurred: {e}")
    finally:
        victron_logger.info("Closing connection to the Modbus server")
        client.close()    
    
    return battery_power, battery_soc

if __name__ == "__main__":
    # Get power value from user
    print("Type in chargepower in W:")
    power = input()
    
    write_power_to_victron(power)

import time
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from my_logging import logger
from param_init import VICTRON_IP_ADDRESS, RECONNECT_INTERVAL

# Configuration
VICTRON_PORT = 502
REGISTER_ADDRESS = 37
GERAETE_ID = 228

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
            logger.warning(f"Unable to connect to the Modbus server at {VICTRON_IP_ADDRESS}:{VICTRON_PORT}. Retrying...")
            time.sleep(RECONNECT_INTERVAL)

        state = True
    except ModbusException as e:
        logger.error(f"Modbus exception occurred: {e}")
        client.close()
        state = False
    except Exception as e:
        logger.error(f"Unexpected exception occurred: {e}")
        client.close()
        state = False
    
    return state


def print_current_settings(registers_data):
    #print("Enables/Disables charge (0=enabled, 1=disabled):", registers_data.registers[1])
    #print("Enables/Disables feedback (0=enabled, 1=disabled):", registers_data.registers[2])
    #print("power setpoint:", registers_data.registers[0])
    #print("power L2 setpoint:", registers_data.registers[3])
    #print("power L3 setpoint:", registers_data.registers[4])
    logger.info(f"power setpoint: {registers_data.registers[0]}")


def write_power_to_victron(power):

    # Create Modbus client
    client = ModbusTcpClient(VICTRON_IP_ADDRESS, port=VICTRON_PORT)

    try:
        # Ensure connection is active before writing
        ensure_connection(client)
        logger.info(f"Connected to the Modbus server at {VICTRON_IP_ADDRESS}:{VICTRON_PORT}")

        # TODO remove this (only for debugging)
        # read register before writing
        registers_data = client.read_holding_registers(address=REGISTER_ADDRESS, count=5, slave=GERAETE_ID)

        if registers_data.isError():
            # TODO: handle error?
            logger.error(f"Modbus Error: {registers_data}")
        else:
            print_current_settings(registers_data)


        # convert power to int16
        value = int(power)
        if 0 > value > -32768:
            value = 65536 + value
        elif value < 32767:
            value = value
        else:
            logger.error("Power is not in range of int16!")
            value = 0

        # write data into the victron power setpoint register
        result = client.write_register(address=REGISTER_ADDRESS, value=value, slave=GERAETE_ID)

        if not result.isError():
            logger.info(f"Successfully wrote value {value} to register {REGISTER_ADDRESS}")
        else:
            logger.error(f"Error writing value {value} to register {REGISTER_ADDRESS}")
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    except ModbusException as e:
        logger.error(f"Modbus exception occurred: {e}")
    except Exception as e:
        logger.error(f"Unexpected exception occurred: {e}")
    finally:
        logger.info("Closing connection to the Modbus server")
        client.close()    

if __name__ == "__main__":
    # Get power value from user
    print("Type in chargepower in W:")
    power = input()
    
    write_power_to_victron(power)

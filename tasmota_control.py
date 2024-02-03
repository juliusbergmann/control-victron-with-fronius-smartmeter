import paho.mqtt.client as mqtt
import time
import threading
from my_logging import mqtt_logger

class MQTTClient:
    def __init__(self, broker, port, username, password):
        self.client = mqtt.Client()
        self.client.username_pw_set(username, password)
        self.client.connect(broker, port, 60)
        self.client.loop_start()
        self.sensors = []

    def on_message(self, client, userdata, message):
        mqtt_logger.info(f"Received message: {message.payload.decode()} on topic {message.topic}")
        for sensor in self.sensors:
            if message.topic == f"stat/{sensor.name}/POWER":
                if message.payload.decode() == "ON":
                    sensor.status_power_on = True
                    mqtt_logger.info(f"{sensor.name} is set to ON")
                elif message.payload.decode() == "OFF":
                    sensor.status_power_on = False
                    mqtt_logger.info(f"{sensor.name} is set to OFF")
                else:
                    mqtt_logger.error(f"Unknown message: {message.payload.decode()} on topic {message.topic}")

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def publish(self, topic, message):
        self.client.publish(topic, message, retain=True)

class TasmotaDevice:
    def __init__(self, name, mqtt_client, power, min_runtime):
        self.name = name
        self.mqtt_client = mqtt_client
        mqtt_client.sensors.append(self)
        self.mqtt_client.subscribe(f"stat/{self.name}/POWER")
        
        self.status_power_on = None
        self.power = power # in W
        self.min_runtime = min_runtime # in s
        self.last_status_change = time.time()

    def turn_on(self):
        if self.status_power_on == False:
            current_time = time.time()
            if current_time - self.last_status_change > self.min_runtime:
                self.mqtt_client.publish(f"cmnd/{self.name}/Power1", "ON")
                self.last_status_change = current_time
                mqtt_logger.info(f"{self.name} turned on")
            else:
                mqtt_logger.warning(f"{self.name} cannot be turned on yet. Minimum runtime not reached.")
        else:
            mqtt_logger.info(f"{self.name} is already on")

    def turn_off(self):
        if self.status_power_on == True:
            current_time = time.time()
            if current_time - self.last_status_change > self.min_runtime:
                self.mqtt_client.publish(f"cmnd/{self.name}/Power1", "OFF")
                self.last_status_change = current_time
                mqtt_logger.info(f"{self.name} turned off")
            else:
                mqtt_logger.warning(f"{self.name} cannot be turned off yet. Minimum runtime not reached.")
        else:
            mqtt_logger.info(f"{self.name} is already off")

if __name__ == "__main__":
    mqtt_client = MQTTClient("192.168.178.30", 1883, "mqtt-user", "mqtt-user")
    mqtt_client.client.on_message = mqtt_client.on_message

    pool_heatpump = TasmotaDevice("pool_heatpump", mqtt_client)
    pool_pump = TasmotaDevice("pool_pump", mqtt_client)

    def control_device(device, on_time, off_time):
        while True:
            device.turn_on()
            time.sleep(on_time)
            device.turn_off()
            time.sleep(off_time)

    threading.Thread(target=control_device, args=(pool_heatpump, 30, 30)).start()
    threading.Thread(target=control_device, args=(pool_pump, 30, 30)).start()
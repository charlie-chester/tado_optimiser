import logging
import requests
import json


class HomeAssistantAPI:
    def __init__(self, token):
        self.token = token
        self.ha_url = "http://supervisor/core/api/services/mqtt/publish"
        self.mqtt_topic = "homeassistant/sensor/tado_temperature/config"
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def update_entity(self, sensor_config):
        discovery_message = {
            "topic": self.mqtt_topic,
            "payload": json.dumps(sensor_config),
            "retain": True}

        response = requests.post(self.ha_url, headers=self.headers, json=discovery_message)
        logging.info(msg=f"Status code: {response.status_code}")

        if response.status_code == 200:
            logging.info(msg="MQTT discovery message sent successfully")
        else:
            logging.info(msg=f"Failed to send MQTT discovery message: {response.status_code}, {response.text}")

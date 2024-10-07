import logging
import time
import requests
import json

class HomeAssistantAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = "http://homeassistant.local:8123/api/states/"
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def wait_for_ha_startup(self):
        pass

    def update_entity(self, sensor, payload):
        fullUrl = f"{self.base_url}{sensor}"
        data = requests.post(fullUrl, headers=self.headers, json=payload)

        logging.info(msg=f"Status code: {data.status_code}")

        if data.status_code == 201:
            logging.info(msg=f"New entity successfully created: {sensor}")
        elif data.status_code == 200:
            logging.info(msg=f"Entity successfully updated: {sensor}")
        else:
            logging.error(msg=f"Error updating entity: {sensor}")
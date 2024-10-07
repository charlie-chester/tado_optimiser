import logging

import requests


class HomeAssistantAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = "http://homeassistant.local:8123/api/states/"
        self.headers = headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def update_entity(self, sensor, payload):
        fullUrl = f"{self.base_url}{sensor}"
        data = requests.post(fullUrl, headers=self.headers, json=payload)

        logging.info(msg=f"Status code: {data.status_code}")

        if data.status_code == 201:
            logging.info(msg=f"Entity updated: {sensor}")
        else:
            logging.error(msg=f"Error updating entity: {sensor}")

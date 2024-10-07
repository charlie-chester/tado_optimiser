import logging
import requests
import os


class HomeAssistantAPI:
    def __init__(self,):
        self.token = os.getenv("$SUPERVISOR_TOKEN")
        self.base_url = "http://homeassistant.local:8123"
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def update_entity(self, sensor, payload):
        fullUrl = f"{self.base_url}/api/states/{sensor}"
        data = requests.post(fullUrl, headers=self.headers, json=payload)

        logging.info(msg=f"Status code: {data.status_code}")

        if data.status_code == 201:
            logging.info(msg=f"New entity successfully created: {sensor}")
        elif data.status_code == 200:
            logging.info(msg=f"Entity successfully updated: {sensor}")
        else:
            logging.error(msg=f"Error updating entity: {sensor}")

import logging
import requests
import os


class HomeAssistantAPI:
    def __init__(self,):
        self.token = os.getenv("SUPERVISOR_TOKEN")
        self.base_url = "http://supervisor/core/api/states/"
        self.supervisor_url = "http://supervisor/core/api/"
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def is_ha_running(self):
        response = requests.get(self.supervisor_url, headers=self.headers)
        data = response.json()
        state = data.get("state")
        logging.info(msg=f"Home Assistant state: {state}")
        return state == "running"

    def update_entity(self, sensor, payload):
        logging.info(msg=f"Updating entity: {sensor}")
        fullUrl = f"{self.base_url}{sensor}"
        response = requests.post(fullUrl, headers=self.headers, json=payload)
        logging.info(msg=f"Status code: {response.status_code}")

        if response.status_code == 201:
            logging.info(msg=f"New entity successfully created: {sensor}")
        elif response.status_code == 200:
            logging.info(msg=f"Entity successfully updated: {sensor}")
        else:
            logging.error(msg=f"Error updating entity: {sensor}")

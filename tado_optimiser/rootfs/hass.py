import logging
import requests
import os


class HomeAssistantAPI:
    def __init__(self,):
        self.token = os.getenv("SUPERVISOR_TOKEN")
        self.base_url = "http://supervisor/core/api/states/"
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def update_entity(self, sensor, payload):
        logging.debug(msg=f"Updating entity: {sensor}")
        fullUrl = f"{self.base_url}{sensor}"
        response = requests.post(fullUrl, headers=self.headers, json=payload)
        logging.debug(msg=f"Status code: {response.status_code}")

        if response.status_code == 201:
            logging.debug(msg=f"New entity successfully created: {sensor}")
        elif response.status_code == 200:
            logging.debug(msg=f"Entity successfully updated: {sensor}")
        else:
            logging.error(msg=f"Error updating entity: {sensor}")

    def get_entity_state(self, sensor):
        fullUrl = f"{self.base_url}{sensor}"
        response = requests.get(fullUrl, headers=self.headers)
        return response.json()["state"]

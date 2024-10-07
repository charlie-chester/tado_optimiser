import logging
import time
import requests
import json


class HomeAssistantAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = "http://homeassistant.local:8123"
        self.api_endpoint = "/api/states"
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def wait_for_ha_startup(self, poll_interval=5):
        while not self._is_ha_fully_started():
            logging.info(f"Waiting for {poll_interval} seconds before checking again...")
            time.sleep(poll_interval)
        logging.info("Home Assistant is fully started.")

    def _is_ha_fully_started(self):
        try:
            response = requests.get(f"{self.base_url}{self.api_endpoint}", headers=self.headers)
            response.raise_for_status()
            states = response.json()

            # Log state entities for debugging
            logging.debug(f"State entities received: {json.dumps(states, indent=2)}")

            # Check if the states contain a specific entity, which indicates HA is fully started
            if states and any(state['entity_id'] == 'homeassistant' for state in states):
                return True
            else:
                logging.info("Home Assistant is not fully started yet.")
                return False
        except requests.exceptions.RequestException as e:
            logging.error(f"Error checking Home Assistant state: {e}")
            return False

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

import logging
import time
import requests
import os


class HomeAssistantAPI:
    def __init__(self,):
        self.token = os.getenv("SUPERVISOR_TOKEN")
        self.base_url = "http://supervisor/core/api/states/"
        self.supervisor_url = "http://supervisor/core/api/"
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def is_home_assistant_running(self):
        try:
            response = requests.get(self.supervisor_url, headers=self.headers)
            response.raise_for_status()  # Raise an error for bad status codes
            data = response.json()
            logging.debug(f"Supervisor API response: {data}")
            message = data.get("message")
            logging.debug(f"Home Assistant message: {message}")
            return message == "API running."
        except requests.RequestException as e:
            logging.error(f"Error querying Home Assistant state: {e}")
            return False

    def wait_for_home_assistant(self):
        while not self.is_home_assistant_running():
            logging.info("Waiting for Home Assistant to start...")
            time.sleep(5)  # Check every 5 seconds
        logging.info("Home Assistant is running. Proceeding with entity updates.")

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

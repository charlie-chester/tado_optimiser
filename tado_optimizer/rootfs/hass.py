import logging
import time
import requests


class HomeAssistantAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = "http://homeassistant.local:8123/api/states/"
        self.headers = headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def wait_for_ha_startup(self):
        logging.info("Checking that Home Assistant to started...")
        while True:
            try:
                data = requests.get(self.base_url, headers=self.headers)
                if data.status_code == 200:
                    logging.info("Home Assistant started event received.")
                    break
                else:
                    logging.info(f"Waiting for Home Assistant to start. Status code: {data.status_code}")
            except Exception as e:
                logging.error(f"Error waiting for Home Assistant to start: {e}")
            time.sleep(10)

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

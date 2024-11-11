import logging
import os
import requests

logger = logging.getLogger("tado_optimiser")


# noinspection DuplicatedCode
class HomeAssistantAPI:
    def __init__(self,):
        self.token = os.getenv("SUPERVISOR_TOKEN")
        self.base_url = "http://supervisor/core/api"
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def update_entity(self, sensor, payload):
        logger.debug(msg=f"Updating entity: {sensor}")
        full_url = f"{self.base_url}/states/{sensor}"
        response = requests.post(full_url, headers=self.headers, json=payload)
        logger.debug(msg=f"Status code: {response.status_code}")

        if response.status_code == 201:
            logger.debug(msg=f"New entity successfully created: {sensor}")
        elif response.status_code == 200:
            logger.debug(msg=f"Entity successfully updated: {sensor}")
        else:
            logger.error(msg=f"Error updating entity: {sensor}")

    def get_entity_state(self, sensor):
        full_url = f"{self.base_url}/states/{sensor}"
        response = requests.get(full_url, headers=self.headers)

        if response.status_code == 200:
            logger.debug(msg=f"Entity found: {sensor}")
            state = response.json()["state"]
            return state
        else:
            logger.error(msg=f"Error getting entity: {sensor}")
            return "Entity not found"

    def set_hvac_mode(self, entity_id, hvac_mode):
        full_url = f"{self.base_url}/services/climate/set_hvac_mode"
        payload = {"entity_id": entity_id, "hvac_mode": hvac_mode}
        response = requests.post(full_url, headers=self.headers, json=payload)
        logger.debug(msg=f"Status code: {response.status_code}")

        if response.status_code == 200:
            logger.debug(msg=f"HVAC mode set to '{hvac_mode}' for entity: {entity_id}")
        else:
            logger.debug(msg=f"Failed to set HVAC mode to '{hvac_mode}' for entity: {entity_id}")

    def set_temperature(self, entity_id, temperature):
        full_url = f"{self.base_url}/services/climate/set_temperature"
        payload = {"entity_id": entity_id, "temperature": temperature}
        response = requests.post(full_url, headers=self.headers, json=payload)
        logger.debug(msg=f"Status code: {response.status_code}")

        if response.status_code == 200:
            logger.debug(msg=f"Temperature set to '{temperature}' for entity: {entity_id}")
        else:
            logger.debug(msg=f"Failed to set temperature to '{temperature}' for entity: {entity_id}")

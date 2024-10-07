import logging
import time
import requests
import asyncio
import json
import websockets

class HomeAssistantAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = "http://homeassistant.local:8123/api/states/"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    async def _listen_for_ha_started(self):
        ws_url = "ws://homeassistant.local:8123/api/websocket"
        try:
            async with websockets.connect(ws_url) as websocket:
                # Send authentication message
                auth_message = {
                    "type": "auth",
                    "access_token": self.token
                }
                await websocket.send(json.dumps(auth_message))

                response = await websocket.recv()
                data = json.loads(response)

                logging.info(msg=f"Data get: {data.get('type')}")

                if data.get("type") == "auth_ok":
                    logging.info("Authenticated successfully.")

                    # Listen for events
                    while True:
                        message = await websocket.recv()
                        event_data = json.loads(message)

                        if event_data.get("type") == "event" and event_data["event"]["event_type"] == "homeassistant_started":
                            logging.info("Home Assistant has started.")
                            break
                else:
                    logging.error("Authentication failed.")
        except Exception as e:
            logging.error(f"Error connecting to WebSocket: {e}")

    def wait_for_ha_startup(self):
        # Run the WebSocket listener
        logging.info(msg="Checking that Home Assistant has started...")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._listen_for_ha_started())
        logging.info(msg="Home Assistant is ready.")

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
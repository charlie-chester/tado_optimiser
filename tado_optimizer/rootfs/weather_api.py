import logging
import requests
from datetime import datetime
from hass import HomeAssistantAPI

hass = HomeAssistantAPI()

class WeatherAPI:
    def __init__(self, open_weather_api_key, latitude, longitude):
        self.base_url = "https://api.openweathermap.org/data/3.0/onecall?"
        self.api_key = open_weather_api_key
        self.latitude = latitude
        self.longitude = longitude
        self.weather_data = {}

    def get_weather_data(self):
        fullUrl = f"{self.base_url}lat={self.latitude}&lon={self.longitude}&appid={self.api_key}&units=metric"
        self.weather_data = requests.get(fullUrl).json()
        status = self.weather_data.status_code
        logging.info(msg="Getting weather data")
        logging.debug(msg=f"Get weather data fullUrl: {fullUrl}")
        logging.info(msg=f"Weather API status code: {status}")

    def sample_update(self):
        now = datetime.now().strftime("%H:%M:%S")
        sensor = "sensor.tado_optimizer_custom_sensor_1"
        payload = {
            "state": self.weather_data["hourly"][0]["temp"],
            "attributes": {
                "unit_of_measurement": "Time",
                "friendly_name": "Tado Optimizer 1",
                "icon": "mdi:thermometer",
                "Latitude": self.latitude,
                "Longitude": self.longitude,
                "humidity": "78%"
            }
        }

        hass.update_entity(sensor, payload)

import logging
import requests
from datetime import datetime
from hass import HomeAssistantAPI

home_assistant = HomeAssistantAPI()

def convert_time(unix_time):
    readable_time = datetime.fromtimestamp(unix_time)
    formatted_time = readable_time.strftime('%H:%M - %d %B %Y')
    return formatted_time

def convert_time_date_only(unix_time):
    readable_time = datetime.fromtimestamp(unix_time)
    formatted_time = readable_time.strftime('%d %B %Y')
    return formatted_time

class WeatherAPI:
    def __init__(self, open_weather_api_key, latitude, longitude):
        self.base_url = "https://api.openweathermap.org/data/3.0/onecall?"
        self.api_key = open_weather_api_key
        self.latitude = latitude
        self.longitude = longitude
        self.weather_data = {}

    def get_weather_data(self):
        logging.info(msg="Getting weather data")
        fullUrl = f"{self.base_url}lat={self.latitude}&lon={self.longitude}&appid={self.api_key}&units=metric"
        logging.debug(msg=f"Get weather data fullUrl: {fullUrl}")
        response = requests.get(fullUrl)
        status = response.status_code
        logging.info(msg=f"Weather API status code: {status}")
        self.weather_data = response.json()

    def sample_update(self):
        hourly_data = self.weather_data["hourly"]
        sensor = "sensor.tado_optimizer_custom_sensor_1"
        payload = {
            "state": hourly_data[0]["temp"],
            "attributes": {
                "unit_of_measurement": "°C",
                "friendly_name": convert_time(hourly_data[0]["dt"]),
                "icon": "mdi:thermometer",
                "Pressure": hourly_data[0]["pressure"],
                "Humidity": hourly_data[0]["humidity"],
            }
        }

        home_assistant.is_ha_running()
        home_assistant.update_entity(sensor, payload)

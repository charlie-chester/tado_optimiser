import logging
import yaml
import requests

# Access options file and obtain variables
options_file = "/data/options.json"
with open(options_file, "r") as file:
    options = yaml.safe_load(file)

class WeatherAPI:
    def __init__(self):
        self.base_url = "https://api.openweathermap.org/data/3.0/onecall?"
        self.api_key = options.get("open_weather_api")
        self.latitude = options.get("latitude")
        self.longitude = options.get("longitude")

    def get_weather_data(self):
        fullUrl = f"{self.base_url}lat={self.latitude}&lon={self.longitude}&appid={self.api_key}&units=metric"
        data = requests.get(fullUrl)
        status = data.status_code
        logging.info(msg="Getting weather data")
        logging.debug(msg=f"Get weather data fullUrl: {fullUrl}")
        logging.info(msg=f"Weather API status code: {status}")
        return data.json()



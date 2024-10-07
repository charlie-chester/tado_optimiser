import logging
import requests

class WeatherAPI:
    def __init__(self, open_weather_api_key, latitude, longitude):
        self.base_url = "https://api.openweathermap.org/data/3.0/onecall?"
        self.api_key = open_weather_api_key
        self.latitude = latitude
        self.longitude = longitude

    def get_weather_data(self):
        fullUrl = f"{self.base_url}lat={self.latitude}&lon={self.longitude}&appid={self.api_key}&units=metric"
        data = requests.get(fullUrl)
        status = data.status_code
        logging.info(msg="Getting weather data")
        logging.debug(msg=f"Get weather data fullUrl: {fullUrl}")
        logging.info(msg=f"Weather API status code: {status}")
        return data.json()

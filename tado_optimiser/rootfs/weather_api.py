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
        self.weather_data = response.json()

        status = response.status_code
        if status == 200:
            logging.info(msg="Weather data successfully retrieved")
        else:
            logging.error(msg=f"Error getting weather data. Status code: {status}")

    def sample_update(self):
        hourly_data = self.weather_data["hourly"]
        sensor = "sensor.tado_optimiser_custom_sensor_1"
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

        home_assistant.update_entity(sensor, payload)

    def hourly_entities(self):
        hourly_data = self.weather_data["hourly"]
        for hour in range(0, 12):
            wind_gust = hourly_data[hour].get("wind_gust", "No Data")
            if wind_gust == "No Data":
                logging.info(msg=f"No Wind Gust data found for {convert_time(hourly_data[hour]['dt'])} using default message")

            rain = hourly_data[hour].get("rain", "No Data")
            if rain == "No Data":
                logging.info(msg=f"No Rain data found for {convert_time(hourly_data[hour]['dt'])} using default message")

            snow = hourly_data[hour].get("snow", "No Data")
            if snow == "No Data":
                logging.info(msg=f"No Snow data found for {convert_time(hourly_data[hour]['dt'])} using default message")

            sensor = f"sensor.tado_open_weather_hour_{hour}"
            try:
                payload = {
                    "state": hourly_data[hour]["temp"],
                    "attributes": {
                        "unit_of_measurement": "°C",
                        "friendly_name": convert_time(hourly_data[hour]["dt"]),
                        "icon": "mdi:thermometer",
                        "Feels like": hourly_data[hour]["feels_like"],
                        "Pressure": hourly_data[hour]["pressure"],
                        "Humidity": hourly_data[hour]["humidity"],
                        "Dew point": hourly_data[hour]["dew_point"],
                        "UVI": hourly_data[hour]["uvi"],
                        "Clouds": hourly_data[hour]["clouds"],
                        "Visibility": hourly_data[hour]["visibility"],
                        "Wind speed": hourly_data[hour]["wind_speed"],
                        "Wind gust": wind_gust,
                        "Wind degrees": hourly_data[hour]["wind_deg"],
                        "POP": hourly_data[hour]["pop"],
                        "Rain": rain,
                        "Snow": snow,
                        "Weather - ID": hourly_data[hour]["weather"][0]["id"],
                        "Weather - Main": hourly_data[hour]["weather"][0]["main"],
                        "Weather - Description": hourly_data[hour]["weather"][0]["description"]
                    }
                }

            except KeyError as e:
                missing_key = str(e).strip("'")
                logging.info(msg=f"KeyError: Missing key '{missing_key}' in hourly data for "
                         f"{convert_time(hourly_data[hour]['dt'])}")
                payload = {
                    "state": hourly_data[hour]["temp"],
                    "attributes": {
                        "unit_of_measurement": "°C",
                        "friendly_name": convert_time(hourly_data[hour]["dt"]),
                    }
                }

            home_assistant.update_entity(sensor, payload)

        logging.info(msg="Hourly entities created / updated")

import logging
import requests
from datetime import datetime
from hass import HomeAssistantAPI


logger = logging.getLogger("tado_optimiser")

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
        logger.info(msg="Getting weather data")
        fullUrl = f"{self.base_url}lat={self.latitude}&lon={self.longitude}&appid={self.api_key}&units=metric"
        logger.debug(msg=f"Get weather data fullUrl: {fullUrl}")
        response = requests.get(fullUrl)
        self.weather_data = response.json()

        status = response.status_code
        if status == 200:
            logger.info(msg="Weather data successfully retrieved")
        else:
            logger.error(msg=f"Error getting weather data. Status code: {status}")

    def current_weather(self):
        current_data = self.weather_data["current"]
        sensor = "sensor.tado_optimiser_current"
        payload = {
            "state": current_data["temp"],
            "attributes": {
                "unit_of_measurement": "°C",
                "friendly_name": convert_time(current_data["dt"]),
                "icon": "mdi:thermometer",
                "Sunrise": convert_time(current_data["sunrise"]),
                "Sunset": convert_time(current_data["sunset"]),
                "Temp": current_data["temp"],
                "Feels like": current_data["feels_like"],
                "Pressure": current_data["pressure"],
                "Humidity": current_data["humidity"],
                "Dew point": current_data["dew_point"],
                "Clouds": current_data["clouds"],
                "UVI": current_data["uvi"],
                "Visibility": current_data["visibility"],
                "Wind speed": current_data["wind_speed"],
                "Wind Gust": current_data.get("wind_gust", "No Data"),
                "Wind degrees": current_data["wind_deg"],
                "Rain": current_data.get("rain", {}).get("1h", 0),
                "Snow": current_data.get("snow", {}).get("1h", 0),
                "Weather - ID": current_data["weather"][0]["id"],
                "Weather - Main": current_data["weather"][0]["main"],
                "Weather - Description": current_data["weather"][0]["description"]
            }
        }
        home_assistant.update_entity(sensor, payload)
        logger.info(msg="Current weather entity created / updated")

    def hourly_entities(self):
        hourly_data = self.weather_data["hourly"]
        for hour in range(0, 12):
            sensor = f"sensor.tado_optimiser_hour_{hour}"
            payload = {
                "state": hourly_data[hour]["temp"],
                "attributes": {
                    "unit_of_measurement": "°C",
                    "friendly_name": convert_time(hourly_data[hour]["dt"]),
                    "icon": "mdi:thermometer",
                    "Time": convert_time(hourly_data[hour]["dt"]),
                    "Temp": hourly_data[hour]["temp"],
                    "Feels like": hourly_data[hour]["feels_like"],
                    "Pressure": hourly_data[hour]["pressure"],
                    "Humidity": hourly_data[hour]["humidity"],
                    "Dew point": hourly_data[hour]["dew_point"],
                    "UVI": hourly_data[hour]["uvi"],
                    "Clouds": hourly_data[hour]["clouds"],
                    "Visibility": hourly_data[hour]["visibility"],
                    "Wind speed": hourly_data[hour]["wind_speed"],
                    "Wind gust": hourly_data[hour].get("wind_gust", "No Data"),
                    "Wind degrees": hourly_data[hour]["wind_deg"],
                    "POP": hourly_data[hour]["pop"],
                    "Rain": hourly_data[hour].get("rain", {}).get("1h", 0),
                    "Snow": hourly_data[hour].get("snow", {}).get("1h", 0),
                    "Hourly Weather - ID": hourly_data[hour]["weather"][0]["id"],
                    "Hourly Weather - Main": hourly_data[hour]["weather"][0]["main"],
                    "Hourly Weather - Description": hourly_data[hour]["weather"][0]["description"]
                }
            }
            home_assistant.update_entity(sensor, payload)
        logger.info(msg="Hourly entities created / updated")

    def daily_entities(self):
        daily_data = self.weather_data["daily"]
        for day in range(0, 8):
            sensor = f"sensor.tado_optimiser_day_{day}"
            payload = {
                "state": daily_data[day]["temp"]["day"],
                "attributes": {
                    "unit_of_measurement": "°C",
                    "friendly_name": convert_time_date_only(daily_data[day]["dt"]),
                    "icon": "mdi:thermometer",
                    "Date": convert_time_date_only(daily_data[day]["dt"]),
                    "Sunrise": convert_time(daily_data[day]["sunrise"]),
                    "Sunset": convert_time(daily_data[day]["sunset"]),
                    "Moonrise": convert_time(daily_data[day]["moonrise"]),
                    "Moonset": convert_time(daily_data[day]["moonset"]),
                    "Moon phase": daily_data[day]["moon_phase"],
                    "Summary": daily_data[day]["summary"],
                    "Temp - Day": daily_data[day]["temp"]["day"],
                    "Temp - Min": daily_data[day]["temp"]["min"],
                    "Temp - Max": daily_data[day]["temp"]["max"],
                    "Temp - Night": daily_data[day]["temp"]["night"],
                    "Temp - Eve": daily_data[day]["temp"]["eve"],
                    "Temp - Morn": daily_data[day]["temp"]["morn"],
                    "Feels like - Day": daily_data[day]["feels_like"]["day"],
                    "Feels like - Night": daily_data[day]["feels_like"]["night"],
                    "Feels like - Eve": daily_data[day]["feels_like"]["eve"],
                    "Feels like - Morn": daily_data[day]["feels_like"]["morn"],
                    "Pressure": daily_data[day]["pressure"],
                    "Humidity": daily_data[day]["humidity"],
                    "Dew point": daily_data[day]["dew_point"],
                    "Wind speed": daily_data[day]["wind_speed"],
                    "Wind Gusts": daily_data[day].get("wind_gust", "No Data"),
                    "Wind degrees": daily_data[day]["wind_deg"],
                    "Wind gust": daily_data[day]["wind_gust"],
                    "Weather - ID": daily_data[day]["weather"][0]["id"],
                    "Weather - Main": daily_data[day]["weather"][0]["main"],
                    "Weather - Description": daily_data[day]["weather"][0]["description"],
                    "Clouds": daily_data[day]["clouds"],
                    "UVI": daily_data[day]["uvi"],
                    "POP": daily_data[day]["pop"],
                    "Rain": daily_data[day].get("rain", 0),
                    "Snow": daily_data[day].get("snow", 0),
                    "Daily Weather - ID": daily_data[day]["weather"][0]["id"],
                    "Daily Weather - Main": daily_data[day]["weather"][0]["main"],
                    "Daily Weather - Description": daily_data[day]["weather"][0]["description"],
                }
            }
            home_assistant.update_entity(sensor, payload)
        logger.info(msg="Daily entities created / updated")

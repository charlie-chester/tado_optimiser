import json
import logging
import time
import os
from datetime import datetime

import requests

from home_assistant_api import HomeAssistantAPI

logger = logging.getLogger("tado_optimiser")

home_assistant = HomeAssistantAPI()

def day_suffix(day):
        return "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

def convert_time(unix_time):
    readable_time = datetime.fromtimestamp(unix_time)
    formatted_time = readable_time.strftime(f"%H:%M - %-d{day_suffix(day=readable_time.day)} %B %Y")
    return formatted_time

def convert_time_date_only(unix_time):
    readable_time = datetime.fromtimestamp(unix_time)
    formatted_time = readable_time.strftime(f"%A %-d{day_suffix(day=readable_time.day)} %B %Y")
    return formatted_time

class WeatherAPI:
    def __init__(self, open_weather_api_key, latitude, longitude):
        self.base_url = "https://api.openweathermap.org/data/3.0/onecall?"
        self.api_key = open_weather_api_key
        self.latitude = latitude
        self.longitude = longitude
        self.weather_data = {}
        self.weather_data_last_updated = ""

    def update_weather_data(self):
        now = datetime.now()

        # Checks to see if weather data files are present and if not runs plan to make new ones
        if not os.path.exists("/config/weather_data.json") or not os.path.exists("/config/weather_data_last_updated.txt"):
            logger.info(msg="Weather data backup files not present running plan to make new ones")
            self.get_weather_data()

        # If data files are present but no data in system load them
        elif self.weather_data_last_updated == "" or self.weather_data == {}:
            with open("/config/weather_data.json", "r") as f:
                self.weather_data = json.load(f)
            with open("/config/weather_data_last_updated.txt", "r") as f:
                self.weather_data_last_updated = f.read()

            logger.info(msg="Weather data loaded from backup files")

            # Checks if backup weather data is older than 15 minutes and updates weather data
            if (now - datetime.strptime(self.weather_data_last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds() > 60 * 15:
                logger.info(msg="Backup weather data older than 15 minutes updating")
                self.get_weather_data()
    
        # Checks if minute is either 0, 15, 30 or 45 and updates weather data
        if now.minute % 15 == 0 and (now - datetime.strptime(self.weather_data_last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds() > 30:
                self.get_weather_data()
        else:
            if (now - datetime.strptime(self.weather_data_last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds() > 30:
                logger.info(msg=f"Weather data not updated. Last updated: {self.weather_data_last_updated}")
                self.current_weather()
                self.hourly_entities()
                self.daily_entities()
            
    def get_weather_data(self):
        # Updates weather data if it fails will stay in loop
        fullUrl = f"{self.base_url}lat={self.latitude}&lon={self.longitude}&appid={self.api_key}&units=metric"
        logger.debug(msg=f"Get weather data fullUrl: {fullUrl}")
        response = requests.get(fullUrl)
        status = response.status_code

        if status == 200:
            # Records weather data & timestamp
            self.weather_data = response.json()
            self.weather_data_last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Write formatted json to file & records timestamp
            with open("/config/weather_data.json", "w") as f:
                json.dump(self.weather_data, f, indent=4)
            with open("/config/weather_data_last_updated.txt", "w") as f:
                f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
            logger.info(msg=f"Weather data updated: {self.weather_data_last_updated}")
            self.current_weather()
            self.hourly_entities()
            self.daily_entities()
            
        else:
            logger.error(msg=f"Error getting weather data. Status code: {status} Will try again in 30 minute")
            time.sleep(60 * 30)
            self.update_weather_data()

    def current_weather(self):
        # Creates / updates entities
        current_data = self.weather_data["current"]
        sensor = "sensor.tado_optimiser_current"
        try:
            payload = {
                "state": current_data["temp"],
                "attributes": {
                    "unit_of_measurement": "°C",
                    "friendly_name": convert_time(current_data["dt"]),
                    "icon": "mdi:thermometer",
                    "Time": convert_time(current_data["dt"]),
                    "Sunrise": convert_time(current_data["sunrise"]),
                    "Sunset": convert_time(current_data["sunset"]),
                    "Temp": current_data["temp"],
                    "Feels like": current_data["feels_like"],
                    "Pressure": current_data["pressure"],
                    "Humidity": current_data["humidity"],
                    "Dew point": current_data["dew_point"],
                    "Clouds": current_data["clouds"],
                    "UVI": current_data["uvi"],
                    "Visibility": current_data.get("visibility", "No Data"),
                    "Wind speed": current_data["wind_speed"],
                    "Wind gust": current_data.get("wind_gust", "No Data"),
                    "Wind degrees": current_data["wind_deg"],
                    "Rain": current_data.get("rain", {}).get("1h", 0),
                    "Snow": current_data.get("snow", {}).get("1h", 0),
                    "Weather - ID": current_data["weather"][0]["id"],
                    "Weather - Main": current_data["weather"][0]["main"],
                    "Weather - Description": current_data["weather"][0]["description"].capitalize()
                }
            }

        except KeyError as error:
            logger.error(msg=f"Error creating current weather entity. Key not found: {error}")
            sensor = "sensor.tado_optimiser_current"
            payload = {
                "state": current_data["temp"],
                "attributes": {
                    "unit_of_measurement": "°C",
                    "friendly_name": convert_time(current_data["dt"]),
                    "icon": "mdi:thermometer",
                }
            }
            home_assistant.update_entity(sensor=sensor, payload=payload)

        home_assistant.update_entity(sensor, payload)
        logger.info(msg="Current weather entity created / updated")

    def hourly_entities(self):
        # Creates / updates entities
        hourly_data = self.weather_data["hourly"]
        for hour in range(0, 12):
            sensor = f"sensor.tado_optimiser_hour_{hour}"
            try:
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
                        "Visibility": hourly_data[hour].get("visibility", "No Data"),
                        "Wind speed": hourly_data[hour]["wind_speed"],
                        "Wind gust": hourly_data[hour].get("wind_gust", "No Data"),
                        "Wind degrees": hourly_data[hour]["wind_deg"],
                        "POP": hourly_data[hour]["pop"],
                        "Rain": hourly_data[hour].get("rain", {}).get("1h", 0),
                        "Snow": hourly_data[hour].get("snow", {}).get("1h", 0),
                        "Hourly Weather - ID": hourly_data[hour]["weather"][0]["id"],
                        "Hourly Weather - Main": hourly_data[hour]["weather"][0]["main"],
                        "Hourly Weather - Description": hourly_data[hour]["weather"][0]["description"].capitalize(),
                    }
                }

            except KeyError as error:
                logger.error(msg=f"Error creating hourly weather entity. Key not found: {error}")
                sensor = f"sensor.tado_optimiser_hour_{hour}"
                payload = {
                    "state": hourly_data[hour]["temp"],
                    "attributes": {
                        "unit_of_measurement": "°C",
                        "friendly_name": convert_time(hourly_data[hour]["dt"]),
                        "icon": "mdi:thermometer",
                    }
                }
                home_assistant.update_entity(sensor=sensor, payload=payload)

            home_assistant.update_entity(sensor=sensor, payload=payload)

        logger.info(msg="Hourly entities created / updated")

    def daily_entities(self):
        # Creates / updates entities
        daily_data = self.weather_data["daily"]
        for day in range(0, 8):
            sensor = f"sensor.tado_optimiser_day_{day}"
            try:
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
                        "Wind gust": daily_data[day].get("wind_gust", "No Data"),
                        "Wind degrees": daily_data[day]["wind_deg"],
                        "Clouds": daily_data[day]["clouds"],
                        "UVI": daily_data[day]["uvi"],
                        "POP": daily_data[day]["pop"],
                        "Rain": daily_data[day].get("rain", 0),
                        "Snow": daily_data[day].get("snow", 0),
                        "Daily Weather - ID": daily_data[day]["weather"][0]["id"],
                        "Daily Weather - Main": daily_data[day]["weather"][0]["main"],
                        "Daily Weather - Description": daily_data[day]["weather"][0]["description"].capitalize(),
                    }
                }
            except KeyError as error:
                logger.error(msg=f"Error creating daily weather entity. Key not found: {error}")
                sensor = f"sensor.tado_optimiser_day_{day}"
                payload = {
                    "state": daily_data[day]["temp"]["day"],
                    "attributes": {
                        "unit_of_measurement": "°C",
                        "friendly_name": convert_time_date_only(daily_data[day]["dt"]),
                        "icon": "mdi:thermometer",
                    }
                }

                home_assistant.update_entity(sensor=sensor, payload=payload)

            home_assistant.update_entity(sensor=sensor, payload=payload)

        logger.info(msg="Daily entities created / updated")

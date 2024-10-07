import json
import logging
import time
from datetime import datetime
import yaml
import schedule
from weather_api import WeatherAPI
from hass import HomeAssistantAPI

time.sleep(10)

options_addon = "/data/options.json"
with open(options_addon, "r") as file:
    addon_options = yaml.safe_load(file)

LOG_LEVEL = addon_options.get("log_level", "INFO")
LATITUDE = addon_options.get("latitude")
LONGITUDE = addon_options.get("longitude")
OPEN_WEATHER_API = addon_options.get("open_weather_api")

options_supervisor = "/data/auth.json"
with (open(options_supervisor, "r") as file):
    supervisor_options = json.load(file)

TOKEN = supervisor_options.get("access_token")

logging.basicConfig(level=getattr(logging, LOG_LEVEL),
                    format="%(asctime)s %(levelname)s %(filename)s line %(lineno)d: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

logging.info(msg="Tado Optimizer starting")

logging.info(msg=f"The latitude is {LATITUDE}")
logging.info(msg=f"The longitude is {LONGITUDE}")
logging.info(msg=f"The Open Weather API Key is {OPEN_WEATHER_API}")
logging.info(msg=f"The Home Assistant Token is {TOKEN}")

weather = WeatherAPI(open_weather_api_key=OPEN_WEATHER_API, latitude=LATITUDE, longitude=LONGITUDE)
hass = HomeAssistantAPI(token=TOKEN)

def main():
    weather.get_weather_data()

    now = datetime.now().strftime("%H:%M:%S")
    sensor = "sensor.tado_optimizer_custom_sensor_1"
    payload = {
        "state": now,
        "attributes": {
            "unit_of_measurement": "Time",
            "friendly_name": "Tado Optimizer 1",
            "icon": "mdi:thermometer"
        }
    }

    hass.update_entity(sensor, payload)


main()

for minute in ["00:05", "15:00", "30:00", "45:00"]:
    schedule.every().hour.at(minute).do(main)

while True:
    schedule.run_pending()
    time.sleep(1)

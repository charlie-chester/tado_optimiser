import logging
import time
import os
from datetime import datetime
import yaml
import schedule
from weather_api import WeatherAPI

time.sleep(10)

options_file = "/data/options.json"
with open(options_file, "r") as file:
    options = yaml.safe_load(file)

LOG_LEVEL = options.get("log_level", "INFO")
LATITUDE = options.get("latitude")
LONGITUDE = options.get("longitude")
OPEN_WEATHER_API = options.get("open_weather_api")
TOKEN = os.getenv("SUPERVISOR_TOKEN")

logging.basicConfig(level=getattr(logging, LOG_LEVEL),
                    format="%(asctime)s %(levelname)s %(filename)s line %(lineno)d: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

logging.info(msg="Tado Optimizer starting")

logging.info(msg=f"The latitude is {LATITUDE}")
logging.info(msg=f"The longitude is {LONGITUDE}")
logging.debug(msg=f"The Open Weather API Key is {OPEN_WEATHER_API}")
logging.debug(msg=f"The Home Assistant Token is {TOKEN}")

weather = WeatherAPI(open_weather_api_key=OPEN_WEATHER_API, latitude=LATITUDE, longitude=LONGITUDE)

def main():
    weather.get_weather_data()
    weather.sample_update()

main()

for minute in ["00:05", "15:00", "30:00", "45:00"]:
    schedule.every().hour.at(minute).do(main)

while True:
    schedule.run_pending()
    time.sleep(1)

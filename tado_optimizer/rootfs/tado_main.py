import logging
import yaml
import schedule
import time
from weather_api import WeatherAPI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s : %(levelname)s : %(filename)s - %(lineno)d : %(message)s",datefmt="%Y-%m-%d %H:%M:%S")
logging.info(msg="Tado Optimizer starting")

# Access options file and obtain variables
options_file = "/data/options.json"
with open(options_file, "r") as file:
    options = yaml.safe_load(file)

LONGITUDE = options.get("longitude")
LATITUDE = options.get("latitude")
OPEN_WEATHER_API_KEY = options.get("open_weather_api")

weather = WeatherAPI()

logging.info(msg=f"The latitude is {LATITUDE}")
logging.info(msg=f"The longitude is {LONGITUDE}")
logging.info(msg=f"The Open Weather API Key is {OPEN_WEATHER_API_KEY}")

weather.get_weather_data()

# def main():
#     weather.get_weather_data()
#
# main()
#
# schedule.every(15).minutes.do(main)
#
# while True:
#     schedule.run_pending()
#     time.sleep(1)

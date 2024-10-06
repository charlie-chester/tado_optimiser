import logging
import yaml
import schedule
import time
from weather_api import WeatherAPI

time.sleep(10)

options_file = "/data/options.json"
with open(options_file, "r") as file:
    options = yaml.safe_load(file)

log_level = options.get("log_level", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level),
                    format="%(asctime)s : %(levelname)s : %(filename)s line %(lineno)d : %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

logging.info(msg="Tado Optimizer starting")

logging.info(msg=f"The latitude is {options.get('latitude')}")
logging.info(msg=f"The longitude is {options.get('longitude')}")
logging.info(msg=f"The Open Weather API Key is {options.get('open_weather_api')}")

weather = WeatherAPI()

def main():
    weather.get_weather_data()

main()

schedule.every(1).minutes.do(main)

while True:
    schedule.run_pending()
    time.sleep(1)

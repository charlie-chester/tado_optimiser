import logging
import os
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s : %(levelname)s : %(filename)s line %(lineno)d : %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
logging.info(msg="Tado Optimizer starting")

# Path to the options.yaml file
options_file = "/data/options.json"

# Read the YAML configuration
with open(options_file, "r") as file:
    options = yaml.safe_load(file)

# Access the specific options
LONGITUDE = options.get("longitude")
LATITUDE = options.get("latitude")
OPEN_WEATHER_API_KEY = options.get("open_weather_api")




logging.info(f"The longitude is {LONGITUDE}")
logging.info(f"The latitude is {LATITUDE}")
logging.info(f"The Open Weather API Key is {OPEN_WEATHER_API_KEY}")



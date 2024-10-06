import logging
import os
import time
import datetime

LONGITUDE = os.getenv("HASSIO_LONGITUDE")
LATITUDE = os.getenv("HASSIO_LATITUDE")
OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")

logging.basicConfig(level=logging.INFO, format="%(asctime)s : %(levelname)s : %(filename)s line %(lineno)d : %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

logging.info(msg="Tado Optimizer starting")

logging.info(f"The longitude is {LONGITUDE}")
logging.info(f"The latitude is {LATITUDE}")
logging.info(f"The Open Weather API Key is {OPEN_WEATHER_API_KEY}")

time.sleep(60 *60)



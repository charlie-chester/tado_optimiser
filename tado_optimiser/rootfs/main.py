import logging
from logging.handlers import RotatingFileHandler
import time
import os
from datetime import datetime
import yaml
import schedule
import shutil
from weather_api import WeatherAPI
from hass import HomeAssistantAPI


# Load the configuration file
configuration_file = "/data/options.json"
with open(configuration_file, "r") as file:
    configurations = yaml.safe_load(file)

#  gets the log level from the user
LOG_LEVEL = configurations.get("log_level", "INFO").upper()

# Set up the logger
logger = logging.getLogger("tado_optimiser")
logger.setLevel(getattr(logging, LOG_LEVEL))  # Set the logging level

# Create a rotating file handler (used to handle logging output)
handler = RotatingFileHandler(filename="/config/logfile.log", maxBytes=1024*1024, backupCount=5)
handler.setLevel(getattr(logging, LOG_LEVEL))  # Setting level for the handler

# Create a logging format
formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(filename)s line %(lineno)d: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)  # Attach the formatter to the handler

# Add the handler to the logger (this is where 'handler' is used)
logger.addHandler(handler)

logger.info(msg="Tado Optimizer starting")

# Checks if the setting file exists and uploads if false
if not os.path.exists("/config/settings.yaml"):
    shutil.copy(src="/settings.yaml", dst="/config/settings.yaml")
    logger.info(msg="Copied settings file to /config")
else:
    logger.info(msg="Settings file already exists in /config")

# Loads the settings file
settings_file = "/config/settings.yaml"
with open(settings_file, "r") as file:
    settings = yaml.safe_load(file)

# Sets the Global variables
CONTROL_TADO = settings.get("control_tado")
LATITUDE = configurations.get("latitude")
LONGITUDE = configurations.get("longitude")
OPEN_WEATHER_API = configurations.get("open_weather_api")
TOKEN = os.getenv("SUPERVISOR_TOKEN")
OUTSIDE_TEMP = settings.get("outside_temp")
SUN_CORRECTION_TEMP = settings.get("sun_correction_temp")
MORNING_ENDS = settings.get("morning_ends")
ROOMS = settings.get("rooms")

# Initial logging of variables
logger.info(msg=f"Latitude: {LATITUDE}")
logger.info(msg=f"Longitude: {LONGITUDE}")
logger.info(msg=f"Open Weather API Key: {OPEN_WEATHER_API}")
logger.info(msg=f"Control Tado: {CONTROL_TADO}")
logger.debug(msg=f"Home Assistant Token: {TOKEN}")

# Initialises the Home Assistant & Weather API Classes
weather = WeatherAPI(open_weather_api_key=OPEN_WEATHER_API, latitude=LATITUDE, longitude=LONGITUDE)
home_assistant = HomeAssistantAPI()

def main():
    logger.info(msg="*************************************************************************")
    logger.info(msg="Starting update cycle")
    logger.info(msg="*************************************************************************")
    logger.info(msg=f"Outside temperature set to: {OUTSIDE_TEMP} C")

    # Updates weather data and entities
    weather.get_weather_data()
    weather.current_weather()
    weather.hourly_entities()
    weather.daily_entities()

    # Checks if user wants Tado control. If true continues
    if CONTROL_TADO:
        tado_control()
    else:
        logger.info(msg="Tado Control not enabled")

def tado_control():
    # Get Sunrise & current weather conditions
    sunrise = datetime.fromtimestamp(weather.weather_data["current"]["sunrise"]).time()
    current_weather_id = weather.weather_data["current"]["weather"][0]["id"]
    current_weather_condition = weather.weather_data["current"]["weather"][0]["description"]
    current_weather_temperature = weather.weather_data["current"]["temp"]

    # Finds temperatures next 3 hours
    temp_hour_0 = weather.weather_data["hourly"][0]["temp"]
    temp_hour_1 = weather.weather_data["hourly"][1]["temp"]
    temp_hour_2 = weather.weather_data["hourly"][2]["temp"]
    temps = [temp_hour_0, temp_hour_1, temp_hour_2]

    # Considers True or False if heating required based on outside temperature
    heating_required = False
    for temp in temps:
        if temp >= OUTSIDE_TEMP:
            heating_required = False
            break
        else:
            heating_required = True

    logger.info(msg="*************************************************************************")

    # Iterate through rooms and apply settings
    for room_name, room_data in ROOMS.items():
        logger.info(msg=room_name.upper().replace('_', ' '))

        # Obtain Tado Data
        room_temperature = home_assistant.get_entity_state(f"sensor.{room_name}_temperature")
        room_climate = home_assistant.get_entity_state(f"climate.{room_name}")

        # Log entries
        logger.info(msg=f"Room Temperature: {room_temperature}")
        logger.info(msg=f"Climate Setting: {room_climate.upper()}")
        logger.info(msg=f"Temps: Hour 0: {temp_hour_0}, Hour 1: {temp_hour_1}, Hour 2: {temp_hour_2}")
        logger.info(msg=f"Heating required: {heating_required}")
        logger.info(msg=f"Sunrise time: {sunrise}")
        logger.info(msg=f"Current weather - ID: {current_weather_id}, Condition: {current_weather_condition}")

        # Set minimum room temperature based on time and room
        if sunrise <= datetime.now().time() < datetime.now().time().replace(hour=MORNING_ENDS["hour"], minute=MORNING_ENDS["minute"]):
            room_minimum_temp = room_data["morning"]
            logger.info(msg=f"Morning: Minimum room temperature: {room_minimum_temp} C")

            # Adjusts room temperature based on sunshine and outside temperature
            if 800 <= current_weather_id <= 802 and current_weather_temperature >= SUN_CORRECTION_TEMP:
                room_minimum_temp = room_minimum_temp - room_data["sun_correction"]
                logger.info(msg=f"Sun Correction: {room_data['sun_correction']} C")
                logger.info(msg=f"Minimum room temperature after sun correction: {room_minimum_temp} C")
        else:
            room_minimum_temp = room_data["day"]
            logger.info(msg=f"Afternoon / Evening: Minimum room temperature: {room_minimum_temp} C")

        # Main logical questions
        if room_climate == "off" and float(room_temperature) < room_minimum_temp:
            home_assistant.set_hvac_mode(entity_id=f"climate.{room_name}", hvac_mode="auto")
            logger.info(msg=f"Room temperature less than {room_minimum_temp} C and climate set to {room_climate.upper()} turning to auto")

        elif room_climate == "off" and heating_required == True:
            home_assistant.set_hvac_mode(entity_id=f"climate.{room_name}", hvac_mode="auto")
            logger.info(msg=f"Outside temperature below {OUTSIDE_TEMP} C in the next 3 hours turning to auto")

        elif room_climate == "auto" and heating_required == False and float(room_temperature) >= room_minimum_temp:
            home_assistant.set_hvac_mode(entity_id=f"climate.{room_name}", hvac_mode="off")
            logger.info(msg=f"Outside temperature above {OUTSIDE_TEMP} in the next 3 hours turning to off")

        else:
            logger.info(msg=f"No change needed. The climate will remain: {room_climate.upper()}")

        logger.info(msg="*************************************************************************")

    logger.info(msg="Update cycle finished")
    logger.info(msg="*************************************************************************")

main()

#  Schedule to run every 10 minutes
for minute in ["00:05", "10:00", "20:00", "30:00", "40:00", "50:00"]:
    schedule.every().hour.at(minute).do(main)

# Keeps schedule running
while True:
    schedule.run_pending()
    time.sleep(1)

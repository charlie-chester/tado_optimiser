import logging
import os
import shutil
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

import schedule
import yaml
from home_assistant_api import HomeAssistantAPI
from octopus_api import Octopus
from tado import Tado
from weather_api import WeatherAPI


def load_config(url):
    system_file = url
    with open(system_file, "r") as file:
        return yaml.safe_load(file)

def copy_settings_file():
    if not os.path.exists("/config/settings.yaml"):
        shutil.copy(src="/settings.yaml", dst="/config/settings.yaml")
        logger.info(msg="Copied settings file to /config")
    else:
        logger.info(msg="Settings file already exists in /config")

def get_time_sector(sunrise, sunset):
    if sunrise <= datetime.now().time() < sunset:
        time_sector = "day"
    elif sunset <= datetime.now().time() < datetime.strptime('23:59', '%H:%M').time():
        time_sector = "evening"
    else:
        time_sector = "night"
    return time_sector

def calculate_radiator_flow_temp(outside_temp):
    if outside_temp <= 0:
        return 75
    elif outside_temp >= 10:
        return 50
    else:
        return 75 - (outside_temp * 2.5)

def log_line_break():
    logger.info(msg="***************************************************************************************")

# Set Global from System
TOKEN = os.getenv("SUPERVISOR_TOKEN")

# Load the configuration file
configurations = load_config(url="/data/options.json")

# Set Global variables from Configuration
LOG_LEVEL = configurations.get("log_level", "INFO").upper()
LATITUDE = configurations.get("latitude")
LONGITUDE = configurations.get("longitude")
OPEN_WEATHER_API = configurations.get("open_weather_api")
OCTOPUS_API = configurations.get("octopus_api")
OCTOPUS_ACCOUNT = configurations.get("octopus_account")

# Set up the logger
logger = logging.getLogger("tado_optimiser")
logger.setLevel(getattr(logging, LOG_LEVEL))
handler = RotatingFileHandler(filename="/config/logfile.log", maxBytes=1024*1024, backupCount=5)
handler.setLevel(getattr(logging, LOG_LEVEL))
formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(filename)s line %(lineno)03d: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Additional block to use system logs in addition
stream_handler = logging.StreamHandler()
stream_handler.setLevel(getattr(logging, LOG_LEVEL))
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
# End of additional code

logger.info(msg="Tado Optimizer starting")

# Check & load settings
copy_settings_file()
settings = load_config(url="/config/settings.yaml")

# Initial variables logging
logger.info(msg=f"Latitude: {LATITUDE}")
logger.info(msg=f"Longitude: {LONGITUDE}")
logger.debug(msg=f"Open Weather API Key: {OPEN_WEATHER_API}")
logger.debug(msg=f"Home Assistant Token: {TOKEN}")

# Initialise Home Assistant, Weather & Octopus Classes
home_assistant = HomeAssistantAPI()
weather = WeatherAPI(open_weather_api_key=OPEN_WEATHER_API, latitude=LATITUDE, longitude=LONGITUDE)
octopus = Octopus(octopus_api=OCTOPUS_API, octopus_account=OCTOPUS_ACCOUNT)

# Initialise Tado Class & all thermostats
THERMOSTATS = []
for room_name in settings["rooms"]:
    new_room = Tado(name=room_name)
    THERMOSTATS.append(new_room)

def main():
    log_line_break()
    logger.info(msg="Starting update cycle")
    log_line_break()

    # Updates weather data and entities
    weather.update_weather_data()

    # Updates Octopus data and entities
    octopus.update_octopus_data()

    # Get Sunrise & current weather conditions
    sunrise = datetime.fromtimestamp(weather.weather_data["current"]["sunrise"]).time()
    sunset = datetime.fromtimestamp(weather.weather_data["current"]["sunset"]).time()
    current_weather_id = weather.weather_data["current"]["weather"][0]["id"]
    current_weather_condition = weather.weather_data["current"]["weather"][0]["description"].capitalize()
    solar_percentage = home_assistant.get_entity_state(sensor="sensor.home_solar_percentage")

    # Gets Electricity and gas prices
    electric_price, time_from, time_to = octopus.get_current_electricity_price(offset=0)
    electric_price = float(electric_price)
    gas_price = float(octopus.get_current_gas_price())
    logger.info(msg=f"Electricity Price: {electric_price} - {time_from[11:16]} ~ {time_to[11:16]} | Gas Price: {gas_price}")

    # Check if system is using the Grid & Predbat Status
    grid_power = home_assistant.get_entity_state(sensor="sensor.givtcp_fd2327g123_grid_power")
    predbat_status = home_assistant.get_entity_state(sensor="predbat.status")

    if grid_power == "Entity not found":
        logger.error(msg="Grid Power entity not found")
        using_grid = False
        grid_status = "No Grid Data"
    else:
        grid_power = float(grid_power)

        if grid_power <= -35:
            grid_status = "Importing"
            using_grid = True
        elif grid_power >= 35:
            grid_status = "Exporting"
            using_grid = False
        else:
            grid_status = "No Grid Activity"
            using_grid = False
            grid_power = 0

    logger.info(msg=f"Grid Power: {grid_power} watts | Grid Status: {grid_status} | Predbat Status: {predbat_status}")

    # Calculates time sector
    time_sector = get_time_sector(sunrise=sunrise, sunset=sunset)

    # Finds temperatures next 3 hours
    temp_hour_0 = weather.weather_data["hourly"][0]["temp"]
    temp_hour_1 = weather.weather_data["hourly"][1]["temp"]
    temp_hour_2 = weather.weather_data["hourly"][2]["temp"]

    # Calculate Flow Temperature
    flow_temperature = calculate_radiator_flow_temp(outside_temp=weather.weather_data["current"]["temp"])
    logger.info(msg=f"Suggested Flow Temperature: {flow_temperature:.2f}")

    # Create / update flow temperature entity
    sensor = "sensor.radiator_flow_temperature"
    payload = {
        "state": round(flow_temperature, 2),
        "attributes": {
            "unit_of_measurement": "°C",
            "friendly_name": "Radiator Flow Temperature",
            "icon": "mdi:thermometer",
        }
    }
    home_assistant.update_entity(sensor=sensor, payload=payload)

    log_line_break()

    # Iterate through rooms and apply settings
    for room in THERMOSTATS:
        logger.info(msg=room.name.upper().replace('_', ' '))

        # Refresh data
        room.update_tado_data()

        # Get target room temperature
        target_temperature = getattr(room, time_sector)

        # Log initial entries
        logger.info(msg=f"Temperature: {room.temperature:.2f} | Climate: {room.climate_gas.upper()} | Mode: {room.tado_mode.upper()} | Electric Override: {str(room.electric_override).upper()}")
        logger.info(msg=f"Outside Temperatures in the next 3 hours: {temp_hour_0:.2f} | {temp_hour_1:.2f} | {temp_hour_2:.2f}")
        logger.info(msg=f"Sunrise: {sunrise} | Sunset: {sunset} | Solar Percentage: {solar_percentage} %")
        logger.info(msg=f"Current weather - ID: {current_weather_id} | Condition: {current_weather_condition}")
        logger.info(msg=f"Time Sector: {time_sector.upper()} | Target Temperature: {target_temperature:.2f}")

        # Adjust target temperature
        target_temperature -= room.away_adjust(target_temperature=target_temperature)

        # Create / update target temperature entity
        sensor = f"sensor.{room.name}_target_temperature"
        payload = {
            "state": target_temperature,
            "attributes": {
                "unit_of_measurement": "°C",
                "friendly_name": f"{room.name.replace('_', ' ').title()} Target",
                "icon": "mdi:thermometer",
            }
        }
        home_assistant.update_entity(sensor=sensor, payload=payload)

        # Control rooms
        room.set_hvac_mode(
            target_temperature=target_temperature,
            temp_hour_0=temp_hour_0,
            temp_hour_1=temp_hour_1,
            electric_price=electric_price,
            gas_price=gas_price,
            using_grid=using_grid,
        )

        log_line_break()

    logger.info(msg="Update cycle finished")
    log_line_break()

main()

#  Schedule to run every 10 minutes
for minute in ["00:00", "05:00", "10:00", "15:00", "20:00", "25:00", "30:00", "35:00", "40:00", "45:00", "50:00", "55:00"]:
    schedule.every().hour.at(minute).do(main)

# Keeps schedule running
while True:
    schedule.run_pending()
    time.sleep(1)

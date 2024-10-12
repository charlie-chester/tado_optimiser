import logging
import time
import os
import yaml
import schedule
from datetime import datetime
from weather_api import WeatherAPI
from hass import HomeAssistantAPI


time.sleep(3)
options_file = "/data/options.json"
with open(options_file, "r") as file:
    options = yaml.safe_load(file)

LOG_LEVEL = options.get("log_level", "INFO").upper()
CONTROL_TADO = options.get("control_tado").upper()
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
logging.info(msg=f"The Open Weather API Key is {OPEN_WEATHER_API}")
logging.info(msg=f"Control Tado is set to {CONTROL_TADO}")
logging.debug(msg=f"The Home Assistant Token is {TOKEN}")

ROOMS = {
    "conservatory": {"morning": 17, "day": 18, "sun_correction": 2},
    "dining_room": {"morning": 17, "day": 18, "sun_correction": 2},
    "lounge": {"morning": 17, "day": 18, "sun_correction": 0},
    "office": {"morning": 17, "day": 17, "sun_correction": 0},
    "bedroom": {"morning": 17, "day": 17, "sun_correction": 0},
    "pink_room": {"morning": 17, "day": 17, "sun_correction": 0},
}

OUTSIDE_TEMP = 12
SUN_CORRECTION_TEMP = 10
MORNING_ENDS = (15, 0)

weather = WeatherAPI(open_weather_api_key=OPEN_WEATHER_API, latitude=LATITUDE, longitude=LONGITUDE)
home_assistant = HomeAssistantAPI()

def main():
    logging.info(msg="*************************************************************************")
    logging.info(msg="Starting update cycle")
    logging.info(msg="*************************************************************************")
    logging.info(msg=f"Outside temperature set to: {OUTSIDE_TEMP} C")

    weather.get_weather_data()
    weather.current_weather()
    weather.hourly_entities()
    weather.daily_entities()

    if CONTROL_TADO == "YES":
        tado_control()
    else:
        logging.info(msg="Tado Control not enabled")

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

    logging.info(msg="*************************************************************************")

    # Iterate through rooms and apply settings
    for room_name, room_data in ROOMS.items():
        logging.info(msg=room_name.upper().replace('_', ' '))

        # Obtain Tado Data
        room_temperature = home_assistant.get_entity_state(f"sensor.{room_name}_temperature")
        room_climate = home_assistant.get_entity_state(f"climate.{room_name}")

        # Log entries
        logging.info(msg=f"Room Temperature: {room_temperature}")
        logging.info(msg=f"Climate Setting: {room_climate.upper()}")
        logging.info(msg=f"Temps: Hour 0: {temp_hour_0}, Hour 1: {temp_hour_1}, Hour 2: {temp_hour_2}")
        logging.info(msg=f"Heating required: {heating_required}")
        logging.info(msg=f"Sunrise time: {sunrise}")
        logging.info(msg=f"Current weather - ID: {current_weather_id}, Condition: {current_weather_condition}")

        # Set minimum room temperature based on time and room
        if sunrise <= datetime.now().time() < datetime.now().time().replace(hour=MORNING_ENDS[0], minute=MORNING_ENDS[1]):
            room_minimum_temp = room_data["morning"]
            logging.info(msg=f"Morning: Minimum room temperature: {room_minimum_temp} C")

            # Adjusts room temperature based on sunshine
            if 800 <= current_weather_id <= 802 and current_weather_temperature >= SUN_CORRECTION_TEMP:
                room_minimum_temp = room_minimum_temp - room_data["sun_correction"]
                logging.info(msg=f"Sun Correction: {room_data['sun_correction']} C")
                logging.info(msg=f"Minimum room temperature after sun correction: {room_minimum_temp} C")
        else:
            room_minimum_temp = room_data["day"]
            logging.info(msg=f"Afternoon / Evening: Minimum room temperature: {room_minimum_temp} C")

        # Main logical questions
        if room_climate == "off" and float(room_temperature) < room_minimum_temp:
            home_assistant.set_hvac_mode(entity_id=f"climate.{room_name}", hvac_mode="auto")
            logging.info(msg=f"Room temperature less than {room_minimum_temp} C and climate set to {room_climate.upper()} turning to auto")

        elif room_climate == "off" and heating_required == True:
            home_assistant.set_hvac_mode(entity_id=f"climate.{room_name}", hvac_mode="auto")
            logging.info(msg=f"Outside temperature below {OUTSIDE_TEMP} C in the next 3 hours turning to auto")

        elif room_climate == "auto" and heating_required == False and float(room_temperature) >= room_minimum_temp:
            home_assistant.set_hvac_mode(entity_id=f"climate.{room_name}", hvac_mode="off")
            logging.info(msg=f"Outside temperature above {OUTSIDE_TEMP} in the next 3 hours turning to off")

        else:
            logging.info(msg=f"No change needed. The climate will remain: {room_climate.upper()}")

        logging.info(msg="*************************************************************************")

    logging.info(msg="Update cycle finished")
    logging.info(msg="*************************************************************************")

main()

for minute in ["00:05", "10:00", "20:00", "30:00", "40:00", "50:00"]:
    schedule.every().hour.at(minute).do(main)

while True:
    schedule.run_pending()
    time.sleep(1)

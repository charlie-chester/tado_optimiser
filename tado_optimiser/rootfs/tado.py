import logging
import yaml
from datetime import datetime
from hass import HomeAssistantAPI

def load_config(url):
    system_file = url
    with open(system_file, "r") as file:
        return yaml.safe_load(file)

logger = logging.getLogger("tado_optimiser")

home_assistant = HomeAssistantAPI()

class Tado:
    def __init__(self, name):
        self.name = name
        self.settings = None
        self.day = None
        self.evening = None
        self.night = None
        self.sun_correction = None
        self.climate = None
        self.connectivity = None
        self.early_start = None
        self.heating = None
        self.humidity = None
        self.overlay = None
        self.power = None
        self.tado_mode = None
        self.temperature = None
        self.window = None
        self.away_time = ""
        self.update_sensors()

    def update_sensors(self):
        # Reloads the settings file then refreshes data
        self.settings = load_config(url="/config/settings.yaml")
        self.day = self.settings["rooms"][self.name]["day"]
        self.evening = self.settings["rooms"][self.name]["evening"]
        self.night = self.settings["rooms"][self.name]["night"]
        self.sun_correction = self.settings["rooms"][self.name]["sun_correction"]

        # Gets these values from Tado direct
        self.climate = home_assistant.get_entity_state(sensor=f"climate.{self.name}")
        self.connectivity = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_connectivity")
        self.early_start = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_early_start")
        self.heating = home_assistant.get_entity_state(sensor=f"sensor.{self.name}_heating")
        self.humidity = home_assistant.get_entity_state(sensor=f"sensor.{self.name}_humidity")
        self.overlay = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_overlay")
        self.power = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_power")
        self.tado_mode = home_assistant.get_entity_state(sensor=f"sensor.{self.name}_tado_mode")
        self.temperature = home_assistant.get_entity_state(sensor=f"sensor.{self.name}_temperature")
        self.window = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_window")

    def set_hvac_mode(self, target_temperature, temp_hour_0, temp_hour_1):
        if temp_hour_0 >= target_temperature or temp_hour_1 >= target_temperature:
            logger.info(msg=f"Temp Hour 0: {temp_hour_0:.2f} or Temp Hour 1: {temp_hour_1:.2f} is the same or higher than the Target Temperature {target_temperature:.2f}")
            home_assistant.set_hvac_mode(entity_id=f"climate.{self.name}", hvac_mode="off")
            logger.info(msg=f"{self.name.upper().replace('_', ' ')} set to OFF")

        elif float(self.temperature) < target_temperature:
            logger.info(msg=f"The Actual Temperature {float(self.temperature):.2f} is lower than the Target Temperature {target_temperature:.2f}")
            home_assistant.set_temperature(entity_id=f"climate.{self.name}", temperature=target_temperature)
            logger.info(msg=f"{self.name.upper().replace('_', ' ')} set to {target_temperature:.2f}")

        elif float(self.temperature) >= target_temperature:
            if float(self.temperature) == target_temperature:
                logger.info(msg=f"The Actual Temperature {float(self.temperature):.2f} is the same as the Target Temperature {target_temperature:.2f}")
            else:
                logger.info(msg=f"The Actual Temperature {float(self.temperature):.2f} is higher than the Target Temperature {target_temperature:.2f}")
            home_assistant.set_hvac_mode(entity_id=f"climate.{self.name}", hvac_mode="off")
            logger.info(msg=f"{self.name.upper().replace('_', ' ')} set to OFF")

    def away_adjust(self, target_temperature):
        if self.tado_mode == "HOME":
            self.away_time = ""
            return 0
        else:
            if self.away_time == "":
                self.away_time = datetime.now()
                logger.info(msg="First cycle in Away mode")
                adjusted_temperature = target_temperature * 0.1
                logger.info(msg=f"{self.name.upper().replace('_', ' ')} in AWAY mode Temperature reduced by 10 % to {target_temperature - adjusted_temperature:.2f}")
                return adjusted_temperature
            else:
                time_difference = (datetime.now() - self.away_time).total_seconds() / 3600
                logger.info(msg=f"Time Now: {datetime.now()} - Away Time: {self.away_time} = {time_difference:.2f} hours")
                if time_difference < 12:
                    logger.info(msg="0 to 12 hour")
                    adjusted_temperature = target_temperature * 0.1
                    logger.info(msg=f"{self.name.upper().replace('_', ' ')} in AWAY mode for {time_difference:.2f} hours. Target Temperature reduced by 10 % to {target_temperature - adjusted_temperature:.2f}")
                    return adjusted_temperature
                elif 12 <= time_difference < 24:
                    logger.info(msg="12 to 24 hours")
                    adjusted_temperature = target_temperature * 0.2
                    logger.info(msg=f"{self.name.upper().replace('_', ' ')} in AWAY mode for {time_difference:.2f} hours. Target Temperature reduced by 20 % to {target_temperature - adjusted_temperature:.2f}")
                    return adjusted_temperature
                else:
                    logger.info(msg="24 hours & over")
                    logger.info(msg=f"{self.name.upper().replace('_', ' ')} in AWAY mode over {time_difference:.2f} hours. Target Temperature set to FROST PROTECTION at 10 C")
                    return 10

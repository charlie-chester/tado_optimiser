import logging
import yaml
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
        self.update_sensors()

    def update_sensors(self):
        # Reloads the settings file then refreshes data
        settings = load_config(url="/config/settings.yaml")
        self.day = settings["rooms"][self.name]["day"]
        self.evening = settings["rooms"][self.name]["evening"]
        self.night = settings["rooms"][self.name]["night"]
        self.sun_correction = settings["rooms"][self.name]["sun_correction"]

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
        if self.tado_mode == "AWAY":
            adjusted_temperature = target_temperature * 0.8
            logger.info(msg=f"{self.name.upper().replace('_', ' ')} in AWAY mode Temperature adjusted from: {target_temperature:.2f} to: {adjusted_temperature:.2f}")
            return adjusted_temperature
        else:
            return target_temperature

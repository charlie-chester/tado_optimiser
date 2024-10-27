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
        self.climate_gas = None
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
        self.electric_override = None
        self.gas_radiator_power = None
        self.electric_radiator_power = None
        self.electric_radiator_name = None
        self.climate_electric = None

    def update_sensors(self):
        # Reloads the settings file then refreshes data
        self.settings = load_config(url="/config/settings.yaml")
        self.day = self.settings["rooms"][self.name]["day"]
        self.evening = self.settings["rooms"][self.name]["evening"]
        self.night = self.settings["rooms"][self.name]["night"]
        self.sun_correction = self.settings["rooms"][self.name]["sun_correction"]
        self.electric_override = self.settings["rooms"][self.name]["electric_override"]
        self.gas_radiator_power = self.settings["rooms"][self.name]["gas_radiator_power"]
        self.electric_radiator_power = self.settings["rooms"][self.name]["electric_radiator_power"]
        self.electric_radiator_name = self.settings["rooms"][self.name]["electric_radiator_name"]

        # Gets these values from Tado direct
        self.climate_gas = home_assistant.get_entity_state(sensor=f"climate.{self.name}")
        self.connectivity = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_connectivity")
        self.early_start = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_early_start")
        self.heating = home_assistant.get_entity_state(sensor=f"sensor.{self.name}_heating")
        self.humidity = home_assistant.get_entity_state(sensor=f"sensor.{self.name}_humidity")
        self.overlay = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_overlay")
        self.power = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_power")
        self.tado_mode = home_assistant.get_entity_state(sensor=f"sensor.{self.name}_tado_mode")
        self.temperature = float(home_assistant.get_entity_state(sensor=f"sensor.{self.name}_temperature"))
        self.window = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_window")

        # Gets these value from electric alternative
        self.climate_electric = home_assistant.get_entity_state(sensor=f"climate.{self.electric_radiator_name}")

    def should_use_electric_override(self, electric_price, gas_price):
        if not self.electric_override:
            return False
        else:
            kwh_gas = self.gas_radiator_power / 1000
            kwh_electric = self.electric_radiator_power / 1000
            gas_cost_per_hour = kwh_gas * gas_price
            electric_cost_per_hour = kwh_electric * electric_price
            logger.info(msg=f"Electric Cost Per Hour {electric_cost_per_hour:.2f} pence")
            logger.info(msg=f"Gas Cost Per Hour {gas_cost_per_hour:.2f} pence")
            return electric_cost_per_hour < gas_cost_per_hour

    def set_hvac_mode(self, target_temperature, temp_hour_0, temp_hour_1, electric_price, gas_price):
        if temp_hour_0 >= target_temperature or temp_hour_1 >= target_temperature:
            logger.info(msg=f"Temp Hour 0: {temp_hour_0:.2f} or Temp Hour 1: {temp_hour_1:.2f} is the same or higher than the Target Temperature {target_temperature:.2f}")

            if self.climate_gas != "off":
                home_assistant.set_hvac_mode(entity_id=f"climate.{self.name}", hvac_mode="off")
            if self.electric_override:
                if self.climate_electric != "off":
                    home_assistant.set_hvac_mode(entity_id=f"climate.{self.electric_radiator_name}", hvac_mode="off")

            logger.info(msg=f"{self.name.upper().replace('_', ' ')} set to OFF")

        elif self.temperature >= target_temperature:
            if self.temperature == target_temperature:
                logger.info(msg=f"The Actual Temperature {self.temperature:.2f} is the same as the Target Temperature {target_temperature:.2f}")
            else:
                logger.info(msg=f"The Actual Temperature {self.temperature:.2f} is higher than the Target Temperature {target_temperature:.2f}")

            if self.climate_gas != "off":
                home_assistant.set_hvac_mode(entity_id=f"climate.{self.name}", hvac_mode="off")
            if self.electric_override:
                if self.climate_electric != "off":
                    home_assistant.set_hvac_mode(entity_id=f"climate.{self.electric_radiator_name}", hvac_mode="off")

            logger.info(msg=f"{self.name.upper().replace('_', ' ')} set to OFF")

        else:
            logger.info(msg=f"The Actual Temperature {self.temperature:.2f} is lower than the Target Temperature {target_temperature:.2f}")
            if self.should_use_electric_override(electric_price=electric_price, gas_price=gas_price):
                logger.info(msg=f"{self.name.upper().replace('_', ' ')} Using electric Override")

                if self.climate_gas != "off":
                    home_assistant.set_hvac_mode(entity_id=f"climate.{self.name}", hvac_mode="off")

                home_assistant.set_hvac_mode(entity_id=f"climate.{self.electric_radiator_name}", hvac_mode="heat")
                home_assistant.set_temperature(entity_id=f"climate.{self.electric_radiator_name}", temperature=target_temperature)
            else:
                if self.electric_override:
                    logger.info(msg=f"{self.name.upper().replace('_', ' ')} Using Gas")
                else:
                    logger.info(msg=f"{self.name.upper().replace('_', ' ')} Electric Override not enabled")

                if self.electric_override:
                    if self.climate_electric != "off":
                        home_assistant.set_hvac_mode(entity_id=f"climate.{self.electric_radiator_name}", hvac_mode="off")

                home_assistant.set_temperature(entity_id=f"climate.{self.name}", temperature=target_temperature)

            logger.info(msg=f"{self.name.upper().replace('_', ' ')} set to {target_temperature:.2f}")

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

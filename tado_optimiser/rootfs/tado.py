import logging
import yaml
from datetime import datetime
from home_assistant_api import HomeAssistantAPI

def load_config(url):
    system_file = url
    with open(system_file, "r") as file:
        return yaml.safe_load(file)

logger = logging.getLogger("tado_optimiser")

home_assistant = HomeAssistantAPI()

# noinspection DuplicatedCode
class Tado:
    def __init__(self, name):
        self.name = name

        # Settings file
        self.settings = None
        self.is_tado = None
        self.gas_climate_entity = None
        self.day = None
        self.evening = None
        self.night = None
        self.electric_override = "False"
        self.gas_radiator_power = None
        self.electric_radiator_power = None
        self.electric_climate_entity = None

        # Generic data
        self.climate_gas = None
        self.current_temperature = None

        # Tado data
        self.connectivity = None
        self.early_start = None
        self.heating = None
        self.humidity = None
        self.overlay = None
        self.power = None
        self.tado_mode = "N/A"
        self.window = None

        # Electric data
        self.climate_electric = None
        
        # Away data
        self.away_time = ""
        
    def update_tado_data(self):
        # Reloads the settings file then refreshes data
        self.settings = load_config(url="/config/settings.yaml")
        self.is_tado = self.settings["rooms"][self.name]["is_tado"]
        self.gas_climate_entity = self.settings["rooms"][self.name]["gas_climate_entity"]
        self.day = self.settings["rooms"][self.name]["day"]
        self.evening = self.settings["rooms"][self.name]["evening"]
        self.night = self.settings["rooms"][self.name]["night"]   
        self.electric_override = self.settings["rooms"][self.name]["electric_override"]
        self.gas_radiator_power = self.settings["rooms"][self.name]["gas_radiator_power"]
        self.electric_radiator_power = self.settings["rooms"][self.name]["electric_radiator_power"]
        self.electric_climate_entity = self.settings["rooms"][self.name]["electric_climate_entity"]

        # Gets generic data
        self.climate_gas = home_assistant.get_entity_state(sensor=self.gas_climate_entity)
        self.current_temperature = float(home_assistant.get_climate_current_temperature(sensor=self.gas_climate_entity))

        # Gets these values from Tado direct
        if self.is_tado:
            self.connectivity = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_connectivity")
            self.early_start = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_early_start")
            self.heating = home_assistant.get_entity_state(sensor=f"sensor.{self.name}_heating")
            self.humidity = home_assistant.get_entity_state(sensor=f"sensor.{self.name}_humidity")
            self.overlay = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_overlay")
            self.power = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_power")
            self.tado_mode = home_assistant.get_entity_state(sensor=f"sensor.{self.name}_tado_mode")
            self.window = home_assistant.get_entity_state(sensor=f"binary_sensor.{self.name}_window")

        # Gets these values from electric alternative
        if self.electric_override:
            self.climate_electric = home_assistant.get_entity_state(sensor=self.electric_climate_entity)

    def calculate_break_even_price(self, gas_price):
        # Calculates the break-even price for electricity to be cheaper than gas
        kwh_gas = self.gas_radiator_power / 1000
        kwh_electric = self.electric_radiator_power / 1000
        gas_cost_per_hour = kwh_gas * gas_price
        break_even_electric_price = gas_cost_per_hour / kwh_electric
        logger.info(msg=f"Break-even Electricity Price: {break_even_electric_price:.2f} pence")
        return break_even_electric_price

    def should_use_electric_override(self, electric_price, gas_price, using_grid):
        # Calculates if electricity is possible & cost-effective returns True or False
        if not self.electric_override:
            return False
        elif not using_grid:
            logger.info(msg="System not using the Grid so skipping Electric Override")
            return False
        else:
            kwh_gas = self.gas_radiator_power / 1000
            kwh_electric = self.electric_radiator_power / 1000
            gas_cost_per_hour = kwh_gas * gas_price
            electric_cost_per_hour = kwh_electric * electric_price
            logger.info(msg=f"Cost per hour: Electric: {electric_cost_per_hour:.2f} | Gas: {gas_cost_per_hour:.2f}")
            self.calculate_break_even_price(gas_price)
            return electric_cost_per_hour < gas_cost_per_hour

    def set_hvac_mode(self, target_temperature, temp_hour_0, temp_hour_1, electric_price, gas_price, using_grid):
        # If the outside temperature in the next 2 hours will meet the target temperature turn off heating
        if temp_hour_0 >= target_temperature or temp_hour_1 >= target_temperature:
            logger.info(msg=f"Temp Hour 0: {temp_hour_0:.2f} or Temp Hour 1: {temp_hour_1:.2f} is the same or higher than the Target Temperature {target_temperature:.2f}")

            if self.climate_gas != "off":
                home_assistant.set_hvac_mode(entity_id=self.gas_climate_entity, hvac_mode="off")
            if self.electric_override:
                if self.climate_electric != "off":
                    home_assistant.set_hvac_mode(entity_id=self.electric_climate_entity, hvac_mode="off")

            logger.info(msg=f"{self.name.upper().replace('_', ' ')} set to OFF")

        # If the room temperature has met the target temperature turn off heating
        elif self.current_temperature >= target_temperature:
            if self.current_temperature == target_temperature:
                logger.info(msg=f"The Actual Temperature {self.current_temperature:.2f} is the same as the Target Temperature {target_temperature:.2f}")
            else:
                logger.info(msg=f"The Actual Temperature {self.current_temperature:.2f} is higher than the Target Temperature {target_temperature:.2f}")

            if self.climate_gas != "off":
                home_assistant.set_hvac_mode(entity_id=self.gas_climate_entity, hvac_mode="off")
            if self.electric_override:
                if self.climate_electric != "off":
                    home_assistant.set_hvac_mode(entity_id=self.electric_climate_entity, hvac_mode="off")

            logger.info(msg=f"{self.name.upper().replace('_', ' ')} set to OFF")

        # If the above 2 fail then it must mean heating is required
        else:
            logger.info(msg=f"The Actual Temperature {self.current_temperature:.2f} is lower than the Target Temperature {target_temperature:.2f}")

            # Checks if you should use electricity and then turns on electricity
            if self.should_use_electric_override(electric_price=electric_price, gas_price=gas_price, using_grid=using_grid):
                if self.climate_gas != "off":
                    home_assistant.set_hvac_mode(entity_id=self.gas_climate_entity, hvac_mode="off")

                home_assistant.set_hvac_mode(entity_id=self.electric_climate_entity, hvac_mode="heat")
                home_assistant.set_temperature(entity_id=self.electric_climate_entity, temperature=target_temperature)
                logger.info(msg=f"{self.name.upper().replace('_', ' ')} using Electricity set to {target_temperature:.2f}")

            # If electric override not possible or electricity not cheaper turn on gas
            else:
                if self.electric_override:
                    if self.climate_electric != "off":
                        home_assistant.set_hvac_mode(entity_id=self.electric_climate_entity, hvac_mode="off")

                if not self.is_tado:
                    home_assistant.set_hvac_mode(entity_id=self.gas_climate_entity, hvac_mode="heat")

                home_assistant.set_temperature(entity_id=self.gas_climate_entity, temperature=target_temperature)
                logger.info(msg=f"{self.name.upper().replace('_', ' ')} using Gas set to {target_temperature:.2f}")

    def away_adjust(self, target_temperature):
        now = datetime.now()

        # If in HOME mode return no reduction
        if self.tado_mode != "AWAY":
            self.away_time = ""
            return 0

        else:
            # If first cycle in AWAY mode reduce by 10%
            if self.away_time == "":
                self.away_time = now
                logger.info(msg="First cycle in Away mode")
                adjusted_temperature = target_temperature * 0.1
                logger.info(msg=f"{self.name.upper().replace('_', ' ')} in AWAY mode Temperature reduced by 10 % to {target_temperature - adjusted_temperature:.2f}")
                return adjusted_temperature

            # Sets different reductions depending on time in AWAY mode
            else:
                time_difference = (now - self.away_time).total_seconds() / 3600
                logger.info(
                    msg=f"Time Now: {now.strftime('%Y-%m-%d %H:%M')} Away Time: {self.away_time.strftime('%Y-%m-%d %H:%M')} = {time_difference:.2f} hours")
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

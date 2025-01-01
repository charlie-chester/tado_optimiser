import json
import logging
import os
import time
from datetime import datetime, timedelta

import requests
from requests.auth import HTTPBasicAuth

from home_assistant_api import HomeAssistantAPI

logger = logging.getLogger("tado_optimiser")

home_assistant = HomeAssistantAPI()

class Octopus:
    def __init__(self, octopus_api, octopus_account):
        self.baseUrl = "https://api.octopus.energy"
        self.account = octopus_account
        self.user_name = octopus_api
        self.pass_word = ""
        self.account_data = {}
        self.account_data_last_updated = ""
        self.agile_rates = {}
        self.agile_rates_last_updated = ""
        self.gas_rates = {}
        self.gas_rates_last_updated = ""

    def update_octopus_data(self):
        # Updates all Octopus data if required
        now = datetime.now()

        # ****************************************************************************************************************
        # Deal with Account data

        # Checks to see if account data files are present and if not runs plan to make new ones
        if not os.path.exists("/config/account_data.json") or not os.path.exists("/config/account_data_last_updated.txt"):
            logger.info(msg="Octopus account data backup files not present running plan to make new ones")
            self.update_account_data()

        # If data files are present but no data in system load them
        elif self.account_data_last_updated == "" or self.account_data == {}:
            with open("/config/account_data.json", "r") as f:
                self.account_data = json.load(f)
            with open("/config/account_data_last_updated.txt", "r") as f:
                self.account_data_last_updated = f.read()

            logger.info(msg="Octopus account data loaded from backup files")

        # Checks last updated time and updates account data if needed
        if (now - datetime.strptime(self.account_data_last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds() > (3600 * 24) - 60:
            self.update_account_data()
        else:
            if (now - datetime.strptime(self.account_data_last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds() > 30:
                logger.info(msg=f"Octopus account data not updated. Last updated: {self.account_data_last_updated}")

        # ****************************************************************************************************************
        # Deal with Agile rates

        # Checks time and updates Agile rates are present and if not runs plan to make new ones
        if not os.path.exists("/config/agile_rates.json") or not os.path.exists("/config/agile_rates_last_updated.txt"):
            logger.info(msg="Agile rates backup files not present running plan to make new ones")
            self.get_agile_rates()

        # If data files are present but no data in system load them
        elif self.agile_rates_last_updated == "" or self.agile_rates == {}: 
            with open("/config/agile_rates.json", "r") as f:
                self.agile_rates = json.load(f)
            with open("/config/agile_rates_last_updated.txt", "r") as f:
                self.agile_rates_last_updated = f.read()

            logger.info(msg="Agile rates loaded from backup files")

        # Checks last updated time and updates Agile rates if needed
        if (now - datetime.strptime(self.agile_rates_last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds() > 3600 - 60:
            self.get_agile_rates() 
        else:
            if (now - datetime.strptime(self.agile_rates_last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds() > 30:
                logger.info(msg=f"Agile rates not updated. Last updated: {self.agile_rates_last_updated}")

        # ****************************************************************************************************************
        # Deal with Gas rates

        # Checks time and updates gas rates  are present and if not runs plan to make new ones
        if not os.path.exists("/config/gas_rates.json") or not os.path.exists("/config/gas_rates_last_updated.txt"):
            logger.info(msg="Gas rates backup files not present running plan to make new ones")
            self.get_gas_rates()

        # If data files are present but no data in system load them
        elif self.gas_rates_last_updated == "" or self.gas_rates == {}: 
            with open("/config/gas_rates.json", "r") as f:
                self.gas_rates = json.load(f)
            with open("/config/gas_rates_last_updated.txt", "r") as f:
                self.gas_rates_last_updated = f.read()

            logger.info(msg="Gas rates loaded from backup files")

        # Checks last updated time and updates gas rates if needed
        if (now - datetime.strptime(self.gas_rates_last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds() > 3600 - 60:
            self.get_gas_rates()
        else:
            if (now - datetime.strptime(self.gas_rates_last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds() > 30:
                logger.info(msg=f"Gas rates not updated. Last updated: {self.agile_rates_last_updated}")

        # ****************************************************************************************************************

        # Creates / updates entities
        self.update_agile_entities()

    def action_get(self, full_url):
        # Main Action-Get function if it fails will stay in loop
        response = requests.get(full_url, auth=HTTPBasicAuth(username=self.user_name, password=self.pass_word))

        status = response.status_code
        if status == 200:
            logger.debug(msg="Octopus data successfully retrieved")
            return response.json()
        else:
            logger.error(msg=f"Error: {response.status_code, response.text}")
            logger.error(msg=f"Error getting Octopus data. Status code: {status} Will try again in 1 minute")
            time.sleep(60)
            self.action_get(full_url=full_url)

    def update_account_data(self):
        # Gets basic account details
        end_point = f"/v1/accounts/{self.account}"
        full_url = self.baseUrl + end_point
        self.account_data = self.action_get(full_url=full_url)
        self.account_data_last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Write formatted json to file & records timestamp
        with open("/config/account_data.json", "w") as f:
            json.dump(self.account_data, f, indent=4)
        with open("/config/account_data_last_updated.txt", "w") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        logger.info(msg=f"Account data updated: {self.account_data_last_updated}")

    def get_agile_rates(self):
        # Gets Agile rates from account details
        for meter in self.account_data["properties"][0]["electricity_meter_points"]:
            if not meter["is_export"]:
                for agreement in meter["agreements"]:
                    valid_from = datetime.strptime(agreement["valid_from"][:10], "%Y-%m-%d").date()
                    valid_to = datetime.strptime(agreement["valid_to"][:10], "%Y-%m-%d").date()

                    if valid_from < datetime.now().date() < valid_to:
                        tariff_code = agreement["tariff_code"]
                        product_code = tariff_code[5:-2]
                        end_point = f"/v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/"
                        full_url = self.baseUrl + end_point
                        self.agile_rates = self.action_get(full_url=full_url)
                        self.agile_rates_last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        # Write formatted json to file & records timestamp
                        with open("/config/agile_rates.json", "w") as f:
                            json.dump(self.agile_rates, f, indent=4)

                        with open("/config/agile_rates_last_updated.txt", "w") as f:
                            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                        logger.info(msg=f"Agile rates updated: {self.agile_rates_last_updated}")

    def get_gas_rates(self):
        # Gets gas rates from account details
        for agreement in self.account_data["properties"][0]["gas_meter_points"][0]["agreements"]:
            valid_from = datetime.strptime(agreement["valid_from"][:10], "%Y-%m-%d").date()
            valid_to = agreement["valid_to"]

            if valid_from < datetime.now().date() and valid_to is None:
                tariff_code = agreement["tariff_code"]
                product_code = tariff_code[5:-2]
                end_point = f"/v1/products/{product_code}/gas-tariffs/{tariff_code}/standard-unit-rates/"
                full_url = self.baseUrl + end_point
                self.gas_rates = self.action_get(full_url=full_url)
                self.gas_rates_last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Write formatted json to file & records timestamp
                with open("/config/gas_rates.json", "w") as f:
                    json.dump(self.gas_rates, f, indent=4)
                with open("/config/gas_rates_last_updated.txt", "w") as f:
                    f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                logger.info(msg=f"Gas rates updated: {self.agile_rates_last_updated}")

    def get_current_electricity_price(self, offset):
        # Gets the Agile price based on the offset passed
        now = datetime.now()
        for rate in self.agile_rates["results"]:
            valid_from = datetime.strptime(rate["valid_from"], "%Y-%m-%dT%H:%M:%SZ")
            valid_to = datetime.strptime(rate["valid_to"], "%Y-%m-%dT%H:%M:%SZ")

            if valid_from <= (now + timedelta(minutes=offset)) < valid_to:
                logger.debug(msg=f"Price: {rate['value_inc_vat']} - From: {rate['valid_from'][:-1].replace('T', ' ')} To: {rate['valid_to'][:-1].replace('T', ' ')}")
                return rate["value_inc_vat"], rate["valid_from"], rate["valid_to"]

    def get_current_gas_price(self):
        # Gets the current gas price
        now = datetime.now()
        for rate in self.gas_rates["results"]:
            payment_method = rate["payment_method"]
            valid_from = datetime.strptime(rate["valid_from"], "%Y-%m-%dT%H:%M:%SZ")
            valid_to = rate["valid_to"]

            # if the date is None, set it to a date in the future + 500 days
            if valid_to is None:
                valid_to = now + timedelta(days=500)
            else:
                valid_to = datetime.strptime(rate["valid_to"], "%Y-%m-%dT%H:%M:%SZ")

            logger.debug(msg=f"Valid from: {valid_from} - Valid to: {valid_to} - Payment method: {payment_method}")
            
            if valid_from <= now < valid_to and payment_method == "DIRECT_DEBIT":
                return rate["value_inc_vat"]

    def update_agile_entities(self):
        # Creates / updates entities
        for offset in range(0, 271, 30):
            price, time_from, time_to = self.get_current_electricity_price(offset=offset)
            sensor = f"sensor.agile_electricity_price_{offset}"
            payload = {
                "state": price,
                "attributes": {
                    "unit_of_measurement": "p",
                    "friendly_name": f"{time_from[11:16]} - {time_to[11:16]}",
                    "icon": "mdi:currency-gbp",
                }
            }
            home_assistant.update_entity(sensor=sensor, payload=payload)

        logger.info(msg="Agile entities created / updated")

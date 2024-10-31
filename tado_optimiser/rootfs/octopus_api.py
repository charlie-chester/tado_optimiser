import logging
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth

logger = logging.getLogger("tado_optimiser")

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

    def action_get(self, fullUrl):
        response = requests.get(fullUrl, auth=HTTPBasicAuth(username=self.user_name, password=self.pass_word))
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(msg=f"Error: {response.status_code, response.text}")

    def update_account_details(self):
        now = datetime.now()
        if self.account_data_last_updated == "" or (now - datetime.strptime(self.account_data_last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds() > 3600:
            endPoint = f"/v1/accounts/{self.account}"
            fullUrl = self.baseUrl + endPoint
            self.account_data = self.action_get(fullUrl=fullUrl)
            self.account_data_last_updated = now.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(msg=f"Account details updated: {self.account_data_last_updated}")
        else:
            logger.info(msg=f"Account details not updated. Last updated: {self.account_data_last_updated}")

    def update_agile_rates(self):
        self.update_account_details()
        now = datetime.now()
        if self.agile_rates_last_updated == "" or (now - datetime.strptime(self.agile_rates_last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds() > 3600:
            for meter in self.account_data["properties"][0]["electricity_meter_points"]:
                if not meter["is_export"]:
                    for agreement in meter["agreements"]:
                        valid_from = datetime.strptime(agreement["valid_from"][:10], "%Y-%m-%d").date()
                        valid_to = datetime.strptime(agreement["valid_to"][:10], "%Y-%m-%d").date()

                        if valid_from < datetime.now().date() < valid_to:
                            tariff_code = agreement["tariff_code"]
                            product_code = tariff_code[5:-2]
                            endPoint = f"/v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/"
                            fullUrl = self.baseUrl + endPoint
                            self.agile_rates = self.action_get(fullUrl=fullUrl)
                            self.agile_rates_last_updated = now.strftime("%Y-%m-%d %H:%M:%S")
                            logger.info(msg=f"Agile rates updated: {self.agile_rates_last_updated}")
        else:
            logger.info(msg=f"Agile rates not updated. Last updated: {self.agile_rates_last_updated}")

    def update_gas_rates(self):
        self.update_account_details()
        now = datetime.now()
        if self.gas_rates_last_updated == "" or (now - datetime.strptime(self.gas_rates_last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds() > 3600:
            for agreement in self.account_data["properties"][0]["gas_meter_points"][0]["agreements"]:
                valid_from = datetime.strptime(agreement["valid_from"][:10], "%Y-%m-%d").date()
                valid_to = agreement["valid_to"]

                if valid_from < datetime.now().date() and valid_to is None:
                    tariff_code = agreement["tariff_code"]
                    product_code = tariff_code[5:-2]
                    endPoint = f"/v1/products/{product_code}/gas-tariffs/{tariff_code}/standard-unit-rates/"
                    fullUrl = self.baseUrl + endPoint
                    self.gas_rates = self.action_get(fullUrl=fullUrl)
                    self.gas_rates_last_updated = now.strftime("%Y-%m-%d %H:%M:%S")
                    logger.info(msg=f"Gas rates updated: {self.agile_rates_last_updated}")
        else:
            logger.info(msg=f"Gas rates not updated. Last updated: {self.agile_rates_last_updated}")

    def get_current_electricity_price(self):
        self.update_agile_rates()
        now = datetime.now()
        for rate in self.agile_rates["results"]:
            valid_from = datetime.strptime(rate["valid_from"], "%Y-%m-%dT%H:%M:%SZ")
            valid_to = datetime.strptime(rate["valid_to"], "%Y-%m-%dT%H:%M:%SZ")

            if valid_from <= now < valid_to:
                logger.info(msg=f"Price: {rate['value_inc_vat']} - From: {rate['valid_from'][:-1].replace('T', ' ')} - To: {rate['valid_to'][:-1].replace('T', ' ')}")
                return rate["value_inc_vat"]

    def get_current_gas_price(self):
        self.update_gas_rates()
        now = datetime.now()
        for rate in self.gas_rates["results"]:
            valid_from = datetime.strptime(rate["valid_from"], "%Y-%m-%dT%H:%M:%SZ")
            valid_to = rate["valid_to"]
            payment_method = rate["payment_method"]

            if valid_from <= now and valid_to is None and payment_method == "DIRECT_DEBIT":
                logger.info(msg=f"Price: {rate['value_inc_vat']} - From: {rate['valid_from'][:-1].replace('T', ' ')} - To: {rate['valid_to']}")
                return rate["value_inc_vat"]

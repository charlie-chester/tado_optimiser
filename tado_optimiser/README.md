#  Tado Optimiser
## Tado Optimiser Add-on

In an effort to learn how to code—especially to develop a Home Assistant addon—I came up with the idea of improving my Tado system.

I’ve added features that help in my specific situation. If you think they might benefit you too, feel free to install the addon and help me test my coding.

This addon works with any home heating system that uses smart TRVs controlled within Home Assistant via the “Climate” feature. When a radiator calls for heat, its system automatically controls the boiler—just like with Tado, where activating a TRV triggers the boiler to turn on or off.

If you only have Sonoff TRVs, this addon will open the valve when heat is required, but it won’t be able to fire up the boiler.

Additionally, the addon allows you to control an electric radiator (also managed in Home Assistant via the “Climate” feature), providing the option to use electricity instead of gas when prices are cheaper.

While you could use this addon to control all your TRVs, the best approach might be to include only those that you would want to switch to electric heating as an override.

In my setup, I have eight Tado TRVs. I let Tado manage seven of them, but for my conservatory, I’ve set up an electric radiator. This setup allows me to take advantage of lower electricity prices at night.

To use Tado Optimiser, you need to have the following: -

- [ ] A Tado system or similar set up with the ability to control the TRV's with the "climate" feature in Home Assistant.
- [ ] An OpenWeather API 3.0 key. Available here https://openweathermap.org You will need to subscribe for a key. This is free and you'll get 1,000 calls per day. Make sure that when you get the key, you set the daily amount to 1,000 or less to make sure.
- [ ] An Octopus account, and you know the API key and account number.
- [ ] If using an Electric Override device, it must be able to be controlled using the "climate" feature in Home Assistant.

### My basic dashboard.

<img src="https://github.com/charlie-chester/tado_optimiser/blob/main/tado_optimiser/images/dash_1.png?raw=true" alt="Basic Dashboard" width="800">

### The way my system works: -
- [ ] The logic runs every 5 minutes.
- [ ] The OpenWeather API is called, and all the Hourly & Daily Entities are created in Home Assistant.
- [ ] The Octopus API is called to find out your tariffs so the current Gas & Electricity price can be obtained. Entities are then created. In the illustration, I'm using Octopus Agile, but it should work with other tariffs within Octopus.
- [ ] Each room in your house is then evaluated to see if it needs heat. Considerations are made to the future outside air temperature and the price of the current Gas & Electricity. If Electricity is cheaper any Electrical Override set up will be used instead of the Gas. The electric override will only be used if the system is currently using the grid. This was added so it wouldn't interrupt Predbat. 

### The Settings file

<img src="https://github.com/charlie-chester/tado_optimiser/blob/main/tado_optimiser/images/settings_1.png?raw=true" alt="Settings File" width="400">

- [ ] Day is from Sunrise to 60 minutes before Sunset.
- [ ] Evening is 60 minutes before Sunset to Midnight.
- [ ] Night is everything else.
- [ ] Radiator power in watts.
- [ ] Temperatures in centigrade.

The settings file is located in the /addon_configs folder. It will be created on the first run.

### Home Assistant Entities

The YAML for the Weather Entities are as follows: -

### Current
```yaml
type: entities
entities:
  - entity: sensor.tado_optimiser_current
    secondary_info: last-updated
title: Tado Optimiser Current Weather
```
### Hourly
```yaml
type: entities
entities:
  - entity: sensor.tado_optimiser_hour_0
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_hour_1
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_hour_2
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_hour_3
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_hour_4
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_hour_5
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_hour_6
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_hour_7
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_hour_8
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_hour_9
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_hour_10
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_hour_11
    secondary_info: last-updated
title: Tado Optimiser Hourly Forecast
show_header_toggle: false
state_color: false
```
### Daily
```yaml
type: entities
entities:
  - entity: sensor.tado_optimiser_day_0
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_day_1
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_day_2
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_day_3
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_day_4
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_day_5
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_day_6
    secondary_info: last-updated
  - entity: sensor.tado_optimiser_day_7
    secondary_info: last-updated
title: Tado Optimiser Daily Forecast
```
### 30 Minute Prices
```yaml
type: entities
entities:
  - entity: sensor.agile_electricity_price_0
    secondary_info: last-updated
  - entity: sensor.agile_electricity_price_30
    secondary_info: last-updated
  - entity: sensor.agile_electricity_price_60
    secondary_info: last-updated
  - entity: sensor.agile_electricity_price_90
    secondary_info: last-updated
  - entity: sensor.agile_electricity_price_120
    secondary_info: last-updated
  - entity: sensor.agile_electricity_price_150
    secondary_info: last-updated
  - entity: sensor.agile_electricity_price_180
    secondary_info: last-updated
  - entity: sensor.agile_electricity_price_210
    secondary_info: last-updated
  - entity: sensor.agile_electricity_price_240
    secondary_info: last-updated
  - entity: sensor.agile_electricity_price_270
    secondary_info: last-updated
title: Tado Optimiser Agile Prices
```
### Room Target Temperatures
```yaml
type: tile
entity: sensor.conservatory_target_temperature
layout_options:
  grid_columns: 2
  grid_rows: 1
```

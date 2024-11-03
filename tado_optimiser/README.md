#  Tado Optimiser
## Tado Optimiser Add-on

In an attempt to learn how to "Code" and especially "Code"
an addon for Home Assistant, I came up with the idea to make my Tado system better.

I think Tado on its own is brilliant, and I am in no way saying that it's not.
I've just added a couple of features that help me in my situation.
If you think this may help you too, then feel free to install and help me test my coding.

To use Tado Optimiser, you need to have the following: -

- [ ] A Tado system set up and the Tado Integration in Home Assistant.
- [ ] An OpenWeather API 3.0 key. Available here https://openweathermap.org You will need to subscribe for a key, but you also get 10,000 per day free so won't go over. Make sure that when you get the key, you set the daily amount to 1000 or less to make sure.
- [ ] An Octopus account, and you know the API key and account number.

### My basic dashboard.

<img src="/images/dash_1.png" alt="Alt text" width="3138">

### The way my system works: -
- [ ] The logic runs every 10 minutes.
- [ ] The OpenWeather API is called, and all the Hourly & Daily Entities are created in Home Assistant.
- [ ] The Octopus API is called to find out your tariffs so the current Gas & Electricity price can be obtained. Entities are then created. In the illustration, I'm using Octopus Agile, but it should work other tariffs.
- [ ] Each room in your house is then evaluated to see if it needs heat. Considerations are made to the future outside air temperature. Also during this calculation, the price of Gas & Electricity is tested, and if Electricity is cheaper than any Electrical Override set up will be used instead of the Gas  

### The Settings file

<img src="/images/settings_1.png" alt="Alt text" width="400">

- [ ] Day is from Sunrise to Sunset.
- [ ] Evening is Sunset to Midnight.
- [ ] Night is everything else.
- [ ] Radiator power is in watts.
- [ ] Temperatures in centigrade.

The settings file is located in the /addon_configs folder. It will be created on the first run.


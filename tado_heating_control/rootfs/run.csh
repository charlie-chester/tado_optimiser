#!/bin/csh -f

while (1)
    echo "Starting Tado Heating Control"
    python3 hass.py
    echo "Tado Heating Control crashed. Restarting in 5 seconds..."
    sleep 5
end

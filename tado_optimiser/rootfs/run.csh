#!/bin/csh -f

while (1)
    echo "Starting Tado Optimiser"
    python3 hass.py
    echo "Tado Optimiser crashed. Restarting in 5 seconds..."
    sleep 5
end
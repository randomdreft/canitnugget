#!/bin/bash

# Script om McDonald's nugget prijzen bij te werken
# Draait elke 8 uur via cron

cd /var/www/canitnugget

# Controleer of Python en benodigde packages geïnstalleerd zijn
if ! command -v python3 &> /dev/null; then
    echo "Python3 niet gevonden, installeer eerst Python3"
    exit 1
fi

# Installeer benodigde packages als ze niet bestaan
if ! python3 -c "import requests, bs4" 2>/dev/null; then
    echo "Installeer benodigde Python packages..."
    pip3 install requests beautifulsoup4
fi

# Voer de price scraper uit
echo "Prijzen bijwerken op $(date)..."
python3 price_scraper.py

# Log de update
echo "Prijzen bijgewerkt op $(date)" >> /var/www/canitnugget/price_update.log

echo "Klaar!"

#!/usr/bin/env python3
"""
McDonald's Nugget Price Scraper
Downloadt en bewaart de actuele prijzen van chicken mcnuggets (geen veggie/spicy)
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import re

def scrape_mcdonalds_prices():
    """Scrape McDonald's website voor chicken mcnugget prijzen"""
    
    # URL van de McDonald's menu pagina
    url = "https://mcdonaldsmenu.nl/#mcdonalds-prijzen"
    
    try:
        # Headers om te voorkomen dat we geblokkeerd worden
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Scraping {url}...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Zoek naar chicken mcnugget prijzen (geen veggie, geen spicy)
        nugget_prices = {}
        
        # Zoek in alle tabellen naar nugget prijzen
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    text = ' '.join(cell.get_text(strip=True) for cell in cells).lower()
                    
                    # Zoek alleen naar chicken mcnuggets (geen veggie, geen spicy)
                    # Specifiekere filter: moet "chicken mcnuggets" bevatten
                    if 'chicken mcnuggets' in text and 'veggie' not in text and 'spicy' not in text:
                        print(f"DEBUG: Gevonden chicken mcnuggets rij: '{text}'")
                        
                        # Probeer de prijs te extraheren
                        price_text = cells[-1].get_text(strip=True)
                        if '€' in price_text:
                            # Haal de prijs eruit met regex - zoek naar het laatste € teken
                            price_match = re.search(r'€\s*([\d,]+)', price_text)
                            if price_match:
                                price = price_match.group(1).replace(',', '.')
                                try:
                                    price_float = float(price)
                                    
                                    # Bepaal het aantal nuggets uit de tekst
                                    # Gebruik exacte patronen om verwarring te voorkomen
                                    if 'chicken mcnuggets 6' in text and 6 not in nugget_prices:
                                        nugget_prices[6] = price_float
                                        print(f"6 chicken mcnuggets: €{price_float}")
                                    elif 'chicken mcnuggets 9' in text and 9 not in nugget_prices:
                                        nugget_prices[9] = price_float
                                        print(f"9 chicken mcnuggets: €{price_float}")
                                    elif 'chicken mcnuggets 20' in text and 20 not in nugget_prices:
                                        nugget_prices[20] = price_float
                                        print(f"20 chicken mcnuggets: €{price_float}")
                                    
                                except ValueError:
                                    continue
        
        # Als we geen prijzen hebben gevonden, gebruik standaard prijzen
        if not nugget_prices:
            print("Geen prijzen gevonden, gebruik standaard prijzen...")
            nugget_prices = {
                6: 3.55,
                9: 4.80,
                20: 9.50
            }
        
        # Zorg ervoor dat alle benodigde aantallen aanwezig zijn (geen 4 meer)
        required_sizes = [6, 9, 20]
        for size in required_sizes:
            if size not in nugget_prices:
                print(f"Waarschuwing: Geen prijs gevonden voor {size} nuggets, gebruik standaard prijs")
                if size == 6:
                    nugget_prices[size] = 3.55
                elif size == 9:
                    nugget_prices[size] = 4.80
                elif size == 20:
                    nugget_prices[size] = 9.50
        
        # Sla de prijzen op met timestamp
        price_data = {
            'timestamp': datetime.now().isoformat(),
            'prices': nugget_prices,
            'source': url,
            'note': 'Alleen chicken mcnuggets (geen veggie/spicy)'
        }
        
        # Schrijf naar JSON bestand
        with open('/var/www/canitnugget/prices.json', 'w') as f:
            json.dump(price_data, f, indent=2)
        
        print(f"Prijzen opgeslagen: {nugget_prices}")
        return nugget_prices
        
    except Exception as e:
        print(f"Fout bij scrapen: {e}")
        
        # Probeer bestaande prijzen te laden
        try:
            if os.path.exists('/var/www/canitnugget/prices.json'):
                with open('/var/www/canitnugget/prices.json', 'r') as f:
                    price_data = json.load(f)
                print(f"Bestaande prijzen geladen: {price_data['prices']}")
                return price_data['prices']
        except:
            pass
        
        # Fallback naar standaard prijzen (geen 4 meer)
        return {
            6: 3.55,
            9: 4.80,
            20: 9.50
        }

if __name__ == "__main__":
    scrape_mcdonalds_prices()

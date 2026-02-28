# Can It Nugget? 🍗

**Check of je favoriete aantal McNuggets te bestellen is bij McDonald's.**

[canitnugget.nl](https://canitnugget.nl)

Je wilt 14 nuggets. Kan dat? Nope. 15? Jawel (6 + 9). Dit is het probleem waar je niet om vroeg, maar nu niet meer zonder kunt.

## Hoe werkt het?

McDonald's verkoopt Chicken McNuggets in verpakkingen van **6**, **9** en **20**. Niet elk aantal is te maken met een combinatie van die verpakkingen. Can It Nugget berekent:

1. **Of** het gevraagde aantal mogelijk is
2. **Welke combinatie** het goedkoopst is
3. **Wat het kost** op basis van actuele prijzen

### De wiskunde

Dit is een variant van het [Frobenius-probleem](https://nl.wikipedia.org/wiki/Munteenhedenprobleem) (ook bekend als het Chicken McNugget Theorem). Met verpakkingen van 6, 9 en 20 is **43** het grootste aantal dat je *niet* kunt bestellen. Elk getal boven 43 is altijd mogelijk.

De site gebruikt dynamisch programmeren om de goedkoopste combinatie te vinden.

### Voorbeelden

| Aantal | Mogelijk? | Combinatie |
|--------|-----------|------------|
| 12 | Ja | 6 + 6 |
| 14 | Nee | — |
| 15 | Ja | 6 + 9 |
| 26 | Ja | 20 + 6 |
| 43 | Nee | Grootste onmogelijke getal! |
| 44+ | Altijd | Altijd mogelijk |

## Prijzen

Prijzen worden automatisch gescrapet van [mcdonaldsmenu.nl](https://mcdonaldsmenu.nl) met een Python-script. Bij falen valt de site terug op standaardprijzen.

| Bestand | Functie |
|---------|---------|
| `price_scraper.py` | Scrapet actuele McNugget-prijzen |
| `update_prices.sh` | Cron wrapper voor de scraper |
| `prices.json` | Gecachte prijzen met timestamp |

## Zelf draaien

Open `index.html` in je browser — klaar. De prijsscraper is optioneel.

```bash
# Optioneel: prijzen updaten
pip install requests beautifulsoup4
python3 price_scraper.py
```

## Technisch

- **Frontend**: vanilla HTML + CSS + JavaScript, geen dependencies
- **Algoritme**: dynamisch programmeren voor optimale combinatie
- **Prijzen**: Python scraper met BeautifulSoup, fallback naar hardcoded prijzen
- **Responsive**: werkt op desktop en mobiel

## Licentie

Public domain — gebruik het, fork het, bestel nuggets.

# Can It Nugget? 🍗

**Check of je favoriete aantal McNuggets te bestellen is bij McDonald's.**

[canitnugget.nl](https://canitnugget.nl)

Je wilt 14 nuggets. Kan dat? Nope. 15? Jawel (6 + 9). Dit is het probleem waar je niet om vroeg, maar nu niet meer zonder kunt.

## Hoe werkt het?

McDonald's verkoopt Chicken McNuggets in verpakkingen van **6**, **9** en **20**. Niet elk aantal is te maken met een combinatie van die verpakkingen. Can It Nugget berekent:

1. **Of** het gevraagde aantal mogelijk is
2. **Welke combinatie** het goedkoopst is
3. **Wat het kost** op basis van actuele bezorgprijzen, ook per nugget

Verder:

- **Deelbare link**: de adresbalk volgt je invoer (`?n=43`, met `&verspil=1` in verspillingsmodus). Met de knop *Deel dit* deel je het antwoord (op de telefoon via het deelmenu, anders naar het klembord).
- **Alle manieren**: onder het antwoord een ingeklapte lijst van elke combinatie die precies jouw aantal maakt, op prijs gesorteerd (bij grote aantallen de 20 goedkoopste).
- **Bestellen voor een groep**: aantal personen × nuggets per persoon; de goedkoopste bestelling voor minstens dat aantal, bestelbare aantallen vlakbij, eerlijk verdelen en het Tikkie-bedrag per persoon.
- **Budgetmodus**: vul een bedrag in (`15`, `15,50`, `€ 15`) en zie hoeveel nuggets je er maximaal voor krijgt, met de combinatie en wat je overhoudt (tot € 1.000).
- **Getallenrooster**: een ingeklapt spiekrooster van 1 t/m 100 (op de telefoon 60) met welke aantallen wel en niet kunnen. Staat bewust dicht: zelf ontdekken is leuker.
- **Sausjes, calorieën en Big Macs**: bij jouw bestelling het aantal sausjes (onze aanname, zelf aan te passen), kcal/vet/zout met fiets- en wandelminuten (voedingswaarde van mcdonalds.com/nl) en de nugget-index: hoeveel Big Macs of maanden Netflix je voor hetzelfde geld had.
- **Uitdaging van de dag**: elke dag één aantal (uit de datum, voor iedereen hetzelfde). Kan het, en wat is de goedkoopste combinatie? Met reeks 🔥 en een deeltekst zonder spoilers.
- **Doosjesspeeltuin**: verzin je eigen doosmaten en zie het grootste aantal dat nooit kan, hoeveel er nooit kunnen en een minirooster. Met een ggd groter dan 1 kan er oneindig veel niet.
- **Prijs per nugget per doos**: bij de verpakkingen staat ook de prijs per nugget, met een 👑 voor de voordeligste. Dat is niet vanzelf de grootste doos: op dit moment is de 9 per nugget goedkoper dan de 20.
- **Waar komen de prijzen vandaan?**: onder de verpakkingen één korte regel met soort prijs, aantal filialen en datum (na 3 dagen met leeftijd erbij, na 7 dagen *mogelijk verouderd*). Het (i) klapt een tabel open met de prijzen per filiaal en platform, de mediaan en een link om zelf een winkelprijs te melden.
- **Prijsgeschiedenis**: ingeklapt, en `history.json` wordt pas opgehaald als je hem openklapt. Nuggets 6/9/20 per kwartaal sinds 2021, als prijs per doos of per nugget (wie was wanneer het voordeligst?), optioneel met de Veggie Nuggets als stippellijn (historisch: ze staan sinds 2025 niet meer op het menu en zitten dus niet in de calculator). Daaronder de Big Mac sinds 1987: winkelprijs volgens The Economist (met guldens), het eurozone-gemiddelde als gelabelde opvulling voor 2000–2010 en de bezorgprijs. Met tooltips, toetsenbordbediening en elke grafiek ook als tabel.
- **Waarom 43?**: ingeklapte uitleg over het McNugget-getal, uitgerekend uit de doosjes die er zijn.
- **Paaseieren** bij een paar bijzondere aantallen. Probeer 42 maar eens.

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

**McDonald's Nederland publiceert zelf geen prijzen**, en prijzen verschillen
per filiaal. De "menuprijzen"-sites die in Google bovenaan staan verzinnen of
kopiëren hun cijfers; die gebruiken we niet.

Wat wel echt is: de menukaarten van filialen op **Thuisbezorgd** en **Uber
Eats**. Elke ochtend meet de scraper in [`scraper/`](scraper/) een vast mandje
van tien filialen verspreid over het land en publiceert per doosje de
**mediaan**. Dat zijn dus **bezorgprijzen** — doorgaans 10–35% duurder dan aan
de balie — en zo staan ze ook in `prices.json`
(`"kind": "bezorgprijs"`, `"source": "Thuisbezorgd/Uber Eats, mediaan van 10 filialen"`).
De site zegt dat er ook bij ("Bezorgprijzen, mediaan van 10 filialen") en toont
per filiaal wat er gemeten is. Wie in de winkel een prijs ziet, kan die
[melden via een issue](https://github.com/randomdreft/canitnugget/issues/new).

Mislukt de meting, dan blijft het vorige `prices.json` gewoon staan met zijn
oude datum, zodat de site laat zien dat de prijzen verouderd zijn. De scraper
vult nooit zelf verzonnen of ingebouwde prijzen in. Alleen als `prices.json`
helemaal niet te laden is, valt de site terug op de laatst geziene prijzen in
de browser, of op een ingebouwde reserve (de mediaan van 29 september 2026),
en zegt dat er dan duidelijk bij.

### Prijsgeschiedenis

`history.json` bevat:

- **Nuggets 6/9/20 (2021–nu)** en **Veggie Nuggets (2021–mei 2025**, daarna van
  het menu): mediaan per kwartaal van gearchiveerde Thuisbezorgd- en Uber
  Eats-menu's uit het [Internet Archive](https://web.archive.org/), aangevuld
  met de dagelijkse metingen. Ook bezorgprijzen. Elke losse meting staat erbij,
  met een link naar de gearchiveerde pagina.
- **Big Mac**: dezelfde bezorgprijs-mediaan, plus de winkelprijs volgens
  [The Economist](https://github.com/TheEconomist/big-mac-data): Nederland
  1987–1999 (guldens, omgerekend tegen 2,20371) en 2011–nu, met het
  eurozone-gemiddelde als duidelijk gelabelde opvulling voor 2000–2010.

Methode, schema en beheer: [`scraper/README.md`](scraper/README.md).

| Bestand | Functie |
|---------|---------|
| `scraper/nugget_prijzen.py` | Dagelijkse meting → `prices.json` + `history.json` |
| `scraper/backfill_wayback.py` | Geschiedenis uit het Internet Archive en The Economist |
| `scraper/filialen.json` | Het vaste mandje filialen |
| `prices.json` | Actuele prijzen (kopie; live versie op de server) |
| `history.json` | Prijsgeschiedenis (kopie; live versie op de server) |

## Zelf draaien

Open `index.html` in je browser — klaar. De prijsscraper is optioneel en heeft
alleen Python 3 en Google Chrome nodig:

```bash
python3 scraper/nugget_prijzen.py --droog --alleen alkmaar
```

## Technisch

- **Frontend**: vanilla HTML + CSS + JavaScript, geen dependencies
- **Algoritme**: dynamisch programmeren voor optimale combinatie
- **Prijzen**: Python-scraper (alleen standaardbibliotheek) met headless Chrome, dagelijks via een systemd-timer
- **Responsive**: werkt op desktop en mobiel; op de telefoon staat het antwoord direct onder het invoerveld
- **Licht en donker**: volgt de systeeminstelling (`prefers-color-scheme`); alle kleuren zijn CSS-tokens op `:root`, getoetst op WCAG AA
- **Delen**: favicon (`favicon.svg` + PNG/ICO), Open Graph-afbeelding `og-image.png` (bron: `bron/og-image.html`)

## Bijdragen

Hulp is welkom! Je hoeft geen programmeur te zijn om mee te doen.

### Een idee of een fout gevonden?

Maak een [issue](https://github.com/randomdreft/canitnugget/issues/new) aan. Beschrijf wat je zag of wat je zou willen, bijvoorbeeld:

- een prijs die niet klopt;
- een aantal waarvoor de site een verkeerde combinatie geeft;
- iets dat er raar uitziet op je telefoon;
- een leuk idee voor de site.

Een schermafbeelding en het aantal nuggets dat je invoerde helpen enorm.

### Zelf iets aanpassen?

1. **Fork** deze repository (knop rechtsboven op GitHub).
2. Maak je wijziging in je eigen kopie. Test het door `index.html` in je browser te openen.
3. Open een **pull request** met een korte uitleg van wat je veranderd hebt en waarom.

Houd een pull request klein en gericht op één ding; dat bekijkt en verwerkt het snelst. Twijfel je of iets gewenst is? Open dan eerst een issue om het te bespreken.

Een paar uitgangspunten:

- De site blijft **vanilla HTML, CSS en JavaScript** zonder dependencies of buildstap.
- Teksten op de site en in de repository zijn **Nederlands**.
- Het moet blijven werken op **mobiel**.

## Licentie

Public domain — gebruik het, fork het, bestel nuggets.

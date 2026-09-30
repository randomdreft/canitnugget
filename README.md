# Can It Nugget? 🍗

**Check of je favoriete aantal McNuggets te bestellen is bij McDonald's.**

[canitnugget.nl](https://canitnugget.nl)

Je wilt 14 nuggets. Kan dat? Nope. 15? Jawel (6 + 9). Dit is het probleem waar je niet om vroeg, maar nu niet meer zonder kunt.

## Hoe werkt het?

McDonald's verkoopt Chicken McNuggets in doosjes van **6**, **9** en **20**. Niet elk aantal is met die doosjes te maken. Typ een aantal en Can It Nugget zegt meteen:

1. **of** het kan;
2. **welke combinatie** het goedkoopst is;
3. **wat het kost**, ook per nugget, op basis van actuele bezorgprijzen.

### Bovenaan: simpel

Eén invoerveld, direct antwoord. Verder alleen:

- **Verspillingsmodus**: bestel meer dan je nodig hebt als dat goedkoper is. Ook zonder die modus krijg je een tip als dat zo is ("voor € 0,10 minder krijg je 20 nuggets").
- **Deelbare link**: de adresbalk volgt je invoer (`?n=43`, met `&verspil=1` in verspillingsmodus), en *Deel dit* deelt het antwoord.
- **Paaseieren** bij een paar bijzondere aantallen. Probeer 42 maar eens.

### Onder de vouw: voor wie meer wil

Alles hieronder staat ingeklapt, zodat de bovenkant simpel blijft.

| Onderdeel | Wat het doet |
|---|---|
| **Alle manieren** | Elke combinatie die precies jouw aantal maakt, op prijs gesorteerd |
| **Bestellen voor een groep** | Personen × nuggets per persoon → goedkoopste bestelling, eerlijk verdelen, Tikkie-bedrag |
| **Budgetmodus** | Hoeveel nuggets krijg je maximaal voor `€ 15`? |
| **Aantal vs. prijs** | Grafiek van de goedkoopste prijs per aantal. *Spoiler*: verklapt welke aantallen niet kunnen |
| **Getallenrooster** | Spiekrooster 1–100 van wat wel en niet kan. Bewust dicht: zelf ontdekken is leuker |
| **Sausjes, calorieën en Big Macs** | Sausjes (onze aanname, zelf aan te passen), kcal met fietsminuten, en de nugget-index |
| **Uitdaging van de dag** | Elke dag één aantal voor iedereen. Kan het? Met reeks 🔥 en een deeltekst zonder spoilers |
| **Doosjesspeeltuin** | Verzin eigen doosmaten en zie het grootste aantal dat nooit kan |
| **Waar komen de prijzen vandaan?** | Prijzen per filiaal, de mediaan, en een link om een winkelprijs te melden |
| **Prijsgeschiedenis** | Nuggets per kwartaal sinds 2021 (per doos of per nugget, optioneel veggie) en de Big Mac sinds 1987 |
| **Waarom 43?** | Uitleg over het McNugget-getal, uitgerekend uit de doosjes |

### De wiskunde

Dit is een variant van het [Frobenius-probleem](https://nl.wikipedia.org/wiki/Munteenhedenprobleem) (ook bekend als het Chicken McNugget Theorem). Met doosjes van 6, 9 en 20 is **43** het grootste aantal dat je *niet* kunt bestellen; elk aantal daarboven kan altijd.

De goedkoopste combinatie komt uit dynamisch programmeren in centen (geen afrondingsfouten), bij gelijke prijs met de minste doosjes. Verspillingsmodus zoekt tot *N + grootste doos − 1*: een grotere bestelling bevat altijd een doosje dat je kunt weglaten.

**Het goedkoopste doosje per nugget is niet vanzelf het grootste.** Met de huidige bezorgprijzen is de 9 per nugget voordeliger dan de 20, en volgens de prijsgeschiedenis was dat in de meeste kwartalen sinds 2021 zo.

### Voorbeelden

| Aantal | Kan het? | Combinatie |
|--------|----------|------------|
| 12 | Ja | 6 + 6 |
| 14 | Nee | — |
| 15 | Ja | 6 + 9 |
| 26 | Ja | 20 + 6 |
| 43 | Nee | Het grootste aantal dat nooit kan |
| 44+ | Altijd | — |

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
[melden via een issue](https://github.com/randomdreft/canitnugget/issues/new?template=winkelprijs.yml).

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

Open `index.html` in je browser. Klaar. Zonder `prices.json` (bijvoorbeeld via `file://`) rekent de site met ingebouwde reserveprijzen en zegt dat er ook bij. Wil je de echte prijzen zien, start dan een lokale webserver:

```bash
python3 -m http.server 8000   # en open http://localhost:8000
```

De prijsscraper is optioneel en heeft alleen Python 3 en Google Chrome nodig:

```bash
python3 scraper/nugget_prijzen.py --droog --alleen alkmaar
```

## Projectstructuur

| Pad | Wat |
|---|---|
| `index.html` | De hele site: HTML, CSS en JavaScript in één bestand |
| `prices.json`, `history.json` | Kopie van de prijsdata; de live versie wordt dagelijks op de server geschreven |
| `scraper/` | Prijsscraper, Wayback-backfill en systemd-units. Zie [`scraper/README.md`](scraper/README.md) |
| `favicon.*`, `apple-touch-icon.png`, `og-image.png` | Icoontjes en het deelplaatje |
| `bron/og-image.html` | Bron van `og-image.png` (renderen op 1200×630) |
| `robots.txt` | Alles mag |

## Technisch

- **Frontend**: vanilla HTML, CSS en JavaScript, geen dependencies en geen buildstap
- **Grafieken**: eigen inline SVG, met tooltips, toetsenbordbediening en een tabelweergave
- **Prijzen**: Python-scraper (alleen standaardbibliotheek) met headless Chrome, dagelijks via een systemd-timer
- **Responsive**: op de telefoon staat het antwoord direct onder het invoerveld
- **Licht en donker**: volgt de systeeminstelling; alle kleuren zijn CSS-tokens op `:root`, getoetst op WCAG AA
- **Hosting**: statische bestanden achter nginx; de webroot bevat alleen wat publiek mag zijn

Wat er wanneer veranderd is staat in [`CHANGELOG.md`](CHANGELOG.md).

## Bijdragen

Hulp is welkom! Je hoeft geen programmeur te zijn om mee te doen.

### Een idee of een fout gevonden?

Maak een [issue](https://github.com/randomdreft/canitnugget/issues/new/choose) aan. Er zijn formulieren voor een fout, een idee en een **winkelprijs** die je gezien hebt. Denk aan:

- een prijs die niet klopt;
- een aantal waarvoor de site een verkeerde combinatie geeft;
- iets dat er raar uitziet op je telefoon;
- een leuk idee voor de site.

Een schermafbeelding en de link uit je adresbalk (die bevat je aantal) helpen enorm.

Issues met het label [`good first issue`](https://github.com/randomdreft/canitnugget/labels/good%20first%20issue) zijn goede eerste klusjes.

### Zelf iets aanpassen?

1. **Fork** deze repository (knop rechtsboven op GitHub).
2. Maak je wijziging in je eigen kopie. Test het door `index.html` in je browser te openen.
3. Open een **pull request** met een korte uitleg van wat je veranderd hebt en waarom.

Houd een pull request klein en gericht op één ding; dat bekijkt en verwerkt het snelst. Twijfel je of iets gewenst is? Open dan eerst een issue om het te bespreken.

Een paar uitgangspunten:

- De site blijft **vanilla HTML, CSS en JavaScript** zonder dependencies of buildstap.
- Teksten op de site en in de repository zijn **Nederlands**.
- Het moet blijven werken op **mobiel**, in licht én donker.
- Bovenaan blijft het **simpel**: één getal, direct antwoord. Nieuwe uitgebreide dingen komen ingeklapt onder de vouw, en alles wat verklapt welke aantallen niet kunnen staat standaard dicht.

## Licentie

Public domain ([Unlicense](LICENSE)): gebruik het, fork het, bestel nuggets.

# Prijsscraper canitnugget.nl

Levert twee bestanden in de webroot (`/var/www/canitnugget/`):

| Bestand | Wat | Ververst |
|---|---|---|
| `prices.json` | Actuele nuggetprijzen: mediaan van een vast mandje filialen | dagelijks |
| `history.json` | Prijsgeschiedenis: nuggets, veggie, Big Mac (2021–nu, Big Mac vanaf 1987) | dagelijks (+ eenmalige backfill) |

## Eerlijk over de bron

**McDonald's Nederland publiceert geen prijzen.** Er bestaat geen officiële
prijslijst, en de "menuprijzen"-sites die in Google bovenaan staan
(menuprijzen.nl en consorten) verzinnen of kopiëren hun cijfers — die gebruiken
we **nooit**. De oude bron van deze site, mcdonaldsmenu.nl, is een geparkeerd
domein geworden.

Wat wél echt is: de menukaarten van filialen op **Thuisbezorgd** en **Uber
Eats**. Dat zijn **bezorgprijzen**, doorgaans 10–35% hoger dan aan de balie, en
ze verschillen per filiaal (franchisenemers bepalen zelf hun prijs). Daarom
publiceren we de **mediaan over een vast mandje filialen** en noemen we het ook
zo: `"kind": "bezorgprijs"`, `"source": "Thuisbezorgd/Uber Eats, mediaan van 10 filialen"`.

## Bestanden

| Bestand | Rol |
|---|---|
| `nugget_prijzen.py` | Dagelijkse meting → `prices.json` + punt in `history.json` |
| `backfill_wayback.py` | Eenmalig/herhaalbaar: geschiedenis uit het Internet Archive + The Economist |
| `menukaart.py` | Prijzen uit een menupagina halen (alle bekende paginaformaten 2021–nu) |
| `historie.py` | `history.json` opbouwen: uitschieters, kwartaalmedianen, Economist-reeksen |
| `filialen.json` | Het vaste mandje filialen |
| `systemd/` | `canitnugget-prijzen.service` + `.timer` |
| `installeer.sh` | Installeren/deployen op trogdor |

Alleen de Python-standaardbibliotheek; pagina's worden opgehaald met
`google-chrome --headless=new --dump-dom` (curl krijgt een 403 van beide
platforms). Chrome krijgt een gewone Chrome-User-Agent, anders toont
Thuisbezorgd een "Even geduld..."-botcontrole.

## Dagelijkse meting

`nugget_prijzen.py` haalt de filialen uit `filialen.json` **na elkaar** op, met
15–45 s pauze ertussen, één keer per dag. Per filiaal worden 6, 9 en 20
Chicken McNuggets en de Big Mac uitgelezen. Daarna:

- `prices.json`: per doosgrootte de **mediaan** over de gelukte filialen
  (bij een even aantal het gemiddelde van de middelste twee, afgerond op centen);
- `history.json`: de meting per filiaal gaat in `raw` (één per filiaal per
  maand, de nieuwste telt), de dagmediaan in `series.dagelijks`, en alle
  reeksen worden opnieuw berekend;
- The Economist-data wordt eens per 30 dagen ververst (mislukt dat, dan blijft
  de oude reeks staan).

**Geen stille terugval.** Lukken er minder dan `minimum_geslaagd` (5) filialen,
dan worden `prices.json` en `history.json` **niet** aangeraakt en eindigt het
script met exitcode 1. De oude tijdstempel blijft dan staan, zodat de site na
7 dagen "mogelijk verouderd" toont. Nooit ingebouwde of verzonnen prijzen.

Veggie Nuggets zijn sinds ongeveer mei 2025 van het menu. `prices.json` meldt ze
als `"available": false` met de laatst bekende prijzen uit de geschiedenis.
Duiken ze ooit weer op in het mandje, dan wordt dat vanzelf `"available": true`.

### Het mandje

Acht Thuisbezorgd-filialen en twee Uber Eats-filialen, verspreid over het land:
Alkmaar, Rotterdam, Amersfoort, Nijmegen, Breda, Zwolle, Leeuwarden,
Maastricht (Thuisbezorgd), Amsterdam Muntplein en Groningen Herestraat (Uber
Eats). Valt een filiaal blijvend af (sluiting, nieuwe URL), vervang het dan
door een ander in dezelfde regio en noteer dat hier.

## prices.json

```json
{
 "timestamp": "2026-09-29T09:28:35+02:00",
 "prices": {"6": 3.73, "9": 5.2, "20": 11.8},
 "source": "Thuisbezorgd/Uber Eats, mediaan van 10 filialen",
 "kind": "bezorgprijs",
 "note": "...",
 "n": 10,
 "bigmac": 8.15,
 "veggie": {"available": false, "last_seen": "2025-05", "last_prices": {"6": 3.45, "9": 4.75, "20": 10.65}, "last_prices_periode": "2025-Q2"},
 "stores": [{"name": "Alkmaar Centrum", "platform": "thuisbezorgd", "url": "...", "prices": {"6": 3.8, "9": 4.95, "20": 9.95}, "bigmac": 6.9}],
 "history": "/history.json"
}
```

`timestamp` en `prices` zijn onveranderd ten opzichte van het oude formaat;
de rest is erbij gekomen. `timestamp` staat in Nederlandse tijd.
Let op: `source` is nu een omschrijving, geen URL.

## history.json

```text
{
 "schema": 1,
 "generated": ISO-tijdstempel,
 "economist_opgehaald": ISO-tijdstempel,
 "notes": toelichting in woorden,
 "series": {
  "nuggets":        [{"date": "2023-08-15", "periode": "2023-Q3", "6": 3.7, "9": 4.95, "20": 10.3, "n": 7}, ...],
  "veggie":         [idem, 2021–2025],
  "bigmac_bezorg":  [{"date", "periode", "eur", "n"}, ...],
  "bigmac_nl":      [{"date": "1987-01-01", "eur": 2.04, "nlg": 4.5, "valuta": "NLG", "bron": "economist-historisch"},
                     {"date": "2011-07-01", "eur": 3.25, "valuta": "EUR", "bron": "economist-v2"}, ...],
  "bigmac_eurozone":[{"date": "2000-04-01", "eur": 2.56, "bron": "economist-v2", "let_op": "gemiddelde eurozone, geen Nederlandse prijs"}, ...],
  "dagelijks":      [{"date": "2026-09-29", "6": 3.73, "9": 5.2, "20": 11.8, "bigmac": 8.15, "n": 10}, ...]
 },
 "sources": [{"id", "naam", "url", "wat"}, ...],
 "raw": [{"date": "2023-09-26", "bron": "wayback"|"dagelijks", "platform": "thuisbezorgd"|"ubereats",
          "filiaal": "mcdonalds-heerhugowaard", "url": "https://web.archive.org/web/...",
          "nuggets": {"6":..,"9":..,"20":..}, "veggie": {...}, "bigmac": ..,
          "uitgesloten": {"nuggets.20": "reden"}   (alleen bij uitschieters)}, ...]
}
```

- `nuggets`, `veggie` en `bigmac_bezorg` zijn **bezorgprijzen**; `bigmac_nl` en
  `bigmac_eurozone` zijn **winkelprijzen** (The Economist). Niet op één lijn
  zetten zonder dat te vermelden.
- Een maat die in een kwartaal niet gemeten is, staat op `null` (de 6 stuks
  staat pas vanaf eind 2022 in de gearchiveerde menu's).
- `date` in de kwartaalreeksen is het midden van het kwartaal (15e van de
  middelste maand), handig om te plotten; `periode` is het echte label.

## Methode van de geschiedenis

**Nuggets, veggie en Big Mac-bezorgprijs (2021–nu)** komen uit het
[Internet Archive](https://web.archive.org/). `backfill_wayback.py`:

1. vraagt via de CDX-API alle gearchiveerde pagina's op onder
   `thuisbezorgd.nl/menu/mcdonalds*`, `thuisbezorgd.nl/en/menu/mcdonalds*`,
   `ubereats.com/nl/store/mcdonalds*` en `ubereats.com/nl-en/store/mcdonalds*`
   (status 200, vanaf 2021);
2. groepeert per platform + filiaal + maand (Uber Eats-filialen op winkel-ID,
   want dezelfde winkel komt onder meerdere namen voor);
3. haalt per groep hoogstens 3 momentopnamen op tot er één prijzen oplevert;
4. gooit Uber Eats-filialen buiten Nederland weg (`addressCountry` ≠ `NL`: er
   staan Britse, Belgische en Amerikaanse McDonald's tussen);
5. leest de prijzen uit met `menukaart.py`: vijf paginaformaten, alleen
   exacte productnamen ("Chicken McNuggets 9", niet "… Voordeelmenu" of
   "Spicy …"), alleen euro's, centen-notatie (Uber Eats 2022: `495`) omgerekend,
   binnen plausibele grenzen en met oplopende prijzen 6 < 9 < 20.

Daarna (`historie.py`, bij elke run opnieuw):

- **uitschieters**: een waarde die meer dan 50% afwijkt van de mediaan van de
  andere metingen binnen 120 dagen (bij minstens 3 buren) telt niet mee en
  krijgt in `raw` een `uitgesloten`-markering met reden;
- **kwartaalmediaan** over alle filiaal-maand-metingen in het kwartaal. Per
  maand zijn er maar een paar gearchiveerde filialen, dus per kwartaal is
  robuuster dan per maand. Wie het fijner wil: alles staat in `raw`.

Niet elke momentopname is bruikbaar: pagina's zonder menu (verwijzingen,
lege client-side pagina's, afgekapte opnames) leveren niets op. Het
Internet Archive bewaart een willekeurige steekproef van filialen, dus het is
geen panel: elk kwartaal is een ander mengsel van filialen.

Bekende eigenaardigheden in de data:

- **Oktober 2021**: zeven Amsterdamse filialen stonden op Thuisbezorgd met 20
  nuggets voor € 5,75 (vermoedelijk een actie). Als uitschieter uitgesloten.
- **Veggie Nuggets ontbreken van eind 2021 tot medio 2023** in de gearchiveerde
  menu's (wel veggie-burgers, geen veggie-nuggets); dat gat is echt, geen
  parseerfout. Laatste waarneming: mei 2025.
- **Leeuwarden** is structureel duur (6 stuks € 5,50). De mediaan vangt dat op;
  in de geschiedenis wordt zo'n waarde als uitschieter gemarkeerd.
- Kwartalen met weinig metingen (n = 2–5, vooral 2021–2023 en begin 2026)
  springen meer heen en weer dan de werkelijke prijs; kijk naar `n`.
- De 6 stuks staat pas vanaf eind 2022 op de gearchiveerde menu's.

**Big Mac winkelprijs** komt uit
[TheEconomist/big-mac-data](https://github.com/TheEconomist/big-mac-data):
Nederland 1987–1999 in guldens (`big-mac-historical-source-data.csv`,
omgerekend tegen 2,20371 gulden per euro; de guldenprijs staat erbij in `nlg`)
en Nederland 2011–nu in euro's (`big-mac-source-data-v2.csv`, halfjaarlijks).
Voor 2000–2010 publiceerde The Economist alleen een eurozone-gemiddelde; dat
staat als duidelijk gelabelde opvulling in `bigmac_eurozone`.

## Beheer op trogdor

```bash
sudo ./installeer.sh                                   # installeren/deployen naar /usr/local/lib/canitnugget
sudo systemctl start canitnugget-prijzen.service       # nu meten
journalctl -u canitnugget-prijzen.service -n 50        # log
systemctl list-timers canitnugget-prijzen.timer        # volgende run (dagelijks 06:30 NL-tijd, +0–30 min)

# testen zonder iets te schrijven
python3 nugget_prijzen.py --droog --alleen alkmaar

# geschiedenis opnieuw opbouwen (~1 uur, beleefd tempo; cache in ~/.cache/canitnugget-wayback)
python3 backfill_wayback.py --history /tmp/history.json
sudo install -o canitnugget -g canitnugget -m 644 /tmp/history.json /var/www/canitnugget/history.json
```

De service draait als systeemgebruiker `canitnugget` (nooit Chrome als root),
met `HOME=/var/lib/canitnugget`. Schrijfrecht op de webroot gaat via een ACL
op alleen `/var/www/canitnugget` (`setfacl -m u:canitnugget:rwx`); eigenaar
www-data blijft. Beide JSON-bestanden worden atomisch geschreven (tmp-bestand +
rename), dus nginx serveert nooit een half bestand.

De backfill praat met archive.org op ~4 s per verzoek: sneller en archive.org
weigert een tijd lang elke verbinding.

"""Prijzen van McNuggets, Veggie Nuggets en Big Mac uit een menupagina halen.

Gedeeld door nugget_prijzen.py (dagelijks, live pagina's) en
backfill_wayback.py (oude pagina's uit het Internet Archive).

Thuisbezorgd en Uber Eats hebben door de jaren heen vijf verschillende
paginaformaten gehad. Elk formaat heeft hieronder een eigen patroon; alle
treffers worden verzameld en per product wint de prijs die het vaakst
voorkomt (dezelfde prijs staat vaak meerdere keren in één pagina).

Alles is standaardbibliotheek: geen BeautifulSoup, geen requests.
"""

import collections
import html
import re

# Productsleutels -> exacte productnaam (hoofdletterongevoelig, geanker)
PRODUCTEN = {
    'N6': r'(?:Chicken )?McNuggets 6(?: stuks)?',
    'N9': r'(?:Chicken )?McNuggets 9(?: stuks)?',
    'N20': r'(?:Chicken )?McNuggets 20(?: stuks)?',
    'V6': r'Veggie (?:Mc)?Nuggets 6',
    'V9': r'Veggie (?:Mc)?Nuggets 9',
    'V20': r'Veggie (?:Mc)?Nuggets 20',
    'BM': r'Big Mac',
}
# Schrijfwijzen als '9 Chicken McNuggets©' en 'Big Mac®' komen alleen voor op
# Belgische, Britse en Amerikaanse Uber Eats-pagina's; bewust niet herkend.
_PRODUCT_RE = {k: re.compile(r'^' + v + r'$', re.I) for k, v in PRODUCTEN.items()}

# Wat een product redelijkerwijs kan kosten (euro, bezorgprijs). Daarbuiten
# is het vrijwel zeker een parseerfout (centen als euro's, verkeerde
# valuta, een menu in plaats van het losse product).
GRENZEN = {
    'N6': (1.5, 9.0), 'N9': (2.0, 13.0), 'N20': (4.5, 28.0),
    'V6': (1.5, 9.0), 'V9': (2.0, 13.0), 'V20': (4.5, 28.0),
    'BM': (2.5, 15.0),
}


def _euro(tekst):
    return float(tekst.replace('.', '').replace(',', '.')) if ',' in tekst else float(tekst)


def _kandidaten(t):
    """Alle (productnaam, prijs in euro) paren die in de pagina te vinden zijn."""
    paren = []
    # JSON zit soms dubbel ge-escaped in een <script>; eerst plat slaan
    t2 = t.replace('\\u0026', '&').replace('\\u002F', '/').replace('\\"', '"')

    # 1. schema.org MenuItem (Uber Eats, alle jaren). Tussen aanhalingstekens
    #    = euro's ("5.35"); een kaal geheel getal = centen (2022: 495).
    for m in re.finditer(
            r'"@type"\s*:\s*"MenuItem"\s*,\s*"name"\s*:\s*"([^"]+)"(.{0,800}?)"price"\s*:\s*("?)([\d.]+)\3'
            r'(?:\s*,\s*"priceCurrency"\s*:\s*"([A-Z]{3})")?', t2, re.S):
        naam, _, quote, getal, valuta = m.groups()
        if valuta and valuta != 'EUR':
            continue
        prijs = float(getal)
        if not quote and '.' not in getal:
            prijs = prijs / 100
        paren.append((naam, prijs))

    # 2. Thuisbezorgd 2023-nu: JSON met "type":"menuitem" en "basePrice" in euro's
    for m in re.finditer(
            r'"id":"[^"]{4,40}","name":"([^"]+)","description":"[^"]*",'
            r'(?:(?!"type":"menuitem").){0,1500}"type":"menuitem".{0,300}?"basePrice":([\d.]+)', t2, re.S):
        paren.append((m.group(1), float(m.group(2))))

    # 3. Thuisbezorgd 2021: HTML met data-product-name en een meal__price
    for m in re.finditer(r'data-product-name="([^"]+)".{0,1500}?meal__price[^>]*>\s*€\s*([\d,]+)', t, re.S):
        paren.append((m.group(1), _euro(m.group(2))))

    # 4. Thuisbezorgd (overgangsvorm): koppen met data-qa="heading" en "€ 4,95"
    for m in re.finditer(r'data-qa="heading">([^<]+)<.{0,5000}?€\xa0(\d+,\d{2})', html.unescape(t), re.S):
        paren.append((m.group(1), _euro(m.group(2))))

    # 5. Thuisbezorgd 2022: "prices":{"delivery":<centen>}
    for m in re.finditer(r'"categoryId":"[^"]*","name":"([^"]+)".{0,800}?"prices":\{"delivery":(\d+)', t2, re.S):
        paren.append((m.group(1), int(m.group(2)) / 100))
    return paren


def land(t):
    """addressCountry uit de schema.org-gegevens, of None."""
    m = re.search(r'"addressCountry"\s*:\s*"([A-Z]{2})"', t)
    return m.group(1) if m else None


def is_botcheck(t):
    """Thuisbezorgd toont soms een 'Even geduld...'-controlepagina."""
    return '<title>Even geduld' in t[:5000] or len(t) < 2000


def extraheer(t):
    """Geeft {'N6': 3.8, 'N9': 4.95, 'N20': 9.95, 'BM': 6.95, ...}.

    Alleen producten die gevonden zijn, binnen GRENZEN liggen en waarvan de
    doosgroottes logisch oplopen (6 < 9 < 20) komen terug.
    """
    gezien = collections.defaultdict(collections.Counter)
    volgorde = {}
    for naam, prijs in _kandidaten(t):
        naam = html.unescape(naam).strip()
        naam = re.sub(r'\s+', ' ', naam)
        for sleutel, rx in _PRODUCT_RE.items():
            if rx.match(naam):
                p = round(prijs, 2)
                gezien[sleutel][p] += 1
                volgorde.setdefault((sleutel, p), len(volgorde))
    res = {}
    for sleutel, teller in gezien.items():
        # meest voorkomende prijs; bij gelijkspel de eerst gevonden
        prijs = sorted(teller.items(), key=lambda kv: (-kv[1], volgorde[(sleutel, kv[0])]))[0][0]
        lo, hi = GRENZEN[sleutel]
        if lo <= prijs <= hi:
            res[sleutel] = prijs
    for soort in ('N', 'V'):
        reeks = [res.get(soort + m) for m in ('6', '9', '20')]
        aanwezig = [p for p in reeks if p is not None]
        if aanwezig != sorted(aanwezig) or len(set(aanwezig)) != len(aanwezig):
            for m in ('6', '9', '20'):
                res.pop(soort + m, None)
    return res


def naar_json(res):
    """{'N6':..,'V9':..,'BM':..} -> {'nuggets': {'6':..}, 'veggie': {...}, 'bigmac': ..}"""
    uit = {}
    for soort, naam in (('N', 'nuggets'), ('V', 'veggie')):
        d = {m: res[soort + m] for m in ('6', '9', '20') if soort + m in res}
        if d:
            uit[naam] = d
    if 'BM' in res:
        uit['bigmac'] = res['BM']
    return uit


if __name__ == '__main__':
    import sys
    for pad in sys.argv[1:]:
        with open(pad, errors='ignore') as f:
            tekst = f.read()
        print(pad, land(tekst), extraheer(tekst))

"""history.json opbouwen: ruwe metingen -> reeksen per kwartaal.

Eén bron van waarheid is de lijst `raw` in history.json: één regel per
filiaal per maand (Wayback-momentopname of dagelijkse meting). Alle
reeksen in `series` worden daar telkens opnieuw uit berekend, zodat een
aanpassing aan de methode nooit handwerk in de reeksen vraagt.

Zie README.md in deze map voor het schema en de methode.
"""

import csv
import datetime as dt
import io
import json
import os
import statistics
import tempfile
import urllib.request
from zoneinfo import ZoneInfo
from decimal import Decimal, ROUND_HALF_UP

GULDEN_PER_EURO = 2.20371
SCHEMA_VERSIE = 1

ECONOMIST_BRONNEN = {
    'v2': 'https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/source-data/big-mac-source-data-v2.csv',
    'hist': 'https://raw.githubusercontent.com/TheEconomist/big-mac-data/master/source-data/big-mac-historical-source-data.csv',
}

# Uitschieters: een waarde die meer dan 50% afwijkt van de mediaan van de
# andere metingen binnen VENSTER_DAGEN, met minstens MIN_BUREN buren.
VENSTER_DAGEN = 120
MIN_BUREN = 3
MAX_AFWIJKING = 1.5

VELDEN = [('nuggets', '6'), ('nuggets', '9'), ('nuggets', '20'),
          ('veggie', '6'), ('veggie', '9'), ('veggie', '20'), ('bigmac', None)]


def centen(x):
    """Afronden op hele centen, half naar boven (zoals een kassabon)."""
    return float(Decimal(str(x)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def mediaan(waarden):
    return centen(statistics.median(waarden)) if waarden else None


def schrijf_json_atomisch(pad, data, modus=0o644):
    """tmp-bestand in dezelfde map + rename: een lezer ziet nooit een half bestand."""
    map_ = os.path.dirname(os.path.abspath(pad))
    fd, tmp = tempfile.mkstemp(prefix='.' + os.path.basename(pad) + '.', suffix='.tmp', dir=map_)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, modus)
        os.replace(tmp, pad)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def lees_json(pad, standaard=None):
    try:
        with open(pad, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return standaard


# ---------- ruwe metingen ----------

def sleutel(r):
    """Eén meting per platform + filiaal + maand."""
    return (r['platform'], r['filiaal'], r['date'][:7])


def voeg_toe(raw, nieuw, vervang=True):
    """Voegt metingen toe aan raw. vervang=True: een nieuwere meting van
    hetzelfde filiaal in dezelfde maand vervangt de oude (dagelijkse run);
    vervang=False: de eerste blijft staan (backfill)."""
    index = {sleutel(r): i for i, r in enumerate(raw)}
    for r in nieuw:
        k = sleutel(r)
        if k in index:
            if vervang:
                raw[index[k]] = r
        else:
            index[k] = len(raw)
            raw.append(r)
    raw.sort(key=lambda r: (r['date'], r['platform'], r['filiaal']))
    return raw


def _waarde(r, groep, maat):
    if groep == 'bigmac':
        return r.get('bigmac')
    return (r.get(groep) or {}).get(maat)


def markeer_uitschieters(raw):
    """Zet r['uitgesloten'] = {veld: reden} bij waarden die sterk afwijken
    van vergelijkbare metingen in dezelfde periode. Idempotent."""
    datums = [dt.date.fromisoformat(r['date'][:10]) for r in raw]
    for r in raw:
        r.pop('uitgesloten', None)
    for groep, maat in VELDEN:
        veld = groep if maat is None else f'{groep}.{maat}'
        punten = [(i, datums[i], _waarde(r, groep, maat)) for i, r in enumerate(raw)]
        punten = [p for p in punten if p[2] is not None]
        for i, d, w in punten:
            buren = [w2 for j, d2, w2 in punten if j != i and abs((d2 - d).days) <= VENSTER_DAGEN]
            if len(buren) < MIN_BUREN:
                continue
            m = statistics.median(buren)
            if w > m * MAX_AFWIJKING or w < m / MAX_AFWIJKING:
                raw[i].setdefault('uitgesloten', {})[veld] = (
                    f'{w:.2f} wijkt meer dan 50% af van de mediaan {m:.2f} van '
                    f'{len(buren)} metingen binnen {VENSTER_DAGEN} dagen')
    return raw


def _kwartaal(datum):
    j, m = int(datum[:4]), int(datum[5:7])
    k = (m - 1) // 3 + 1
    return f'{j}-Q{k}', f'{j}-{3 * k - 1:02d}-15'


def reeks(raw, groep, maten, tot=None):
    """Mediaan per kwartaal over alle filiaal-maand-metingen."""
    per = {}
    for r in raw:
        if tot and r['date'][:7] > tot:
            continue
        uit = r.get('uitgesloten', {})
        rij = {}
        for maat in maten:
            veld = groep if maat is None else f'{groep}.{maat}'
            w = _waarde(r, groep, maat)
            if w is not None and veld not in uit:
                rij[maat] = w
        if rij:
            per.setdefault(_kwartaal(r['date']), []).append(rij)
    uit = []
    for (periode, midden), rijen in sorted(per.items()):
        punt = {'date': midden, 'periode': periode}
        for maat in maten:
            naam = 'eur' if maat is None else maat
            punt[naam] = mediaan([r[maat] for r in rijen if maat in r])
        punt['n'] = len(rijen)
        uit.append(punt)
    return uit


# ---------- The Economist ----------

def _haal(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'canitnugget.nl prijsgeschiedenis (+https://canitnugget.nl)'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode('utf-8')


def economist_reeksen():
    """Big Mac-prijzen uit TheEconomist/big-mac-data (winkelprijs, geen bezorging)."""
    v2 = list(csv.DictReader(io.StringIO(_haal(ECONOMIST_BRONNEN['v2']), newline='')))
    # het historische bestand heeft oude Mac-regeleinden (\r)
    hist_tekst = _haal(ECONOMIST_BRONNEN['hist']).replace('\r\n', '\n').replace('\r', '\n')
    hist = list(csv.DictReader(io.StringIO(hist_tekst)))

    nl = []
    for r in hist:
        if r['iso_a3'] == 'NLD' and r['currency_code'] == 'NLG':
            nlg = float(r['local_price'])
            nl.append({'date': r['date'][:10], 'eur': centen(nlg / GULDEN_PER_EURO), 'nlg': nlg,
                       'bron': 'economist-historisch', 'valuta': 'NLG'})
    for r in v2:
        if r['iso_a3'] == 'NLD' and r['currency_code'] == 'EUR':
            nl.append({'date': r['date'][:10], 'eur': float(r['local_price']),
                       'bron': 'economist-v2', 'valuta': 'EUR'})
    nl.sort(key=lambda p: p['date'])
    if not nl:
        raise ValueError('geen Nederlandse Big Mac-prijzen in de Economist-data')

    # Eurozone alleen als opvulling voor het gat in de NL-reeks
    laatste_gulden = max(p['date'] for p in nl if p['valuta'] == 'NLG')
    eerste_euro = min(p['date'] for p in nl if p['valuta'] == 'EUR')
    ez = []
    for r in v2:
        d = r['date'][:10]
        if r['iso_a3'] == 'EUZ' and laatste_gulden < d < eerste_euro:
            ez.append({'date': d, 'eur': centen(float(r['local_price'])), 'bron': 'economist-v2',
                       'let_op': 'gemiddelde eurozone, geen Nederlandse prijs'})
    ez.sort(key=lambda p: p['date'])
    return nl, ez


# ---------- alles samen ----------

BRONNEN = [
    {'id': 'wayback', 'naam': 'Internet Archive Wayback Machine',
     'url': 'https://web.archive.org/',
     'wat': 'Gearchiveerde menupagina’s van McDonald’s-filialen op Thuisbezorgd en Uber Eats (2021–nu). Bezorgprijzen.'},
    {'id': 'dagelijks', 'naam': 'Thuisbezorgd en Uber Eats (live)',
     'url': 'https://www.thuisbezorgd.nl/',
     'wat': 'Dagelijkse meting van een vast mandje filialen, zie scraper/filialen.json. Bezorgprijzen.'},
    {'id': 'economist-v2', 'naam': 'The Economist, Big Mac index (source-data v2)',
     'url': 'https://github.com/TheEconomist/big-mac-data',
     'wat': 'Winkelprijs Big Mac Nederland 2011–nu (halfjaarlijks) en eurozone-gemiddelde 2000–2010.'},
    {'id': 'economist-historisch', 'naam': 'The Economist, Big Mac index (historical source data)',
     'url': 'https://github.com/TheEconomist/big-mac-data',
     'wat': 'Winkelprijs Big Mac Nederland 1987–1999 in guldens; omgerekend tegen 2,20371 gulden per euro.'},
]

TOELICHTING = (
    'Alle prijzen in euro. Nuggets, veggie en bigmac_bezorg zijn BEZORGPRIJZEN (Thuisbezorgd/Uber Eats), '
    'doorgaans 10-35% hoger dan in het restaurant; McDonald’s Nederland publiceert zelf geen prijzen. '
    'Elk punt is de mediaan per kwartaal over alle filiaal-maand-metingen in dat kwartaal (n = aantal metingen); '
    'per filiaal telt hoogstens één meting per maand. Uitschieters (>50% afwijking van de mediaan van '
    'vergelijkbare metingen binnen 120 dagen) tellen niet mee en zijn in raw gemarkeerd met "uitgesloten". '
    'Veggie Nuggets zijn sinds ongeveer mei 2025 niet meer te koop. '
    'bigmac_nl en bigmac_eurozone zijn WINKELPRIJZEN volgens The Economist; bigmac_eurozone is alleen '
    'opvulling voor 2000-2010, toen The Economist geen losse Nederlandse prijs publiceerde. '
    'Guldenprijzen (1987-1999) zijn omgerekend tegen de vaste koers 2,20371 en staan ook in het veld nlg. '
    'dagelijks: mediaan per dag van het vaste filialenmandje.'
)


def bouw(history, raw=None, economist=None, dagelijks_punt=None):
    """Rekent alle reeksen opnieuw uit en geeft een nieuw history-object."""
    history = dict(history or {})
    raw = markeer_uitschieters(list(raw if raw is not None else history.get('raw', [])))
    series = dict(history.get('series', {}))

    if economist is not None:
        series['bigmac_nl'], series['bigmac_eurozone'] = economist
        history['economist_opgehaald'] = dt.datetime.now(ZoneInfo('Europe/Amsterdam')).isoformat(timespec='seconds')

    dag = list(series.get('dagelijks', []))
    if dagelijks_punt:
        dag = [p for p in dag if p['date'] != dagelijks_punt['date']] + [dagelijks_punt]
        dag.sort(key=lambda p: p['date'])
    series['dagelijks'] = dag

    series['nuggets'] = reeks(raw, 'nuggets', ['6', '9', '20'])
    series['veggie'] = reeks(raw, 'veggie', ['6', '9', '20'])
    series['bigmac_bezorg'] = reeks(raw, 'bigmac', [None])
    series.setdefault('bigmac_nl', [])
    series.setdefault('bigmac_eurozone', [])

    volgorde = ['nuggets', 'veggie', 'bigmac_bezorg', 'bigmac_nl', 'bigmac_eurozone', 'dagelijks']
    return {
        'schema': SCHEMA_VERSIE,
        'generated': dt.datetime.now(ZoneInfo('Europe/Amsterdam')).isoformat(timespec='seconds'),
        'economist_opgehaald': history.get('economist_opgehaald'),
        'notes': TOELICHTING,
        'series': {k: series[k] for k in volgorde},
        'sources': BRONNEN,
        'raw': raw,
    }


def veggie_samenvatting(history):
    """{'available': False, 'last_seen': 'YYYY-MM', 'last_prices': {...}} uit de historie."""
    laatst = None
    for r in history.get('raw', []):
        if r.get('veggie') and (laatst is None or r['date'] > laatst):
            laatst = r['date']
    reeks_ = history.get('series', {}).get('veggie', [])
    prijzen = {}
    if reeks_:
        prijzen = {m: reeks_[-1][m] for m in ('6', '9', '20') if reeks_[-1].get(m) is not None}
    return {'available': False, 'last_seen': laatst[:7] if laatst else None,
            'last_prices': prijzen,
            'last_prices_periode': reeks_[-1]['periode'] if reeks_ else None}

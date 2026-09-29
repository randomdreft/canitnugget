#!/usr/bin/env python3
"""Dagelijkse nuggetprijzen voor canitnugget.nl.

Haalt de menupagina's van een vast mandje McDonald's-filialen op
(filialen.json) met headless Google Chrome, leest de prijzen uit en
publiceert per doosgrootte de MEDIAAN als prices.json. Voegt het punt van
vandaag toe aan history.json.

Het zijn bezorgprijzen van Thuisbezorgd/Uber Eats; McDonald's Nederland
publiceert zelf geen prijzen.

Nooit terugvallen op ingebouwde prijzen: lukt de meting niet (te weinig
filialen), dan blijven prices.json en history.json ongewijzigd staan - de
oude tijdstempel laat de site zien dat de prijzen verouderd zijn - en
eindigt het script met exitcode 1.

Gebruik:
  nugget_prijzen.py [--prices PAD] [--history PAD] [--filialen PAD] [--droog] [--alleen NAAM]
"""

import argparse
import datetime as dt
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import historie  # noqa: E402
import menukaart  # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
CHROME = os.environ.get('CANITNUGGET_CHROME', 'google-chrome')
MATEN = ('6', '9', '20')
ECONOMIST_VERVERS_DAGEN = 30


def log(*a):
    print(*a, flush=True)


def user_agent():
    """Dezelfde User-Agent als een gewone Chrome op Linux (zonder 'Headless')."""
    try:
        versie = subprocess.run([CHROME, '--version'], capture_output=True, text=True, timeout=30).stdout
        major = re.search(r'(\d+)\.', versie).group(1)
    except Exception:
        major = '140'
    return f'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major}.0.0.0 Safari/537.36'


def dump_dom(url, profiel, ua, timeout=120):
    cmd = [CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
           '--disable-extensions', '--mute-audio', f'--user-data-dir={profiel}', f'--user-agent={ua}',
           '--lang=nl-NL', '--virtual-time-budget=20000', '--dump-dom', url]
    r = subprocess.run(cmd, capture_output=True, text=True, errors='replace', timeout=timeout)
    return r.stdout


def meet_filiaal(filiaal, profiel, ua, pogingen=2):
    """{'nuggets': {...}, 'bigmac': .., ...} of een foutmelding (str)."""
    fout = 'onbekende fout'
    for poging in range(1, pogingen + 1):
        try:
            tekst = dump_dom(filiaal['url'], profiel, ua)
        except subprocess.TimeoutExpired:
            fout = 'Chrome time-out'
            tekst = ''
        if tekst and menukaart.is_botcheck(tekst):
            fout = 'botcontrole ("Even geduld...") of lege pagina'
        elif tekst:
            if filiaal['platform'] == 'ubereats' and menukaart.land(tekst) not in ('NL', None):
                return f'geen Nederlands filiaal ({menukaart.land(tekst)})'
            res = menukaart.naar_json(menukaart.extraheer(tekst))
            if res.get('nuggets') and all(m in res['nuggets'] for m in MATEN):
                return res
            fout = f'geen volledige nuggetprijzen gevonden ({res or "niets"})'
        elif fout != 'Chrome time-out':
            fout = 'lege uitvoer van Chrome'
        if poging < pogingen:
            time.sleep(random.uniform(30, 60))
    return fout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--prices', default='/var/www/canitnugget/prices.json')
    ap.add_argument('--history', default='/var/www/canitnugget/history.json')
    ap.add_argument('--filialen', default=os.path.join(HIER, 'filialen.json'))
    ap.add_argument('--droog', action='store_true', help='alleen meten en tonen, niets schrijven')
    ap.add_argument('--alleen', help='alleen filialen waarvan de naam dit bevat (test)')
    args = ap.parse_args()

    with open(args.filialen, encoding='utf-8') as f:
        config = json.load(f)
    filialen = config['filialen']
    if args.alleen:
        filialen = [f for f in filialen if args.alleen.lower() in f['naam'].lower()]
    minimum = config.get('minimum_geslaagd', 4)

    ua = user_agent()
    profiel = tempfile.mkdtemp(prefix='canitnugget-chrome-')
    resultaten = []
    try:
        for i, fil in enumerate(filialen):
            if i:
                time.sleep(random.uniform(*config.get('pauze_seconden', [15, 45])))
            res = meet_filiaal(fil, profiel, ua)
            if isinstance(res, dict):
                log(f'OK   {fil["naam"]} ({fil["platform"]}): {json.dumps(res)}')
                resultaten.append((fil, res))
            else:
                log(f'FOUT {fil["naam"]} ({fil["platform"]}): {res}')
    finally:
        shutil.rmtree(profiel, ignore_errors=True)

    n = len(resultaten)
    if n < minimum:
        log(f'MISLUKT: {n} van {len(filialen)} filialen gemeten, minimaal {minimum} nodig. '
            f'prices.json en history.json blijven ongewijzigd.')
        return 1

    # Nederlandse tijd: index.html leest de cijfers van de tijdstempel als lokale tijd
    nu = dt.datetime.now(ZoneInfo('Europe/Amsterdam'))
    vandaag = nu.date().isoformat()
    prijzen = {m: historie.mediaan([r['nuggets'][m] for _, r in resultaten]) for m in MATEN}
    bigmacs = [r['bigmac'] for _, r in resultaten if 'bigmac' in r]
    bigmac = historie.mediaan(bigmacs)
    veggie_nu = [r['veggie'] for _, r in resultaten if r.get('veggie')]
    platforms = sorted({f['platform'] for f, _ in resultaten})
    platformnamen = {'thuisbezorgd': 'Thuisbezorgd', 'ubereats': 'Uber Eats'}

    history = historie.lees_json(args.history, {}) or {}
    ruw = [{'date': vandaag, 'bron': 'dagelijks', 'platform': f['platform'], 'filiaal': f['id'],
            'url': f['url'], **r} for f, r in resultaten]
    raw = historie.voeg_toe(list(history.get('raw', [])), ruw, vervang=True)
    dagpunt = {'date': vandaag, **prijzen, 'bigmac': bigmac, 'n': n}

    economist = None
    opgehaald = history.get('economist_opgehaald')
    if not opgehaald or (nu - dt.datetime.fromisoformat(opgehaald)).days >= ECONOMIST_VERVERS_DAGEN:
        try:
            economist = historie.economist_reeksen()
            log('Economist-data ververst')
        except Exception as e:  # niet fataal: de oude reeks blijft staan
            log(f'Economist-data verversen mislukt ({e}); oude reeks blijft staan')
    nieuwe_history = historie.bouw(history, raw=raw, economist=economist, dagelijks_punt=dagpunt)

    if veggie_nu:
        veggie = {'available': True,
                  'prices': {m: historie.mediaan([v[m] for v in veggie_nu if m in v]) for m in MATEN
                             if any(m in v for v in veggie_nu)},
                  'n': len(veggie_nu)}
    else:
        veggie = historie.veggie_samenvatting(nieuwe_history)

    prices = {
        'timestamp': nu.isoformat(timespec='seconds'),
        'prices': prijzen,
        'source': f'{"/".join(platformnamen[p] for p in platforms)}, mediaan van {n} filialen',
        'kind': 'bezorgprijs',
        'note': ('Bezorgprijzen van Thuisbezorgd/Uber Eats, doorgaans 10-35% hoger dan in het restaurant. '
                 'McDonald’s Nederland publiceert zelf geen prijzen.'),
        'n': n,
        'bigmac': bigmac,
        'veggie': veggie,
        'stores': [{'name': f['naam'], 'platform': f['platform'], 'url': f['url'],
                    'prices': r['nuggets'], 'bigmac': r.get('bigmac')} for f, r in resultaten],
        'history': '/history.json',
    }

    log(f'Mediaan van {n} filialen: 6={prijzen["6"]} 9={prijzen["9"]} 20={prijzen["20"]} Big Mac={bigmac}')
    if args.droog:
        log(json.dumps(prices, ensure_ascii=False, indent=1))
        return 0
    historie.schrijf_json_atomisch(args.history, nieuwe_history)
    historie.schrijf_json_atomisch(args.prices, prices)
    log(f'Geschreven: {args.prices} en {args.history}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

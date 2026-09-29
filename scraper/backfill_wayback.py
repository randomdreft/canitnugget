#!/usr/bin/env python3
"""Prijsgeschiedenis 2021-nu reconstrueren uit het Internet Archive.

Zoekt via de Wayback CDX-API alle gearchiveerde menupagina's van
McDonald's-filialen op Thuisbezorgd en Uber Eats, haalt per filiaal per
maand één bruikbare momentopname op en schrijft de gevonden prijzen als
ruwe metingen naar history.json. Haalt ook de Big Mac-reeksen van The
Economist op. Daarna worden alle reeksen opnieuw berekend.

Beleefd tegen archive.org: alles na elkaar, minstens PAUZE (4) seconden
tussen verzoeken, bij fouten of 429 exponentieel langer wachten (60 s,
120 s, ...). Sneller dan ~15 verzoeken per minuut en archive.org weigert
een tijd lang elke verbinding ('Connection refused'). Opgehaalde
pagina's worden gecachet, dus een tweede run haalt niets dubbel op.

Gebruik:
  backfill_wayback.py [--history PAD] [--cache MAP] [--max-pogingen 3] [--alleen-economist]

Reproduceerbaar: dezelfde cache + dezelfde CDX-lijst = dezelfde uitkomst.
"""

import argparse
import datetime as dt
import gzip
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import historie  # noqa: E402
import menukaart  # noqa: E402

UA = 'canitnugget.nl prijsgeschiedenis (+https://canitnugget.nl)'
PAUZE = 4.0  # archive.org weigert verbindingen bij meer dan ~15 verzoeken per minuut
VANAF = '2021'

PREFIXEN = [
    ('thuisbezorgd', 'www.thuisbezorgd.nl/menu/mcdonalds'),
    ('thuisbezorgd', 'www.thuisbezorgd.nl/en/menu/mcdonalds'),
    ('ubereats', 'www.ubereats.com/nl/store/mcdonalds'),
    ('ubereats', 'www.ubereats.com/nl-en/store/mcdonalds'),
]

_laatste_verzoek = [0.0]


def log(*a):
    print(*a, flush=True)


def haal(url, pogingen=4, timeout=120):
    """GET met pauze, backoff en een beleefde User-Agent. None bij blijvende fout/404."""
    wacht = 60
    for poging in range(1, pogingen + 1):
        verstreken = time.monotonic() - _laatste_verzoek[0]
        if verstreken < PAUZE:
            time.sleep(PAUZE - verstreken)
        _laatste_verzoek[0] = time.monotonic()
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Encoding': 'gzip'})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                if resp.headers.get('Content-Encoding') == 'gzip':
                    data = gzip.decompress(data)
                return data.decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:
            if e.code in (404, 403, 410):
                return None
            log(f'  HTTP {e.code} (poging {poging}), wacht {wacht}s')
        except Exception as e:  # time-outs, verbroken verbindingen
            log(f'  {type(e).__name__}: {e} (poging {poging}), wacht {wacht}s')
        time.sleep(wacht)
        wacht *= 2
    return None


def filiaal_uit_url(platform, url):
    pad = urllib.parse.urlsplit(url).path
    if platform == 'thuisbezorgd':
        m = re.search(r'/menu/(mcdonalds[a-z0-9-]*)', pad)
        return m.group(1) if m else None
    # Uber Eats-winkel-ID's zijn 22 tekens base64url; alles daarna (submenu's,
    # vreemde '/9.10'-paden) hoort er niet bij
    m = re.search(r'/store/(mcdonalds[^/]*)/([A-Za-z0-9_-]{22})(?:/|$)', pad)
    return f'{m.group(1)}/{m.group(2)}' if m else None


def ontdubbel_ubereats(snapshots):
    """Eén filiaalnaam per Uber Eats-ID: dezelfde winkel komt onder
    verschillende namen voor (bijv. '-taunton' en '-tauntons')."""
    naam_per_id = {}
    for platform, _, _, fil in sorted(snapshots, key=lambda s: s[3]):
        if platform == 'ubereats':
            naam_per_id.setdefault(fil.split('/')[1], fil)
    return [(p, ts, url, naam_per_id[fil.split('/')[1]] if p == 'ubereats' else fil)
            for p, ts, url, fil in snapshots]


def cdx(platform, prefix):
    q = urllib.parse.urlencode([('url', prefix), ('matchType', 'prefix'), ('from', VANAF),
                                ('filter', 'statuscode:200'), ('filter', 'mimetype:text/html'),
                                ('fl', 'timestamp,original')])
    tekst = haal('https://web.archive.org/cdx/search/cdx?' + q, pogingen=5, timeout=300)
    if tekst is None:
        raise RuntimeError(f'CDX-zoekopdracht mislukt voor {prefix}')
    uit = []
    for regel in tekst.splitlines():
        delen = regel.split(' ', 1)
        if len(delen) != 2 or not delen[0].isdigit():
            continue
        ts, url = delen
        filiaal = filiaal_uit_url(platform, url)
        if filiaal:
            uit.append((ts, url, filiaal))
    return uit


def groepeer(snapshots):
    """{(platform, filiaal, 'YYYY-MM'): [(ts, url), ...]} met URL's zonder
    querystring vooraan (die zijn het 'schoonst')."""
    groepen = {}
    for platform, ts, url, filiaal in snapshots:
        k = (platform, filiaal, f'{ts[:4]}-{ts[4:6]}')
        groepen.setdefault(k, []).append((ts, url))
    for k in groepen:
        # uniek per tijdstempel, zonder-query eerst, dan chronologisch
        uniek = {}
        for ts, url in groepen[k]:
            if ts not in uniek or '?' in uniek[ts]:
                uniek[ts] = url
        groepen[k] = sorted(uniek.items(), key=lambda p: ('?' in p[1], p[0]))
    return groepen


def pagina(ts, url, cachemap):
    naam = re.sub(r'[^A-Za-z0-9._-]+', '_', f'{ts}_{url}')[:200] + '.html.gz'
    pad = os.path.join(cachemap, naam)
    if os.path.exists(pad):
        with gzip.open(pad, 'rt', encoding='utf-8', errors='replace') as f:
            return f.read()
    tekst = haal(f'https://web.archive.org/web/{ts}id_/{url}')
    if tekst is not None:
        with gzip.open(pad + '.tmp', 'wt', encoding='utf-8') as f:
            f.write(tekst)
        os.replace(pad + '.tmp', pad)
    return tekst


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--history', default='/var/www/canitnugget/history.json')
    ap.add_argument('--cache', default=os.path.expanduser('~/.cache/canitnugget-wayback'))
    ap.add_argument('--max-pogingen', type=int, default=3,
                    help='momentopnamen per filiaal per maand proberen tot er één prijzen oplevert')
    ap.add_argument('--alleen-economist', action='store_true')
    args = ap.parse_args()
    os.makedirs(args.cache, exist_ok=True)

    history = historie.lees_json(args.history, {}) or {}
    raw = list(history.get('raw', []))

    log('The Economist ophalen...')
    economist = historie.economist_reeksen()
    log(f'  bigmac_nl: {len(economist[0])} punten, bigmac_eurozone: {len(economist[1])} punten')

    if not args.alleen_economist:
        snapshots = []
        for platform, prefix in PREFIXEN:
            lijst = cdx(platform, prefix)
            log(f'CDX {prefix}: {len(lijst)} momentopnamen')
            snapshots += [(platform, ts, url, fil) for ts, url, fil in lijst]
        groepen = groepeer(ontdubbel_ubereats(snapshots))
        log(f'{len(groepen)} combinaties van filiaal en maand')

        al_gedaan = {historie.sleutel(r) for r in raw if r.get('bron') == 'wayback'}
        nieuw, geprobeerd, mislukt = [], 0, 0
        for i, ((platform, filiaal, maand), kandidaten) in enumerate(sorted(groepen.items(), key=lambda kv: kv[0][2])):
            if (platform, filiaal, maand) in al_gedaan:
                continue
            gevonden = None
            for ts, url in kandidaten[:args.max_pogingen]:
                geprobeerd += 1
                tekst = pagina(ts, url, args.cache)
                if not tekst:
                    continue
                if platform == 'ubereats':
                    # Uber Eats kent ook Belgische, Britse en Amerikaanse filialen
                    land = menukaart.land(tekst)
                    if land is None:
                        continue
                    if land != 'NL':
                        log(f'  {maand} {platform} {filiaal}: geen Nederlands filiaal ({land}), overgeslagen')
                        break
                res = menukaart.naar_json(menukaart.extraheer(tekst))
                if res:
                    gevonden = {'date': f'{ts[:4]}-{ts[4:6]}-{ts[6:8]}', 'bron': 'wayback',
                                'platform': platform, 'filiaal': filiaal,
                                'url': f'https://web.archive.org/web/{ts}/{url}', **res}
                    break
            if gevonden:
                nieuw.append(gevonden)
                log(f'[{i + 1}/{len(groepen)}] {maand} {platform} {filiaal}: '
                    + json.dumps({k: v for k, v in gevonden.items() if k in ('nuggets', 'veggie', 'bigmac')}))
            else:
                mislukt += 1
                log(f'[{i + 1}/{len(groepen)}] {maand} {platform} {filiaal}: geen prijzen')
            # tussentijds bewaren: een onderbroken run verliest niets
            if len(nieuw) and len(nieuw) % 20 == 0:
                historie.voeg_toe(raw, nieuw, vervang=False)
                nieuw = []
                historie.schrijf_json_atomisch(args.history, historie.bouw(history, raw=raw, economist=economist))
        historie.voeg_toe(raw, nieuw, vervang=False)
        log(f'Klaar: {geprobeerd} pagina’s geprobeerd, {mislukt} combinaties zonder prijzen')

    uit = historie.bouw(history, raw=raw, economist=economist)
    historie.schrijf_json_atomisch(args.history, uit)
    for naam, r in uit['series'].items():
        if r:
            log(f'{naam}: {len(r)} punten, {r[0]["date"]} t/m {r[-1]["date"]}')
    log(f'raw: {len(uit["raw"])} metingen, waarvan {sum(1 for r in uit["raw"] if r.get("uitgesloten"))} met uitgesloten waarden')


if __name__ == '__main__':
    main()

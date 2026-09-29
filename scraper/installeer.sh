#!/bin/bash
# Installeert de prijsscraper van canitnugget.nl op trogdor.
# Idempotent: opnieuw draaien na een wijziging in de repo is de manier om te deployen.
#   sudo ./installeer.sh
set -euo pipefail
cd "$(dirname "$0")"

DOEL=/usr/local/lib/canitnugget
WEBROOT=/var/www/canitnugget
GEBRUIKER=canitnugget

[ "$(id -u)" -eq 0 ] || { echo "Draai als root (sudo)"; exit 1; }

getent passwd "$GEBRUIKER" >/dev/null || \
    useradd --system --home-dir /var/lib/canitnugget --no-create-home \
            --shell /usr/sbin/nologin --comment "canitnugget.nl prijsscraper" "$GEBRUIKER"

install -d -m 755 "$DOEL"
install -m 755 nugget_prijzen.py backfill_wayback.py "$DOEL"/
install -m 644 menukaart.py historie.py filialen.json "$DOEL"/

# Schrijfrecht op alleen deze ene webroot-map (tmp + rename vraagt schrijfrecht
# op de map, niet op het bestand). Via een ACL, zodat eigenaar en groep
# (www-data) ongemoeid blijven.
command -v setfacl >/dev/null || apt-get install -y acl
setfacl -m "u:$GEBRUIKER:rwx" "$WEBROOT"

install -m 644 systemd/canitnugget-prijzen.service systemd/canitnugget-prijzen.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now canitnugget-prijzen.timer
systemctl list-timers canitnugget-prijzen.timer --no-pager

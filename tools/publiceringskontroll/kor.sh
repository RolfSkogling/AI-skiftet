#!/usr/bin/env bash
# kor.sh — BLOCKERANDE publiceringskontroll for ai-skiftet.se.
#
# Kor forkontrollen mot repo-roten pa disk och DAREFTER mot den publicerade
# sajten. Returnerar icke-noll om nagot av stegen gor det, och fortsatter
# ALDRIG tyst efter ett fel: faller forkontrollen ska ingenting pushas, och da
# finns det inget att mata mot live.
#
#   bash tools/publiceringskontroll/kor.sh --slug sa-mycket-sa-fort
#   bash tools/publiceringskontroll/kor.sh                  # svepet, bada lagena
#   bash tools/publiceringskontroll/kor.sh --rot /nagon/annan/klon --slug X
#
# Exitkoder: 0 = bada stegen rena. 1 = en lankad essa utan spelbart ljudkort.
# 2 = kontrollfel, alltsa en kontroll som inte kunnat mata det den ska skydda.
# Varken 1 eller 2 ar ett godkannande.
set -euo pipefail

HAR="$(cd "$(dirname "$0")" && pwd)"
KONTROLL="$HAR/check_ljudkort.py"
ROT="$(cd "$HAR/../.." && pwd)"

if [ "${1:-}" = "--rot" ]; then
  [ -n "${2:-}" ] || { echo "BLOCKERAD: --rot utan vardet." >&2; exit 2; }
  ROT="$2"; shift 2
fi

blockera() { echo "BLOCKERAD: $*" >&2; exit 2; }

[ -f "$KONTROLL" ]  || blockera "hittar inte granskaren: $KONTROLL"
[ -d "$ROT" ]       || blockera "repo-roten finns inte: $ROT"
command -v python3 >/dev/null || blockera "python3 saknas"
# Innehallsgrind: ratt filnamn racker inte, det ska vara ratt fil. En trunkerad
# eller overskriven granskare far inte ge gront genom att inte gora nagot.
grep -q "def bedom_sprak" "$KONTROLL" \
  || blockera "check_ljudkort.py ser inte ut som granskaren (saknar 'def bedom_sprak')"
grep -q "def granska_ljudkort" "$KONTROLL" \
  || blockera "check_ljudkort.py saknar ljudkortslasaren 'def granska_ljudkort'"

steg() {
  etikett="$1"; shift
  echo "" >&2
  echo "=== $etikett ===" >&2
  kod=0
  "$@" || kod=$?
  if [ "$kod" -ne 0 ]; then
    echo "" >&2
    echo "BLOCKERAD i steget \"$etikett\": exitkod $kod. Ingen fortsattning, inget godkannande." >&2
    exit "$kod"
  fi
}

steg "forkontroll pa disk (--local $ROT)" \
     python3 "$KONTROLL" --local "$ROT" "$@"
steg "live-kontroll mot den publicerade sajten (--live)" \
     python3 "$KONTROLL" --live "$@"

echo "" >&2
echo "BADA STEGEN RENA: forkontrollen och live-kontrollen ar overens om att ingen lankad essa saknar spelbart ljudkort." >&2

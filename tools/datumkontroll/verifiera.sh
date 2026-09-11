#!/usr/bin/env bash
# Kor regressionsprovet och kontrollen mot de tre forstasidorna i en lokal klon.
# Avbryter pa forsta fel - en spärr som fortsatter efter ett fel skyddar inget.
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "== regressionsprov =="
python3 tools/datumkontroll/test_updated_date.py

echo
echo "== kontroll mot arbetstradet =="
python3 tools/datumkontroll/updated_date.py check index.html en/index.html no/index.html

if [ "${1:-}" = "--live" ]; then
  echo
  echo "== kontroll mot live =="
  python3 tools/datumkontroll/updated_date.py check --live
fi

echo
echo "datumkontroll: OK"

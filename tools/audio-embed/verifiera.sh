#!/usr/bin/env bash
# Verifiering av ljudspelarkontrollen. Fallerar (exit != 0) om spelaren
# saknas eller ar dubbelinbaddad.
#
#   bash tools/audio-embed/verifiera.sh                  # regressionsprovet
#   bash tools/audio-embed/verifiera.sh --live <basename>  # publicerade sidor
set -euo pipefail
HAR="$(cd "$(dirname "$0")" && pwd)"

if [ "${1:-}" != "--live" ]; then
    cd "$HAR"
    exec python3 -m unittest test_audio_embed_check -v
fi

BASE="${2:?anvandning: verifiera.sh --live <basename>}"
RAW="https://raw.githubusercontent.com/RolfSkogling/AI-skiftet/main"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fel=0
for L in sv en no; do
    if [ "$L" = "sv" ]; then path="${BASE}.html"; else path="${L}/${BASE}.html"; fi
    code=$(curl -sS -o "$TMP/$L.html" -w "%{http_code}" "$RAW/$path" || echo "000")
    if [ "$code" != "200" ]; then
        printf "%-4s %s: HTTP %s\n" "$L" "$path" "$code"
        continue
    fi
    status=$(python3 "$HAR/audio_embed_check.py" "$TMP/$L.html" "$BASE" || true)
    printf "%-4s %-34s %s\n" "$L" "$path" "$status"
    [ "$status" = "present" ] || fel=1
done

if [ "$fel" -ne 0 ]; then
    echo "FEL: ljudspelaren saknas eller ar dubblerad pa minst en sida." >&2
    exit 1
fi
echo "OK: spelaren finns exakt en gang pa alla tre sprak."

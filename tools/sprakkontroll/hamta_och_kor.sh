#!/usr/bin/env bash
# hamta_och_kor.sh — hamtar sprakkontrollen ur repot och kor den, med en egen
# grind pa varje steg. Avsedd for korningar som INTE har en lokal klon
# (schemalagda Cowork-korningar mot GitHub Contents API).
#
# Bakgrund (2026-08-24): STEG 6.6 hamtade tidigare check_language.py med
#   curl -sS ... -o tools/sprakkontroll/$f
# utan -f, utan statuskontroll och utan set -e. En misslyckad nedladdning gav en
# TOM .py-fil, och `python3 tom_fil.py` avslutar med kod 0. Regeln i SKILL.md
# lyder "Exit 0 -> ga vidare till STEG 7", sa den blockerande sparren slappte
# igenom publiceringen utan att ha kort en enda kontroll. Varje led nedan har
# darfor sin egen grind, och allt som inte gar att styrka blockerar.
#
# Anvandning (arbetskatalogen ska redan innehalla dagens sidor i ratt struktur:
# index.html, nyheter/index.html, en/index.html, en/nyheter/index.html,
# no/index.html, no/nyheter/index.html):
#
#   TOK="$(cat ~/AI/.secrets/.github-token)" bash hamta_och_kor.sh /tmp/sprakkontroll 6
#
# Exit 0 = rent OCH tillrackligt manga filer granskade. Allt annat blockerar.
set -euo pipefail

ARBETSKAT="${1:?ange arbetskatalog (dar dagens sidor ligger i ratt struktur)}"
MINST="${2:-6}"
REPO="${SPRAKKONTROLL_REPO:-RolfSkogling/AI-skiftet}"
API="${SPRAKKONTROLL_API:-https://api.github.com/repos/$REPO/contents/tools/sprakkontroll}"

blockera() { echo "BLOCKERAD: $*" >&2; exit 1; }

[ -n "${TOK:-}" ]  || blockera "TOK saknas — kan inte hamta sprakkontrollen."
[ -d "$ARBETSKAT" ] || blockera "arbetskatalogen finns inte: $ARBETSKAT"

VERKTYG="$ARBETSKAT/tools/sprakkontroll"
mkdir -p "$VERKTYG"

for f in check_language.py ordbok.json; do
  rm -f "$VERKTYG/$f"
  kod="$(curl -fsS -o "$VERKTYG/$f" -w '%{http_code}' \
           -H "Authorization: Bearer $TOK" \
           -H "Accept: application/vnd.github.raw" \
           "$API/$f?ref=main")" \
    || blockera "nedladdning av $f misslyckades (curl- eller HTTP-fel)"
  [ "$kod" = "200" ] || blockera "$f gav HTTP $kod"
  [ -s "$VERKTYG/$f" ] || blockera "$f laddades ner tomt"
done

# Innehallsgrind. Ratt filstorlek racker inte — det ska vara ratt fil. En
# felsida, en trunkerad nedladdning eller ett API-felmeddelande i JSON-form
# passerar storlekskontrollen men inte den har.
grep -q "def main" "$VERKTYG/check_language.py" \
  || blockera "check_language.py ser inte ut som granskaren (saknar 'def main')"
grep -q "def stad" "$VERKTYG/check_language.py" \
  || blockera "check_language.py saknar textrensaren 'def stad'"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get("termer") else 1)' \
  "$VERKTYG/ordbok.json" 2>/dev/null \
  || blockera "ordbok.json ar inte en giltig ordbok med termer"

RADER="$(wc -l < "$VERKTYG/check_language.py" | tr -d ' ')"
TERMER="$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["termer"]))' "$VERKTYG/ordbok.json")"
echo "Sprakkontroll hamtad och verifierad: ${RADER} rader granskare, ${TERMER} termpar." >&2

cd "$ARBETSKAT"
exec python3 tools/sprakkontroll/check_language.py --minst "$MINST"

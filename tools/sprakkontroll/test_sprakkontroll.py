#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regressionstester for sprakkontrollen (2026-08-24).

Principen ar densamma som i dedup-fixen: ett test som bara visar att det blev
gront bevisar ingenting. Varje test har kor BADE den gamla logiken och den nya
mot samma indata, och kraver att den gamla SLAPPTE IGENOM felet och att den nya
FANGAR det. Gar den gamla logiken plotsligt ocksa igenom testet ar testet
trasigt, inte fixen bevisad.

    python3 tools/sprakkontroll/test_sprakkontroll.py

Exit 0 = alla tester gick igenom.
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

HAR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HAR))
GRANSKARE = os.path.join(HAR, "check_language.py")

spec = importlib.util.spec_from_file_location("check_language", GRANSKARE)
cl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cl)

REGLER, EGENNAMN, FELSTAVNINGAR = cl.las_ordbok()

RESULTAT: list[tuple[bool, str]] = []


def kolla(villkor: bool, beskrivning: str) -> None:
    RESULTAT.append((bool(villkor), beskrivning))
    print(("  OK   " if villkor else "  FEL  ") + beskrivning)


# ---------------------------------------------------------------------------
# Den GAMLA textrensaren, ordagrant som den sag ut fore 2026-08-24.
# Skillnad mot den nya: negativ lookahead pa exakt sprakstrangen, inget
# undantag for rotelementet, ingen normalisering av sprakkod.
# ---------------------------------------------------------------------------
def gammal_stad(text: str, sprak: str, egennamn) -> str:
    for monster in (r"<script\b.*?</script>", r"<style\b.*?</style>", r"<!--.*?-->"):
        text = re.sub(monster, cl._tomma_rader, text, flags=re.S | re.I)
    text = re.sub(r"<(\w+)\b[^>]*\blang=\"(?!" + sprak + r"\b)[^\"]*\"[^>]*>.*?</\1>",
                  cl._tomma_rader, text, flags=re.S | re.I)
    text = re.sub(r"<div[^>]*class=\"[^\"]*news-card__source[^\"]*\"[^>]*>.*?</div>",
                  cl._tomma_rader, text, flags=re.S | re.I)
    text = re.sub(r"<(\w+)[^>]*class=\"[^\"]*lang-switcher[^\"]*\"[^>]*>.*?</\1>",
                  cl._tomma_rader, text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = cl.html.unescape(text)
    for namn in egennamn:
        text = re.sub(re.escape(namn), " ", text, flags=re.I)
    return text


def granska_med(stad_funktion, namn, text, sprak):
    """Kor cl.granska men med vald textrensare (monkeypatch, aterstalls alltid)."""
    original = cl.stad
    cl.stad = stad_funktion
    try:
        return cl.granska(namn, text, sprak, REGLER, EGENNAMN, FELSTAVNINGAR)
    finally:
        cl.stad = original


SVENSK_LACKA_I_NORSK_SIDA = (
    '<!DOCTYPE html>\n<html lang="nb">\n<head><title>Test</title></head>\n'
    '<body>\n<h1>Test</h1>\n'
    '<p>Dette foretaket har inte tillgang til verktyg for oppgaven.</p>\n'
    '</body>\n</html>\n'
)

NORSK_CITAT_I_SVENSK_SIDA = (
    '<!DOCTYPE html>\n<html lang="sv">\n<head><title>Test</title></head>\n'
    '<body>\n<h1>Test</h1>\n'
    '<p>Statnett skriver att man &rdquo;<span lang="nb">videregaende '
    'opplaering</span>&rdquo; i rapporten.</p>\n'
    '</body>\n</html>\n'
)

NORSK_LACKA_I_SVENSK_SIDA = (
    '<!DOCTYPE html>\n<html lang="sv">\n<head><title>Test</title></head>\n'
    '<body>\n<h1>Test</h1>\n'
    '<p>Eleverna i videregaende opplaering far en milliard kronor.</p>\n'
    '</body>\n</html>\n'
)

TYPO_I_SPRAKKOD = (
    '<!DOCTYPE html>\n<html lang="sv">\n<head><title>Test</title></head>\n'
    '<body>\n<div lang="svenska">\n'
    '<p>Eleverna i videregaende opplaering far en milliard kronor.</p>\n'
    '</div>\n</body>\n</html>\n'
)


def test_1_norsk_sida_granskas():
    print("\nTEST 1 — svenskt ord i norsk sida (fynd 1)")
    gammal = granska_med(gammal_stad, "no/index.html", SVENSK_LACKA_I_NORSK_SIDA, "no")
    ny = granska_med(cl.stad, "no/index.html", SVENSK_LACKA_I_NORSK_SIDA, "no")
    kolla(len(gammal) == 0,
          "gammal logik slappte igenom (%d traffar — felet passerade)" % len(gammal))
    kolla(len(ny) > 0,
          "ny logik fangar det (%d traffar: %s)"
          % (len(ny), ", ".join(sorted({t["term"] for t in ny}))))


# FRYST fixtur, strukturen hos en publicerad no/index.html som den sag ut nar
# fynd 1 gjordes: rotelement <html lang="nb">, lang-switcher, nyhetskort.
#
# Fixturen var tidigare den LEVANDE filen no/index.html. Det testet slutade
# fungera nar sidan andrades: dagens no/index.html saknar sluttagg </html> helt,
# sa den gamla regexen <(\w+) ... lang= ...>.*?</\1> kan inte langre matcha
# rotelementet och den katastrofala tomningen gar inte att reproducera. Testet
# rapporterade da FEL fast grinden var frisk — en falsklarmande testsvit slutar
# man lita pa. Fixturen ar darfor fryst har och beror inte langre pa
# nyhetsinnehall som roterar var sjunde dag. (Rattat 2026-09-02.)
PUBLICERAD_NORSK_SIDA = (
    '<!DOCTYPE html>\n<html lang="nb">\n'
    '<head><meta charset="UTF-8"><title>AI-skiftet</title></head>\n'
    '<body>\n'
    '<nav class="site-nav"><div class="lang-switcher">\n'
    '  <a href="../index.html" lang="sv">SV</a>\n'
    '  <a href="../en/index.html" lang="en">EN</a>\n'
    '</div></nav>\n'
    '<div class="news-card">\n'
    '  <h3>Nyheter fra Norden</h3>\n'
    '  <p>Dette foretaket har inte tillgang til verktyg for oppgaven, og '
    'regjeringen mener at bedriftene trenger mer stotte enn i dag.</p>\n'
    '</div>\n'
    + ('<p>Utfyllende brodtekst som skal granskas av sperren.</p>\n' * 40) +
    '</body>\n</html>\n'
)


def test_2_publicerad_norsk_sida():
    print("\nTEST 2 — publicerad norsk sida tomdes helt av gamla logiken (fynd 1)")
    raw = PUBLICERAD_NORSK_SIDA
    g = len(gammal_stad(raw, "no", EGENNAMN).strip())
    n = len(cl.stad(raw, "no", EGENNAMN).strip())
    kolla(g == 0, "gammal logik lamnade %d tecken att granska av %d" % (g, len(raw)))
    kolla(n > 1000, "ny logik lamnar %d tecken att granska av %d" % (n, len(raw)))
    kolla(len(granska_med(cl.stad, "no/index.html", raw, "no")) > 0,
          "och ny logik hittar det svenska lackaget i sidan")


def test_3_avsett_citat_undantas_fortfarande():
    print("\nTEST 3 — avsett <span lang=\"nb\">-citat far inte borja fallera (regression)")
    citat = granska_med(cl.stad, "index.html", NORSK_CITAT_I_SVENSK_SIDA, "sv")
    utan_citat = granska_med(cl.stad, "index.html", NORSK_LACKA_I_SVENSK_SIDA, "sv")
    kolla(len(citat) == 0,
          "citat markerat med lang=\"nb\" hoppas fortfarande over (%d traffar)" % len(citat))
    kolla(len(utan_citat) > 0,
          "samma ord utan citatmarkering fallerar fortfarande (%d traffar)" % len(utan_citat))


def test_4_okand_sprakkod_tystar_inte():
    print("\nTEST 4 — felstavad sprakkod far inte tysta innehallet")
    gammal = granska_med(gammal_stad, "index.html", TYPO_I_SPRAKKOD, "sv")
    ny = granska_med(cl.stad, "index.html", TYPO_I_SPRAKKOD, "sv")
    kolla(len(gammal) == 0,
          'gammal logik tomde <div lang="svenska"> och slappte igenom (%d traffar)' % len(gammal))
    kolla(len(ny) > 0,
          "ny logik granskar okand sprakkod i stallet for att tomma den (%d traffar)" % len(ny))


def test_5_sprakfamilj():
    print("\nTEST 5 — normalisering av sprakkod")
    fall = [("nb", "no"), ("nb-NO", "no"), ("nn", "no"), ("no", "no"),
            ("sv", "sv"), ("sv-SE", "sv"), ("en", "en"), ("en-US", "en"),
            ("svenska", None), ("", None), ("de", None)]
    fel = [(k, v, cl.sprakfamilj(k)) for k, v in fall if cl.sprakfamilj(k) != v]
    kolla(not fel, "alla %d koder normaliseras ratt%s"
          % (len(fall), "" if not fel else " — fel: %s" % fel))


# ---------------------------------------------------------------------------
# Fynd 2 — tackningsgrinden och den harda nedladdningen
# ---------------------------------------------------------------------------

def _bygg_arbetskatalog(tmp, antal_html=0):
    """Minimal arbetskatalog: verktygen pa plats, N html-filer i roten."""
    verktyg = os.path.join(tmp, "tools", "sprakkontroll")
    os.makedirs(verktyg, exist_ok=True)
    shutil.copy2(GRANSKARE, verktyg)
    shutil.copy2(os.path.join(HAR, "ordbok.json"), verktyg)
    for i in range(antal_html):
        with open(os.path.join(tmp, "sida%d.html" % i), "w", encoding="utf-8") as fh:
            fh.write('<!DOCTYPE html>\n<html lang="sv">\n<body><p>Ren svensk text.</p></body>\n</html>\n')
    return verktyg


def _kor_granskare(tmp, extra=()):
    return subprocess.run(
        [sys.executable, os.path.join(tmp, "tools", "sprakkontroll", "check_language.py"), *extra],
        cwd=tmp, capture_output=True, text=True)


def test_6_noll_granskade_filer():
    print("\nTEST 6 — noll granskade filer far inte ge gront (fynd 2)")
    with tempfile.TemporaryDirectory() as tmp:
        _bygg_arbetskatalog(tmp, antal_html=0)
        # --minst 0 ar exakt det gamla kontraktet: ingen tackningsgrind alls.
        gammal = _kor_granskare(tmp, ["--minst", "0"])
        ny = _kor_granskare(tmp)
        kolla(gammal.returncode == 0,
              "gammalt kontrakt (--minst 0): exit %d pa noll filer — gront utan att ha last nagot"
              % gammal.returncode)
        kolla(ny.returncode == 1,
              "nytt kontrakt (standard --minst 1): exit %d" % ny.returncode)
        kolla("0 filer granskade" in ny.stderr,
              "felmeddelandet sager vad som saknades: %s" % ny.stderr.strip().splitlines()[-1][:90])


def test_7_for_fa_filer():
    print("\nTEST 7 — halv filmangd fangas av --minst (fynd 2)")
    with tempfile.TemporaryDirectory() as tmp:
        _bygg_arbetskatalog(tmp, antal_html=3)
        sex = _kor_granskare(tmp, ["--minst", "6"])
        tre = _kor_granskare(tmp, ["--minst", "3"])
        kolla(sex.returncode == 1, "3 av 6 forvantade filer: exit %d" % sex.returncode)
        kolla(tre.returncode == 0, "3 av 3 forvantade filer: exit %d" % tre.returncode)


CURL_STUB = """#!/bin/bash
# stub-curl for test. Beteende styrs av $STUB_LAGE.
mal=""
while [ $# -gt 0 ]; do
  case "$1" in
    -o) mal="$2"; shift 2;;
    *) shift;;
  esac
done
case "$STUB_LAGE" in
  http_fel)   exit 22;;                                   # curl -f mot 404
  tom)        : > "$mal"; echo -n "200"; exit 0;;         # 200 men tom kropp
  felsida)    echo '<html>404 Not Found</html>' > "$mal"; echo -n "200"; exit 0;;
esac
exit 1
"""


def _kor_hamtaren(tmp, lage):
    bindir = os.path.join(tmp, "bin")
    os.makedirs(bindir, exist_ok=True)
    stub = os.path.join(bindir, "curl")
    with open(stub, "w") as fh:
        fh.write(CURL_STUB)
    os.chmod(stub, 0o755)
    arbete = os.path.join(tmp, "arbete")
    os.makedirs(os.path.join(arbete, "tools", "sprakkontroll"), exist_ok=True)
    env = dict(os.environ, PATH=bindir + os.pathsep + os.environ["PATH"],
               TOK="dummy-token-anvands-aldrig", STUB_LAGE=lage)
    return subprocess.run(["bash", os.path.join(HAR, "hamta_och_kor.sh"), arbete, "6"],
                          capture_output=True, text=True, env=env), arbete, env


GAMLA_SNUTTEN = """set -u
cd "$1"
for f in check_language.py ordbok.json; do
  curl -sS -H "Authorization: Bearer $TOK" -H "Accept: application/vnd.github.raw" \\
    -o "tools/sprakkontroll/$f" \\
    "https://api.github.com/repos/RolfSkogling/AI-skiftet/contents/tools/sprakkontroll/$f?ref=main"
done
python3 tools/sprakkontroll/check_language.py
"""


def test_8_misslyckad_nedladdning_blockerar():
    print("\nTEST 8 — misslyckad nedladdning maste blockera publicering (fynd 2)")
    for lage, forvantat in (("http_fel", "curl- eller HTTP-fel"),
                            ("tom", "laddades ner tomt"),
                            ("felsida", "ser inte ut som granskaren")):
        with tempfile.TemporaryDirectory() as tmp:
            res, arbete, env = _kor_hamtaren(tmp, lage)
            kolla(res.returncode != 0 and "BLOCKERAD" in res.stderr,
                  "lage '%s': ny hamtare exit %d — %s"
                  % (lage, res.returncode, res.stderr.strip().splitlines()[-1][:80]
                     if res.stderr.strip() else "(ingen stderr)"))
            # Samma stub mot den GAMLA snutten ur SKILL.md.
            gammal_dir = os.path.join(tmp, "gammal")
            os.makedirs(os.path.join(gammal_dir, "tools", "sprakkontroll"), exist_ok=True)
            skript = os.path.join(tmp, "gammal.sh")
            with open(skript, "w") as fh:
                fh.write(GAMLA_SNUTTEN)
            gammal = subprocess.run(["bash", skript, gammal_dir],
                                    capture_output=True, text=True, env=env)
            if lage == "tom":
                kolla(gammal.returncode == 0,
                      "lage '%s': gamla snutten exit %d — publicering hade slappts igenom"
                      % (lage, gammal.returncode))
            else:
                print("       (gamla snutten exit %d i lage '%s')" % (gammal.returncode, lage))


# ---------------------------------------------------------------------------
# TEST 9 — stavningsdetektorn (fynd 3, 2026-09-02)
# ---------------------------------------------------------------------------
STAVFEL_I_SVENSK_SIDA = (
    '<!DOCTYPE html>\n<html lang="sv">\n<head><title>Test</title></head>\n'
    '<body>\n<h1>Test</h1>\n'
    '<p>Samma dag presenterade bolaget ocks&auml; en utvidgad satsning.</p>\n'
    '</body>\n</html>\n'
)


def test_9_stavningsdetektorn():
    print("\nTEST 9 — felstavad omljudsvokal fangas (fynd 3)")

    # Den GAMLA logiken = ordboken UTAN felstavningsblocket. Exakt det tillstand
    # som lag i produktion 2026-08-28, da 'ocksa' med a-umlaut publicerades och
    # passerade den blockerande grinden orort.
    import json, tempfile
    with open(cl.ORDBOK, encoding="utf-8") as f:
        data = json.load(f)
    kolla("felstavningar" in data and len(data["felstavningar"]) > 0,
          "ordboken har ett felstavningsblock (%d poster)"
          % len(data.get("felstavningar", [])))
    utan = dict(data); utan.pop("felstavningar", None)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as f:
        json.dump(utan, f, ensure_ascii=False)
        gammal_ordbok = f.name
    g_regler, g_egennamn, g_fel = cl.las_ordbok(gammal_ordbok)
    os.unlink(gammal_ordbok)

    gammal = cl.granska("index.html", STAVFEL_I_SVENSK_SIDA, "sv",
                        g_regler, g_egennamn, g_fel)
    ny = cl.granska("index.html", STAVFEL_I_SVENSK_SIDA, "sv",
                    REGLER, EGENNAMN, FELSTAVNINGAR)

    kolla(len(gammal) == 0,
          "gammal logik slappte igenom 'ocksa' med a-umlaut (%d traffar — "
          "sa kom stavfelet ut i produktion 2026-08-28)" % len(gammal))
    kolla(any(t["fran"] == "felstavning" for t in ny),
          "ny logik fangar det (%d traffar: %s -> %s)"
          % (len(ny), ", ".join(t["term"] for t in ny),
             ", ".join(t["ratt"] for t in ny)))

    # Varfor de gamla detektorerna inte kunde se det:
    kolla(not any(m in STAVFEL_I_SVENSK_SIDA for m in cl.MOJIBAKE),
          "felet ar INTE mojibake — valformad UTF-8, mojibake-listan var blind")
    termer = {t.lower() for post in data["termer"] for t in post.get("sv", []) + post.get("no", [])}
    kolla("ocks\u00e4" not in termer,
          "felet star INTE i termlistan — det ar inget ord pa nagot sprak, "
          "sa ordboksregeln var blind")

    # Precisionskrav: listan far inte fyra pa korrekt text.
    ren = STAVFEL_I_SVENSK_SIDA.replace("ocks&auml;", "ocks&aring;")
    kolla(len(cl.granska("index.html", ren, "sv", REGLER, EGENNAMN, FELSTAVNINGAR)) == 0,
          "och den ratta stavningen ger noll traffar (ingen falsklarm)")


def test_10_felstavningslistan_ar_disjunkt():
    print("\nTEST 10 — felstavningslistan krockar inte med termlistan")
    import json
    with open(cl.ORDBOK, encoding="utf-8") as f:
        data = json.load(f)
    korrekta = set()
    for t in data["termer"]:
        for k in ("no", "sv", "en"):
            korrekta.update(x.lower() for x in t.get(k, []))
    krock = sorted({p["fel"] for p in data.get("felstavningar", [])
                    if p["fel"].lower() in korrekta})
    kolla(not krock,
          "ingen felstavning ar samtidigt en korrekt term (%s)"
          % (", ".join(krock) if krock else "0 krockar"))
    sprak_ok = all(p.get("sprak") in ("sv", "no", "en")
                   for p in data.get("felstavningar", []))
    kolla(sprak_ok, "alla poster har giltig sprakkod")


def main() -> int:
    print("Regressionstester sprakkontroll — gammal logik mot ny, samma indata.")
    for t in (test_1_norsk_sida_granskas, test_2_publicerad_norsk_sida,
              test_3_avsett_citat_undantas_fortfarande, test_4_okand_sprakkod_tystar_inte,
              test_5_sprakfamilj, test_6_noll_granskade_filer, test_7_for_fa_filer,
              test_8_misslyckad_nedladdning_blockerar,
              test_9_stavningsdetektorn, test_10_felstavningslistan_ar_disjunkt):
        t()
    fel = [b for ok, b in RESULTAT if not ok]
    print("\n%d kontroller, %d fel." % (len(RESULTAT), len(fel)))
    for b in fel:
        print("  FEL: " + b)
    return 1 if fel else 0


if __name__ == "__main__":
    sys.exit(main())

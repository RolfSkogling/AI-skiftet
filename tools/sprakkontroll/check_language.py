#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sprakkontroll for ai-skiftet.se - mekanisk sparr mot spraklackage.

Fallerar (exit 1) om norska ord forekommer i svensk text, svenska ord i norsk
text, nordiska facktermer i engelsk text, ELLER om ett ord ar felstavat med fel
omljudsvokal (ocksa med a-umlaut i stallet for a-ring). Korrekturlasning fangar inte
den har feltypen: norska i svensk text laser flytande.

Anvandning:
    python3 tools/sprakkontroll/check_language.py            # hela repot
    python3 tools/sprakkontroll/check_language.py index.html no/index.html
    python3 tools/sprakkontroll/check_language.py --live     # mot publicerad sajt
    python3 tools/sprakkontroll/check_language.py --json     # maskinlasbart
    python3 tools/sprakkontroll/check_language.py --minst 6  # krav pa tackning

Exitkoder: 0 = rent, 1 = traffar ELLER for fa granskade filer.

Undantag: satt lang-attribut pa elementet, t.ex.
    <span lang="nb">videregaende opplaering</span>
sa hoppas innehallet over (avsett citat pa annat sprak). Sprakkoden normaliseras
(nb, nb-NO och nn ar norska), och rotelementet <html> undantas fran regeln —
annars raknas hela dokumentet som ett citat och granskas aldrig.
"""
import argparse, html, json, os, re, sys, urllib.request

HAR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HAR))
ORDBOK = os.path.join(HAR, "ordbok.json")
SPRAK = ("sv", "no", "en")
# Sokvagen ger sprak "sv"/"no"/"en", men dokumenten markerar sig med BCP 47-koder.
# De norska sidorna anvander lang="nb". Utan den har mappningen raknades
# <html lang="nb"> som ett frammandespraakigt citat, och HELA den norska sidan
# tomdes fore granskning — spaerren gav gront utan att ha last nagot
# (upptackt och lagat 2026-08-24).
SPRAKFAMILJ = {"sv": {"sv"}, "no": {"no", "nb", "nn"}, "en": {"en"}}
MOJIBAKE = ["\u00c3\u00a4", "\u00c3\u00b6", "\u00c3\u00a5", "\u00c3\u00a6",
            "\u00c3\u00b8", "\u00c3\u2026", "\u00c3\u201e", "\u00c3\u2013",
            "\u00e2\u20ac", "\u00c2\u00a0"]
LIVE_BAS = "https://ai-skiftet.se"
# Nyhetssidorna ar minimikravet — de maste alltid granskas aven om repot
# saknas (schemalagda korningar utan klon).
LIVE_KARNA = ["/index.html", "/nyheter/index.html", "/en/index.html",
              "/en/nyheter/index.html", "/no/index.html", "/no/nyheter/index.html"]


def live_sidor():
    """Alla publicerade HTML-sidor, harledda ur repot.

    Tidigare var det har en hardkodad lista pa sex nyhetssidor. Foljden var att
    essasidorna ALDRIG granskades mot live: fem spraktraffar i no/delningen.html,
    no/minnet-som-vager-ewmc.html och no/turbulenta-aren.html lag opptackta tills
    ett fullrepo-svep gjordes for hand 2026-09-02. En hardkodad lista vaxer inte
    med sajten — den harleds nu i stallet, sa varje ny essa tacks automatiskt.
    """
    sidor = list(LIVE_KARNA)
    if os.path.isdir(ROOT):
        for kat, undermappar, filnamn in os.walk(ROOT):
            undermappar[:] = [d for d in undermappar
                              if d not in (".git", "node_modules", "assets", "audio")]
            for f in filnamn:
                if not f.endswith(".html"):
                    continue
                rel = os.path.relpath(os.path.join(kat, f), ROOT).replace(os.sep, "/")
                url = "/" + rel
                if url not in sidor:
                    sidor.append(url)
    return sidor


def las_ordbok(sokvag=ORDBOK):
    with open(sokvag, encoding="utf-8") as f:
        data = json.load(f)
    regler = {s: [] for s in SPRAK}
    for post in data["termer"]:
        no = [t.lower() for t in post.get("no", [])]
        sv = [t.lower() for t in post.get("sv", [])]
        if post.get("handhavs", True) is False:
            continue
        en_kontroll = post.get("en_check", False)
        dom = post.get("dom", "")
        ratt_sv = ", ".join(post.get("sv", [])) or "(saknas)"
        ratt_no = ", ".join(post.get("no", [])) or "(saknas)"
        ratt_en = ", ".join(post.get("en", [])) or "(saknas)"
        for term in no:
            if term in sv:
                continue
            regler["sv"].append((term, "norska", ratt_sv, dom))
            if en_kontroll:
                regler["en"].append((term, "norska", ratt_en, dom))
        for term in sv:
            if term in no:
                continue
            regler["no"].append((term, "svenska", ratt_no, dom))
            if en_kontroll:
                regler["en"].append((term, "svenska", ratt_en, dom))
    # Felstavningar: strangar som inte ar ord pa nagot av spraken. Termlistan
    # ovan fangar RIKTIGA ord pa FEL sprak och kan per konstruktion inte se
    # felstavningar — "ocksa" med a-umlaut star inte i nagon ordlista och ar
    # valformad UTF-8, sa varken termregeln eller mojibake-listan reagerade.
    # Den luckan slapp igenom ett publicerat stavfel 2026-08-28.
    felstavningar = {s: [] for s in SPRAK}
    for post in data.get("felstavningar", []):
        sprak = post.get("sprak", "sv")
        if sprak not in felstavningar:
            continue
        felstavningar[sprak].append(
            (re.compile(r"(?<![\w-])" + re.escape(post["fel"]) + r"(?![\w-])", re.IGNORECASE),
             post["fel"], post["ratt"], post.get("kommentar", "")))

    kompilerat = {}
    for sprak, poster in regler.items():
        sedda, unika = set(), []
        for term, kalla, ratt, dom in poster:
            if term in sedda:
                continue
            sedda.add(term)
            kropp = r"\s+".join(re.escape(o) for o in term.split())
            unika.append((re.compile(r"(?<![\w-])" + kropp + r"(?![\w-])", re.IGNORECASE),
                          term, kalla, ratt, dom))
        kompilerat[sprak] = unika
    return kompilerat, data.get("tillatna_egennamn", []), felstavningar


def _tomma_rader(traff):
    return "\n" * traff.group(0).count("\n")


def sprakfamilj(varde):
    """'nb' -> 'no', 'nb-NO' -> 'no', 'sv-SE' -> 'sv'. None for okand kod.

    Okand kod ger medvetet None och INTE 'frammande sprak' — en felstavad
    lang-kod ska leda till att innehallet granskas, aldrig till att det tystas.
    """
    primar = re.split(r"[-_]", str(varde).strip().lower(), 1)[0]
    for familj, koder in SPRAKFAMILJ.items():
        if primar in koder:
            return familj
    return None


def stad(text, sprak, egennamn):
    """Ta bort kod, taggar/attribut, kallrader och egennamn. Bevarar radantal."""
    for monster in (r"<script\b.*?</script>", r"<style\b.*?</style>", r"<!--.*?-->"):
        text = re.sub(monster, _tomma_rader, text, flags=re.S | re.I)

    def _avsett_citat(traff):
        """Tomma bara element som BEVISLIGEN ar pa ett annat sprak.

        Skarpningar mot den gamla negativa lookaheaden `(?!sv\\b)`:
          1. sprakkoden normaliseras — nb, nb-NO och nn ar norska,
          2. okand sprakkod granskas i stallet for att tomas: en felstavad
             lang far aldrig tysta innehall.
        """
        familj = sprakfamilj(traff.group(2))
        if familj is None or familj == sprak:
            return traff.group(0)
        return _tomma_rader(traff)

    # `(?!html\b)` undantar ROTELEMENTET fran citatregeln, och det maste ske i
    # monstret — inte i _avsett_citat. Ett <html ...>-element som MATCHAR och
    # lamnas orort konsumerar anda hela dokumentet ur re.sub:s scanning, sa
    # inre citat skulle aldrig provas. Det var sa <html lang="nb"> tomde hela
    # den norska sidan: dokumentet raknades som ett frammandespraakigt citat
    # (2026-08-24).
    text = re.sub(r"<(?!html\b)(\w+)\b[^>]*\blang=\"([^\"]*)\"[^>]*>.*?</\1>",
                  _avsett_citat, text, flags=re.S | re.I)
    text = re.sub(r"<div[^>]*class=\"[^\"]*news-card__source[^\"]*\"[^>]*>.*?</div>",
                  _tomma_rader, text, flags=re.S | re.I)
    text = re.sub(r"<(\w+)[^>]*class=\"[^\"]*lang-switcher[^\"]*\"[^>]*>.*?</\1>",
                  _tomma_rader, text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    for namn in egennamn:
        text = re.sub(re.escape(namn), " ", text, flags=re.I)
    return text


def sprak_for(sokvag):
    delar = sokvag.replace(os.sep, "/").strip("/").split("/")
    if "en" in delar:
        return "en"
    if "no" in delar:
        return "no"
    return "sv"


def granska(namn, text, sprak, regler, egennamn, felstavningar=None):
    traffar = []
    felstavningar = felstavningar or {}
    for radnr, rad in enumerate(stad(text, sprak, egennamn).split("\n"), 1):
        if not rad.strip():
            continue
        for regex, fel, ratt, kommentar in felstavningar.get(sprak, ()):
            for m in regex.finditer(rad):
                traffar.append({"fil": namn, "rad": radnr, "sprak": sprak,
                                "term": m.group(0), "fran": "felstavning",
                                "ratt": ratt, "dom": kommentar or "stavning",
                                "kontext": rad[max(0, m.start() - 60):m.end() + 60].strip()})
        for regex, term, kalla, ratt, dom in regler[sprak]:
            for m in regex.finditer(rad):
                if m.group(0).isupper() and len(m.group(0)) <= 5:
                    continue          # akronym (FRA, LO, NHO), inte spraklackage
                traffar.append({"fil": namn, "rad": radnr, "sprak": sprak, "term": m.group(0),
                                "fran": kalla, "ratt": ratt, "dom": dom,
                                "kontext": rad[max(0, m.start() - 60):m.end() + 60].strip()})
    for radnr, rad in enumerate(text.split("\n"), 1):
        for m in MOJIBAKE:
            if m in rad:
                traffar.append({"fil": namn, "rad": radnr, "sprak": sprak, "term": m,
                                "fran": "mojibake", "ratt": "korrekt UTF-8", "dom": "teckenkodning",
                                "kontext": rad.strip()[:160]})
    return traffar


def samla_filer(argv):
    if argv:
        return [os.path.abspath(p) for p in argv]
    filer = []
    for kat, undermappar, filnamn in os.walk(ROOT):
        undermappar[:] = [d for d in undermappar if d not in (".git", "node_modules", "assets", "audio")]
        filer += [os.path.join(kat, f) for f in filnamn if f.endswith(".html")]
    return sorted(filer)


def main():
    p = argparse.ArgumentParser(description="Sprakkontroll ai-skiftet.se")
    p.add_argument("filer", nargs="*")
    p.add_argument("--live", action="store_true", help="granska publicerade sidor")
    p.add_argument("--json", action="store_true")
    p.add_argument("--ordbok", default=ORDBOK)
    p.add_argument("--minst", type=int, default=1, metavar="N",
                   help="fallera om farre an N filer granskades (standard 1). "
                        "Satt till antalet sidor som ska publiceras.")
    args = p.parse_args()

    regler, egennamn, felstavningar = las_ordbok(args.ordbok)
    traffar, antal = [], 0

    if args.live:
        for sida in live_sidor():
            url = LIVE_BAS + sida
            with urllib.request.urlopen(url, timeout=30) as r:
                text = r.read().decode("utf-8", "replace")
            antal += 1
            traffar += granska(url, text, sprak_for(sida), regler, egennamn, felstavningar)
    else:
        for sokvag in samla_filer(args.filer):
            rel = os.path.relpath(sokvag, ROOT)
            with open(sokvag, encoding="utf-8", errors="replace") as f:
                text = f.read()
            antal += 1
            traffar += granska(rel, text, sprak_for(rel), regler, egennamn, felstavningar)

    if args.json:
        print(json.dumps({"granskade": antal, "traffar": traffar}, ensure_ascii=False, indent=2))
    else:
        print("Sprakkontroll: %d filer granskade, %d traffar." % (antal, len(traffar)))
        for t in traffar:
            print("  %s:%s [%s] %s (%s) -> ratt: %s" % (t["fil"], t["rad"], t["sprak"],
                                                        t["term"], t["fran"], t["ratt"]))
            print("      ...%s..." % t["kontext"])
    # Tackningsgrind (2026-08-24): noll granskade filer ar INTE ett rent resultat.
    # Utan den har raden ger en tom filmangd — fel katalog, misslyckad
    # nedladdning, sidor skrivna pa fel plats — exit 0 och publiceringen slapps
    # igenom av en sparr som aldrig last nagot.
    if antal < args.minst:
        print("FALLERAR: %d filer granskade, minst %d kravs. Kontrollen har inte "
              "last det den skulle skydda — publicera INTE." % (antal, args.minst),
              file=sys.stderr)
        return 1

    if traffar:
        print("FALLERAR: %d spraktraffar i %d filer. Publicera INTE forran de ar rattade."
              % (len(traffar), antal), file=sys.stderr)
        return 1
    print("RENT: %d filer granskade, inga spraktraffar, ingen mojibake." % antal,
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

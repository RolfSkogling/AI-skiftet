#!/usr/bin/env python3
"""tag_norden.py — markerar notiser med NORDISK PRIMARVINKEL med taggen `norden`.

Bakgrund. Varje notis pa ai-skiftet.se slutar redan med ett "For Norden"-stycke,
sa en filtrering pa "namner Norden" skulle traffa 100 procent av notiserna och
vara meningslos. Det lasaren vill filtrera fram ar notiser dar den nordiska
handelsen ar SJALVA nyheten — svensk eller norsk myndighet, universitet, bolag,
fack eller politiker som primar aktor.

Det ar inte maskinellt identifierbart i dagens uppmarkning. `data-tags` bar bara
kategorin, och "For Norden"-stycket finns overallt. Losningen ar darfor
tvadelad:

1. FRAMAT: den dagliga pipelinen satter `norden` i `data-tags` nar notisen har
   nordisk primarvinkel. Notisen har redan den bedomningen gjord — redaktionella
   linjen punkt 1 kraver minst en sadan notis per dag. Det enda som saknades var
   att skriva ned den i uppmarkningen.

2. BAKAT: det har skriptet gor en heuristisk forsta gallring av arkivet.
   Heuristiken laser BARA rubriken och forsta stycket (= vad notisen handlar om),
   aldrig "For Norden"-stycket. Traffarna ska granskas av manniska; `--rapport`
   skriver ut dem utan att andra nagot.

Anvandning:
  python3 tools/feeds/tag_norden.py --repo . --rapport      # visa traffar
  python3 tools/feeds/tag_norden.py --repo . --skriv        # satt taggen
  python3 tools/feeds/tag_norden.py --repo . --skriv --undanta "slug1,slug2"
"""
import argparse
import html
import os
import re
import sys

SV = "nyheter/index.html"
FILES = {
    "sv": ["index.html", "nyheter/index.html"],
    "en": ["en/index.html", "en/nyheter/index.html"],
    "no": ["no/index.html", "no/nyheter/index.html"],
}

# Aktorer som gor en notis nordisk i sig. Bara egennamn och entydiga
# institutionsnamn — inga losa ord som "nordisk", som forekommer i varenda
# "For Norden"-stycke.
NORDISKA = [
    # myndigheter och offentliga organ
    "Riksdagen", "Regeringen", "Stortinget", "Folketinget", "Eduskunta",
    "IMY", "Integritetsskyddsmyndigheten", "Datatilsynet", "Datatilsynet",
    "MSB", "PTS", "Post- och telestyrelsen", "Nkom", "NVE", "Statnett",
    "Svenska kraftn", "Energimyndigheten", "Vinnova", "Forskningsr",
    "Skolverket", "Utdanningsdirektoratet", "Arbetsf", "SCB",
    "Statistisk sentralbyr", "Kammarkollegiet", "Nasjonal sikkerhetsmyndighet",
    "KI Norge", "AI Sweden", "E-h&auml;lsomyndigheten", "Helsedirektoratet",
    "Nasjonalbiblioteket", "Nasjonalbibliotekets", "Sigma2", "Digitaliserings",
    "Konkurrensverket", "Finansinspektionen", "Oljefonden", "Oljefondens",
    # larosaten och institut
    "KTH", "Chalmers", "Uppsala universitet", "Link&ouml;ping", "Karolinska", "NTNU",
    "UiO", "UiB", "Universitetet i Agder", "SINTEF", "Simula", "RISE", "WASP",
    "WACQT", "SciLifeLab", "DTU", "Aalto", "Stockholms universitet",
    "G&ouml;teborgs universitet", "Sahlgrenska", "NorwAI", "GPT-SW3",
    "NB-Whisper", "Berzelius", "LUMI",
    # bolag
    "Ericsson", "Telenor", "Telia", "Volvo", "Scania", "SAAB", "Saab",
    "Kongsberg", "Equinor", "Yara", "Hydro", "DNB", "SEB", "Nordea",
    "Swedbank", "Handelsbanken", "Klarna", "Spotify", "Lovable", "Tietoevry",
    "1X Technologies", "Nscale", "Aker", "ABB", "Universal Robots",
    "Husqvarna", "Electrolux", "IQM", "ScalinQ", "Tydal", "Computas",
    "Storebrand",
    # media och organisationer
    "SVT", "NRK", "Aftenposten", "Dagens Nyheter", "Ny Teknik",
    "Computer Sweden", "Breakit", "digi.no", "Kode24", "Internetstiftelsen",
    "Stim", "STIM", "TONO", "Tono", "NHO", "Unionen", "Nito", "Tekna",
    "Danske Regioner", "Nordiska ministerr", "CAI-X",
    # geografi som primar aktor
    "Lule&aring;", "Skien", "Narvik", "Tr&oslash;ndelag", "Arendalsuka",
    "Str&auml;ngn&auml;s", "Kajaani", "V&auml;ster&aring;s",
]
# Ordgrans i bada andar. Utan den traffade "Link" bade Link&ouml;ping och
# LinkedIn, och "LO" traffade varje versalt LO inuti ett annat ord.
NORDISKA_RE = [re.compile(r"(?<![A-Za-z0-9])%s" % re.escape(n)) for n in NORDISKA]

# Landsord raknas bara om de star i RUBRIKEN — i brodtexten forekommer de
# alltfor ofta i jamforelser.
LANDSORD_RUBRIK = ["Sverige", "svensk", "Norge", "norsk", "Danmark", "dansk",
                   "Finland", "finsk", "Island", "Norden", "nordisk"]

GROUP_RE = re.compile(
    r'(<div class="news-date-group"[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*>)(.*?)'
    r'(?=<div class="news-date-group"|\Z)', re.S)
CARD_OPEN_RE = re.compile(r'<div class="news-card" data-tags="([^"]*)">')
H3_RE = re.compile(r"<h3>\s*<a[^>]*>(.*?)</a>\s*</h3>", re.S)
P_RE = re.compile(r"<p>(.*?)</p>", re.S)
TAG_STRIP = re.compile(r"<[^>]+>")


def plain(fragment):
    return html.unescape(TAG_STRIP.sub("", fragment)).replace("\xa0", " ").strip()


def split_cards(body):
    """-> lista av (start, slut, tags) for varje news-card i dagsblocket."""
    out = []
    for m in CARD_OPEN_RE.finditer(body):
        out.append(m)
    return out


def card_text(body, matches, i):
    start = matches[i].end()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
    return body[start:end]


def is_nordic(title_html, first_p_html):
    """Rubrik + forsta stycket. 'For Norden'-stycket laser vi ALDRIG."""
    title = title_html
    hits = []
    for name, rx in zip(NORDISKA, NORDISKA_RE):
        if rx.search(title) or rx.search(first_p_html):
            hits.append(name)
    title_plain = plain(title)
    for w in LANDSORD_RUBRIK:
        if re.search(r"\b%s" % re.escape(w), title_plain, re.I):
            hits.append("rubrik:%s" % w)
    return hits


def scan(repo):
    path = os.path.join(repo, SV)
    with open(path, encoding="utf-8") as fh:
        doc = fh.read()
    found = []
    for _open, date, body in GROUP_RE.findall(doc):
        ms = split_cards(body)
        for i, m in enumerate(ms):
            inner = card_text(body, ms, i)
            h3 = H3_RE.search(inner)
            ps = P_RE.findall(inner)
            if not h3 or not ps:
                continue
            hits = is_nordic(h3.group(1), ps[0])
            if hits:
                found.append({"date": date, "index": i, "tags": m.group(1),
                              "title": plain(h3.group(1)), "hits": sorted(set(hits))})
    return found


def write_tags(repo, wanted, undanta):
    """Satter norden-taggen pa (datum, index) i alla 6 filer. Idempotent."""
    keys = {(f["date"], f["index"]) for f in wanted
            if "%s#%d" % (f["date"], f["index"]) not in undanta}
    total = 0
    for lang, rels in FILES.items():
        for rel in rels:
            path = os.path.join(repo, rel)
            with open(path, encoding="utf-8") as fh:
                doc = fh.read()
            out, pos, n = [], 0, 0
            for gm in GROUP_RE.finditer(doc):
                date = gm.group(2)
                body = gm.group(3)
                ms = split_cards(body)
                body_out, bpos = [], 0
                for i, m in enumerate(ms):
                    if (date, i) not in keys:
                        continue
                    tags = m.group(1).split()
                    if "norden" in tags:
                        continue
                    tags.append("norden")
                    body_out.append(body[bpos:m.start()])
                    body_out.append('<div class="news-card" data-tags="%s">' % " ".join(tags))
                    bpos = m.end()
                    n += 1
                if body_out:
                    body_out.append(body[bpos:])
                    out.append(doc[pos:gm.start(3)])
                    out.append("".join(body_out))
                    pos = gm.end(3)
            if out:
                out.append(doc[pos:])
                new = "".join(out)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new)
            print("%-24s +%d norden-taggar (totalt %d i filen)"
                  % (rel, n, open(path, encoding="utf-8").read().count("norden")))
            total += n
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--rapport", action="store_true")
    ap.add_argument("--skriv", action="store_true")
    ap.add_argument("--undanta", default="", help="komma-separerad lista med DATUM#INDEX")
    args = ap.parse_args()

    found = scan(args.repo)
    undanta = {s.strip() for s in args.undanta.split(",") if s.strip()}
    if args.rapport or not args.skriv:
        for f in found:
            mark = "  " if "%s#%d" % (f["date"], f["index"]) not in undanta else "X "
            print("%s%s#%d [%s] %s\n      -> %s"
                  % (mark, f["date"], f["index"], f["tags"], f["title"][:110],
                     ", ".join(f["hits"][:6])))
        print("\n%d traffar (%d undantagna)" % (len(found), len(undanta)))
    if args.skriv:
        n = write_tags(args.repo, found, undanta)
        print("skrev %d taggar" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())

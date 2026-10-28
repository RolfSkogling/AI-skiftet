#!/usr/bin/env python3
"""
frontlabb_tackning.py — mäter hur stor andel av frontlabbens egna släpp
som faktiskt nådde ai-skiftet.se:s nyhetsarkiv.

Bakgrund. Den 27 oktober 2026 annonserade Google DeepMind världsmodellen
Genie 4 kl 16:01 UTC. Körningen elva timmar senare missade den. Orsaken var
inte frågans form utan dess LÄGE: samma söksträng gav noll träffar i
standardläge och nio i extended. Arkivsvepet visade samtidigt att
deepmind.google förekom som källa i 1 av 165 dagsgrupper, och att
frontmodell-vaktens `site:deepmind.google/discover` pekade på en sökväg
DeepMind inte använder — 193 av 193 länkar i deras flöde ligger under /blog/.

Det här skriptet är mätpunkten för den åtgärden. Kör det före och efter en
ändring i STEG 1. En åtgärd utan mätpunkt är en gissning.

Användning:
    python3 tools/matning/frontlabb_tackning.py
    python3 tools/matning/frontlabb_tackning.py --fran 2026-09-01 --slapp 4
    python3 tools/matning/frontlabb_tackning.py --json > matning.json

Exitkod:
    0  alla flöden svarade och mätningen gick igenom
    2  minst ett flöde föll (404, nätfel, trasig XML) — FÄLLER MED FLIT.
       Ett dött flöde som passerar tyst är precis den tysta lucka
       mätningen finns för att stänga.
"""

import argparse
import datetime as dt
import gzip
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

REPO = "RolfSkogling/AI-skiftet"
ARKIV = "nyheter/index.html"

# Flöden verifierade 2026-10-28 genom hämtning och posträkning, inte genom
# att adressen såg rimlig ut. Antalet i kommentaren är vad som räknades då.
#
# Adresserna är de SLUTLIGA, efter omdirigering. Tre av dem stod till och med
# 2026-10-28 i sin pre-omdirigeringsform (deepmind.google/blog/feed,
# mistral.ai/rss.xml, blog.google/technology/ai/rss/) och svarade då 302, 301
# och 301 med tom kropp på en vanlig curl UTAN -L. Det här skriptet märkte
# inget, eftersom urllib följer omdirigeringar av sig själv — men skillens
# föreskrivna curl-rad gjorde det inte, och den läste tre av fyra flöden som
# tomma. Håll därför adresserna här identiska med tabellen i LED 0 i
# ai-skiftet-nyheter: när de glider isär är det instrumentet som ljuger.
FLODEN = {
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",                    # 100 poster
    "OpenAI":          "https://openai.com/news/rss.xml",                         # 1331 poster
    "Mistral":         "https://mistral.ai/news/rss",                             # 92 poster
    "Google AI-blogg": "https://blog.google/innovation-and-ai/technology/ai/rss/",# 20 poster
}

# Labb UTAN användbart flöde per 2026-10-28. Alla kandidatadresser nedan
# provades och gav 404, 403 eller trasig XML. De här labben kan därför inte
# bevakas med uppräkning och MÅSTE ligga kvar på sökning i extended-läge
# med datum i klartext. Ändra inte listan utan att köra --prova-doda först.
UTAN_FLODE = {
    "Anthropic": ["https://www.anthropic.com/news/rss.xml", "https://www.anthropic.com/rss",
                  "https://www.anthropic.com/feed.xml", "https://www.anthropic.com/news/feed.xml",
                  "https://anthropic.com/rss.xml", "https://www.anthropic.com/index.xml"],
    "Meta AI":   ["https://ai.meta.com/blog/rss.xml", "https://ai.meta.com/blog/feed.xml",
                  "https://ai.meta.com/feed/"],
    "xAI":       ["https://x.ai/rss.xml", "https://x.ai/news/rss.xml"],
    "DeepSeek":  ["https://api-docs.deepseek.com/rss.xml"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (ai-skiftet frontlabb-tackning)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    "Accept-Encoding": "gzip",
}

STOPP = {
    "the", "a", "an", "and", "or", "for", "with", "our", "new", "to", "of", "in", "on", "at",
    "is", "are", "we", "you", "your", "its", "it", "from", "by", "now", "more", "most", "that",
    "this", "how", "what", "why", "can", "will", "into", "about", "introducing", "announcing",
    "building", "making", "using", "help", "helps", "beyond", "towards", "generation", "model",
    "models", "google", "deepmind", "openai", "anthropic", "mistral", "meta",
}


def hamta(url, timeout=25):
    """Returnerar (status, bytes). Hanterar gzip — utan det blir XML:en binärsörja."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as f:
            data = f.read()
            if f.headers.get("Content-Encoding") == "gzip":
                data = gzip.decompress(data)
            return f.getcode(), data
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return f"FEL:{type(e).__name__}", b""


def las_token():
    """Samma fallback-kedja som ai-skiftet-nyheter-skillen. Token skrivs aldrig ut."""
    for p in (os.path.expanduser("~/AI/.secrets/.github-token"),
              os.path.expanduser("~/Documents/AI-skiftet/.github-token")):
        try:
            with open(p) as f:
                t = f.read().strip()
                if t:
                    return t
        except OSError:
            pass
    try:
        t = subprocess.run(
            ["security", "find-generic-password", "-a", "rolfskogling",
             "-s", "ai-skiftet-github-token", "-w"],
            capture_output=True, text=True, timeout=10).stdout.strip()
        if t:
            return t
    except Exception:
        pass
    return os.environ.get("GITHUB_TOKEN", "").strip()


def hamta_arkiv(token):
    url = f"https://api.github.com/repos/{REPO}/contents/{ARKIV}?ref=main"
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github.raw")
    with urllib.request.urlopen(req, timeout=60) as f:
        return f.read().decode("utf-8")


def dela_dagsgrupper(html):
    delar = re.split(r'data-date="(\d{4}-\d{2}-\d{2})"', html)
    return dict(zip(delar[1::2], delar[2::2]))


def parsa_datum(txt):
    m = re.match(r"\w+,\s*(\d+)\s+(\w{3})\w*\s+(\d{4})", (txt or "").strip())
    if not m:
        return None
    mn = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
          "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}.get(m.group(2))
    if not mn:
        return None
    return dt.date(int(m.group(3)), mn, int(m.group(1)))


def flodesposter(url):
    """(poster, fel). poster = lista av (datum, rubrik, länk)."""
    status, body = hamta(url)
    if status != 200 or not body:
        return [], f"status {status}"
    try:
        rot = ET.fromstring(body)
    except ET.ParseError as e:
        return [], f"trasig XML ({e.__class__.__name__})"
    ut = []
    for it in rot.findall(".//item"):
        d = parsa_datum(it.findtext("pubDate"))
        if d:
            ut.append((d, (it.findtext("title") or "").strip(),
                       (it.findtext("link") or "").strip()))
    ns = "{http://www.w3.org/2005/Atom}"
    for it in rot.findall(f".//{ns}entry"):
        raw = it.findtext(f"{ns}updated") or it.findtext(f"{ns}published") or ""
        try:
            d = dt.date.fromisoformat(raw[:10])
        except ValueError:
            continue
        lnk = it.find(f"{ns}link")
        ut.append((d, (it.findtext(f"{ns}title") or "").strip(),
                   (lnk.get("href") if lnk is not None else "")))
    if not ut:
        return [], "noll daterade poster"
    return ut, None


def termer(rubrik):
    ord_ = re.findall(r"[A-Za-z0-9][A-Za-z0-9.\-]{2,}", rubrik)
    return [w for w in ord_ if w.lower() not in STOPP][:4]


# --- Släppklassificering -----------------------------------------------------
# Frontmodell-vaktens regel gäller "ny modell, ny version eller större
# capability-uppgradering" — INTE kundcase, policyinlägg, konferenser eller
# partnerskap. Utan det här filtret mäter skriptet fel sak och rapporterar
# rött för alltid: en obetald mätpunkt som ingen till slut tittar på.
#
# Filtret är medvetet KONSERVATIVT. Hellre klassa ett släpp som icke-släpp
# än tvärtom: ett falskt larm urholkar mätningen snabbare än ett missat fall,
# eftersom ett missat fall ändå syns i totalsiffran under --alla.

VERSION = re.compile(r"\b[A-Z][A-Za-z]*(?:[ \-][A-Z][A-Za-z]*)?\s\d+(?:\.\d+)?\b")
SLAPPVERB = re.compile(
    r"^(introducing|announcing|meet|launching)\b"
    r"|\b(a new generation|new frontier|research preview|now generally available"
    r"|open weights|general availability|we(?:'| a)re announcing)\b", re.I)
# Kundcase och liknande: någon annan som ANVÄNDER modellen, inte ett släpp.
KUNDCASE = re.compile(
    r"\b(uses|used|helps?|helping|built|builds|turns?|cut|cuts|increases?|reviewed"
    r"|accelerates?|trusts?|scal(?:es|ing)|partner(?:s|ship)?|joins?|expands?"
    r"|supporting|support for customers)\b", re.I)
EJ_SLAPP = re.compile(
    r"\b(policy|board|grants?|funding|journalism|DevFest|XPRIZE|economy|conference"
    r"|summit|hiring|careers|anniversary|celebrat|roundup|the latest ai news)\b", re.I)


def ar_slapp(rubrik):
    """True om rubriken ser ut som ett modell- eller capability-släpp."""
    if EJ_SLAPP.search(rubrik):
        return False
    if KUNDCASE.search(rubrik):
        return False
    return bool(VERSION.search(rubrik) or SLAPPVERB.search(rubrik))


def tackt(dagar, datum, rubrik, lank, slapp):
    """Letar träff i dagsgrupperna [datum, datum+slapp].
    Stark träff = arkivet citerar flödets egen länk. Svag = minst två
    distinkta termer ur rubriken i samma dagsgrupp."""
    t = [w.lower() for w in termer(rubrik)]
    bas = re.sub(r"^https?://", "", lank).rstrip("/") if lank else None
    for off in range(slapp + 1):
        d = (datum + dt.timedelta(days=off)).isoformat()
        kropp = dagar.get(d)
        if not kropp:
            continue
        lag = kropp.lower()
        if bas and bas.lower() in lag:
            return d, "stark"
        if sum(1 for w in t if w in lag) >= 2:
            return d, "svag"
    return None, None


def main():
    ap = argparse.ArgumentParser(description="Täckningsmätning frontlabb -> ai-skiftet-arkivet")
    ap.add_argument("--fran", default="2026-09-01", help="startdatum YYYY-MM-DD")
    ap.add_argument("--till", default=None, help="slutdatum YYYY-MM-DD (standard: i dag)")
    ap.add_argument("--slapp", type=int, default=4, help="dagars slack efter publicering")
    ap.add_argument("--json", action="store_true", help="skriv maskinläsbart utfall")
    ap.add_argument("--alla", action="store_true",
                    help="visa även poster som inte klassats som släpp (markeras med ·)")
    ap.add_argument("--prova-doda", action="store_true",
                    help="provar även adresserna i UTAN_FLODE och rapporterar om något börjat svara")
    a = ap.parse_args()

    fran = dt.date.fromisoformat(a.fran)
    till = dt.date.fromisoformat(a.till) if a.till else dt.date.today()

    token = las_token()
    if not token:
        print("TOKEN SAKNAS — kan inte hämta arkivet. Skapa ~/AI/.secrets/.github-token.",
              file=sys.stderr)
        return 2

    dagar = dela_dagsgrupper(hamta_arkiv(token))

    fel = []
    resultat = {}
    for labb, url in FLODEN.items():
        poster, f = flodesposter(url)
        if f:
            fel.append(f"{labb}: {url} — {f}")
            resultat[labb] = {"fel": f, "url": url}
            continue
        fonster = sorted([p for p in poster if fran <= p[0] <= till], reverse=True)
        rader = []
        for d, rubrik, lank in fonster:
            traff, styrka = tackt(dagar, d, rubrik, lank, a.slapp)
            rader.append({"datum": d.isoformat(), "rubrik": rubrik, "lank": lank,
                          "arkivdag": traff, "styrka": styrka,
                          "slapp": ar_slapp(rubrik)})
        sl = [r for r in rader if r["slapp"]]
        resultat[labb] = {
            "url": url,
            "poster_i_fonstret": len(rader),
            "slapp_i_fonstret": len(sl),
            "tackta": sum(1 for r in sl if r["arkivdag"]),
            "missade": sum(1 for r in sl if not r["arkivdag"]),
            "tackta_alla": sum(1 for r in rader if r["arkivdag"]),
            "poster": rader,
        }

    if a.prova_doda:
        for labb, urls in UTAN_FLODE.items():
            levande = [u for u in urls if flodesposter(u)[0]]
            if levande:
                print(f"NYTT FLÖDE TILLGÄNGLIGT — {labb}: {levande}")

    if a.json:
        print(json.dumps({"fran": a.fran, "till": till.isoformat(), "slapp": a.slapp,
                          "dagsgrupper_i_arkivet": len(dagar),
                          "resultat": resultat, "fel": fel},
                         ensure_ascii=False, indent=2))
        return 2 if fel else 0

    print(f"TÄCKNINGSMÄTNING  {a.fran} .. {till.isoformat()}   "
          f"slack {a.slapp} dgr   arkivet: {len(dagar)} dagsgrupper")
    print("Räknat: poster klassade som modell-/capability-släpp. "
          "--alla visar även kundcase, policy och event.")
    print("=" * 78)
    tot_t = tot_m = 0
    tot_alla = tot_alla_t = 0
    for labb, r in resultat.items():
        if "fel" in r:
            print(f"\n{labb}: FLÖDET FÖLL — {r['fel']}  ({r['url']})")
            continue
        n = r["slapp_i_fonstret"]
        kvot = f"{r['tackta']}/{n}" if n else "0/0"
        print(f"\n{labb}  —  {kvot} täckta släpp   "
              f"({r['poster_i_fonstret']} poster totalt i flödet)")
        for p in r["poster"]:
            if not (p["slapp"] or a.alla):
                continue
            mark = f"-> {p['arkivdag']} ({p['styrka']})" if p["arkivdag"] else "-> MISSAD"
            flagga = " " if p["slapp"] else "·"
            print(f" {flagga} {p['datum']}  {p['rubrik'][:52]:<52} {mark}")
        tot_t += r["tackta"]
        tot_m += r["missade"]
        tot_alla += r["poster_i_fonstret"]
        tot_alla_t += r["tackta_alla"]
    print("\n" + "=" * 78)
    tot = tot_t + tot_m
    andel = f"{100 * tot_t / tot:.0f}%" if tot else "–"
    print(f"SLÄPP:      {tot_t} täckta, {tot_m} missade av {tot}  ({andel})   <- mätpunkten")
    andel2 = f"{100 * tot_alla_t / tot_alla:.0f}%" if tot_alla else "–"
    print(f"Alla poster: {tot_alla_t} täckta av {tot_alla}  ({andel2})   "
          f"(referens — inte vad regeln kräver)")
    print(f"Labb utan flöde (måste ligga kvar på sökning): {', '.join(UTAN_FLODE)}")
    if fel:
        print("\nFÄLLER — flöden som inte svarade:")
        for f in fel:
            print("  " + f)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

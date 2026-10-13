#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publiceringskontroll for ai-skiftet.se - matter SIDANS TILLSTAND, inte bokforingen.

Fallerar (exit 1) nar en essa ar LANKAD fran biblioteket eller forstasidan
samtidigt som den publicerade essafilen SAKNAR ett spelbart ljudkort.

Kontrollen drar aldrig sin slutsats ur commit-loggar, ur exitkoder fran tidigare
steg eller ur lokal bokforing. Den laser filernas faktiska innehall och
ingenting annat. Det ar hela poangen med den.

Bakgrund, matt 2026-10-13: essan "Sa mycket, sa fort" publicerades i tre
sprakversioner 10:33:50-10:33:57 UTAN ljudkortet i filen. Bibliotek och
forstasidor lankade essan 10:34:00-10:34:14. Ljudkortet lades in forst
10:38:07-10:38:11, i separata commits. Under fyra minuter lag essan alltsa
lankad fran forstasidan utan spelare, och eftersom GitHub Pages serverar HTML
med cache-control: max-age=600 kunde en lasare fa den spelarlosa versionen i
upp till tio minuter till. Korningen rapporterade gront darfor att varje commit
lyckades - den matte sin egen bokforing, inte sidans tillstand.

Anvandning:
    python3 tools/publiceringskontroll/check_ljudkort.py --slug sa-mycket-sa-fort
    python3 tools/publiceringskontroll/check_ljudkort.py                 # svep alla
    python3 tools/publiceringskontroll/check_ljudkort.py --local .       # forkontroll
    python3 tools/publiceringskontroll/check_ljudkort.py --local . --slug sa-mycket-sa-fort
    python3 tools/publiceringskontroll/check_ljudkort.py --json

Exitkoder:
    0  ingen rad fallde, ingen rad ar overifierad
    1  minst en rad FALLD - en lankad essa utan spelbart ljudkort
    2  KONTROLLFEL - en sida gick inte att hamta, en sprakvaxlarlank gick inte
       att folja, ett ovantat svar. Ett kontrollfel ar INTE ett godkannande.

Bara standardbiblioteket. Ingen token, ingen autentisering, inga
tredjepartspaket. Python 3.9+.
"""
import argparse
import itertools
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

LIVE_BAS = "https://ai-skiftet.se"
EGNA_VARDAR = ("ai-skiftet.se", "www.ai-skiftet.se", "rot", "")
SPRAK = ("sv", "en", "no")
BIBLIOTEK = {"sv": "essaer.html", "en": "en/essays.html", "no": "no/essays.html"}
FORSTASIDA = {"sv": "index.html", "en": "en/index.html", "no": "no/index.html"}
# Biblioteket markerar varje essa med <a class="essay-card" href="...">. Det ar
# den markeringen svepet foljer - inte en hardkodad lista. En hardkodad lista
# vaxer inte med sajten, och det var precis sa essasidorna undslapp
# sprakkontrollens live-lage till 2026-09-02.
ESSAKORT = "essay-card"
LJUDTYPER = (".m4a", ".mp3", ".mp4", ".m4b", ".aac", ".ogg", ".oga", ".opus",
             ".wav", ".flac", ".webm")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
# Balanserad taggrakning, inte en regexgenvag: attributvarden far innehalla >
# sa lange de ar citerade.
TAGG = re.compile(r"<(/?)([a-zA-Z][\w:.-]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*?)(/?)>")


class Kontrollfel(Exception):
    """Kontrollen kunde inte mata det den skulle mata. Aldrig ett godkannande."""


# ---------------------------------------------------------------- HTML-parsning

def attribut(taggtext, namn):
    """Vardet av ett attribut i en starttagg, eller None."""
    m = re.search(r"\b%s\s*=\s*\"([^\"]*)\"" % re.escape(namn), taggtext, re.I)
    if m:
        return m.group(1)
    m = re.search(r"\b%s\s*=\s*'([^']*)'" % re.escape(namn), taggtext, re.I)
    if m:
        return m.group(1)
    m = re.search(r"\b%s\s*=\s*([^\s>]+)" % re.escape(namn), taggtext, re.I)
    return m.group(1) if m else None


def klasser(taggtext):
    """Klassattributet som en mangd. Exakta tokens, inte delstrangar.

    Skillnaden ar inte kosmetisk: en delstrangsokning pa "news-audio" traffar
    aven class="news-audio__row" och class="news-audio__player", och da kan ett
    tomt kort med bara en rubrikrad rapporteras som ett komplett ljudkort.
    """
    varde = attribut(taggtext, "class") or ""
    return set(varde.split())


def element(text, villkor, flera=False):
    """Generera (helt, innehall, starttagg) for element dar villkor(namn, attr).

    Balanserad rakning av samnamniga taggar. Self-closing och void-element
    raknas aldrig upp djupet - annars skulle en <source> inuti <audio> gora
    att elementet aldrig ansags stanga.
    """
    pos = 0
    while True:
        start = None
        for kandidat in TAGG.finditer(text, pos):
            if kandidat.group(1):
                continue
            if villkor(kandidat.group(2).lower(), kandidat.group(0)):
                start = kandidat
                break
        if start is None:
            return
        namn = start.group(2).lower()
        if start.group(4) or namn in VOID:
            yield start.group(0), "", start.group(0)
            pos = start.end()
        else:
            slut, djup = None, 1
            for n in TAGG.finditer(text, start.end()):
                if n.group(2).lower() != namn:
                    continue
                if n.group(1):
                    djup -= 1
                    if djup == 0:
                        slut = n
                        break
                elif not (n.group(4) or namn in VOID):
                    djup += 1
            if slut is None:
                # Oavslutat element. Lamna resten av dokumentet som innehall sa
                # att ett trasigt kort diagnostiseras i stallet for att forsvinna.
                yield text[start.start():], text[start.end():], start.group(0)
                return
            yield text[start.start():slut.end()], text[start.end():slut.start()], start.group(0)
            pos = slut.end()
        if not flera:
            return


def forsta(text, villkor):
    return next(element(text, villkor), (None, None, None))


def tysta_kod(text):
    """Blanka script, style och kommentarer.

    En utkommenterad ljudkortsmall ar INTE en publicerad spelare. Utan den har
    rensningen skulle <!-- <div class="news-audio"> ... --> ge gront.
    """
    for monster in (r"<script\b.*?</script>", r"<style\b.*?</style>", r"<!--.*?-->"):
        text = re.sub(monster, lambda m: "\n" * m.group(0).count("\n"), text,
                      flags=re.S | re.I)
    return text


def alla_href(text):
    return (re.findall(r"href\s*=\s*\"([^\"]*)\"", text, re.I)
            + re.findall(r"href\s*=\s*'([^']*)'", text, re.I))


def rotrelativ(sid_rel, href):
    """Los en href mot sidans plats. Returnerar rotrelativ sokvag utan /.

    None for externa lankar, mailto, javascript, data och tomma hrefar.
    """
    href = (href or "").strip()
    if not href or href.startswith("#"):
        return None
    bas = "http://rot/" + sid_rel.lstrip("/")
    try:
        delar = urllib.parse.urlsplit(urllib.parse.urljoin(bas, href))
    except ValueError:
        return None
    if delar.scheme not in ("http", "https", ""):
        return None
    if delar.netloc.lower() not in EGNA_VARDAR:
        return None
    return delar.path.lstrip("/")


# -------------------------------------------------------------------- hamtning

_LOPNUMMER = itertools.count(1)


def unik_url(url):
    """Lagg pa en cache-bustare som ar unik for varje enskild hamtning.

    Nanosekundsklocka + pid + lopnummer. Varken Fastly, GitHub Pages eller en
    mellanliggande proxy kan svara pa den har URL:en med nagot aldre, eftersom
    den aldrig har efterfragats forut. Utan den matte kontrollen cachen i
    stallet for sidan - och HTML:en pa ai-skiftet.se serveras med
    cache-control: max-age=600.
    """
    stampel = "%d.%d.%d" % (time.time_ns(), os.getpid(), next(_LOPNUMMER))
    return "%s%skontroll=%s" % (url, "&" if "?" in url else "?", stampel)


def hamta(url, metod="GET", intervall=None, timeout=30):
    """HTTP-hamtning. Returnerar alltid ett matvarde, aven for 404 och 500.

    Ett HTTP-fel ar en MATNING (ljudfilen svarar 404) och ska kunna falla en
    rad med egen forklaring. Bara nar svaret inte gar att fa alls - DNS, TLS,
    timeout - blir det ett kontrollfel.
    """
    matt = unik_url(url)
    beg = urllib.request.Request(matt, method=metod)
    beg.add_header("Cache-Control", "no-cache, no-store, max-age=0")
    beg.add_header("Pragma", "no-cache")
    beg.add_header("User-Agent", "aiskiftet-publiceringskontroll/1 (stdlib urllib)")
    if intervall:
        beg.add_header("Range", intervall)
    try:
        with urllib.request.urlopen(beg, timeout=timeout) as svar:
            kropp, huvuden, status = svar.read(), svar.headers, svar.status
    except urllib.error.HTTPError as fel:
        kropp, huvuden, status = b"", (fel.headers or {}), fel.code
    except Exception as fel:                      # URLError, timeout, TLS, DNS
        raise Kontrollfel("%s gick inte att hamta: %s" % (url, fel))
    return {"url": matt, "visad": url, "status": status,
            "etag": huvuden.get("ETag") or "(ingen)",
            "lm": huvuden.get("Last-Modified") or "(ingen)",
            "text": kropp.decode("utf-8", "replace"), "byte": len(kropp)}


class Kalla:
    """Live-sajten eller en lokal repo-rot bakom samma granssnitt.

    Lagena skiljer sig i EN sak: live mater HTTP-status och range-stod pa
    ljudfilen, lokalt mater existens och storlek pa disk. Allt annat - vad som
    raknas som ett ljudkort, vad som raknas som lankat - ar identiskt, sa
    forkontrollen och live-kontrollen inte kan ge olika svar pa samma fil.
    """

    def __init__(self, rot=None, bas=LIVE_BAS, timeout=30):
        self.live = rot is None
        self.bas = bas.rstrip("/")
        self.rot = os.path.abspath(rot) if rot else None
        self.timeout = timeout
        self._delade = {}
        self.bevis = []

    def beskrivning(self):
        return "live (%s)" % self.bas if self.live else "local (%s)" % self.rot

    def ref(self, rel):
        rel = rel.lstrip("/")
        if self.live:
            return "%s/%s" % (self.bas, rel)
        return os.path.join(self.rot, *rel.split("/"))

    def sida(self, rel):
        """HTML-sida. Allt annat an ett lasbart 200-svar ar ett kontrollfel."""
        if self.live:
            m = hamta(self.ref(rel), timeout=self.timeout)
            if m["status"] != 200:
                raise Kontrollfel("%s svarade HTTP %d, forvantat 200"
                                  % (m["visad"], m["status"]))
            if not m["text"].strip():
                raise Kontrollfel("%s svarade 200 men tomt" % m["visad"])
            return m
        sokvag = self.ref(rel)
        if not os.path.isfile(sokvag):
            raise Kontrollfel("filen finns inte: %s" % sokvag)
        with open(sokvag, encoding="utf-8", errors="replace") as f:
            text = f.read()
        if not text.strip():
            raise Kontrollfel("filen ar tom: %s" % sokvag)
        st = os.stat(sokvag)
        return {"url": sokvag, "visad": sokvag, "status": 200, "text": text,
                "byte": st.st_size, "etag": "(lokal fil, %d byte)" % st.st_size,
                "lm": time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                    time.gmtime(st.st_mtime))}

    def delad_sida(self, rel):
        """Bibliotek och forstasidor hamtas en gang per korning och ateranvands.

        Det ar ingen cache i den mening kontrollen forbjuder: sidan hamtas med
        en unik cache-bustare i samma matogonblick som allt annat. Alternativet
        - att hamta essaer.html 50 ganger i ett svep - mater inte nagot mer.
        """
        if rel not in self._delade:
            try:
                m = self.sida(rel)
                self._delade[rel] = m
                self.bevis.append((rel, m["visad"], m["etag"], m["lm"], m["byte"]))
            except Kontrollfel as fel:
                self._delade[rel] = fel
        varde = self._delade[rel]
        if isinstance(varde, Kontrollfel):
            raise varde
        return varde

    def mat_ljudkalla(self, src, essa_rel):
        """Mat ljudfilen bakom <source src>. Returnerar (ok, forklaring, url)."""
        sokvag = rotrelativ(essa_rel, src)
        if sokvag is None:
            return False, "ljudkallan pekar utanfor sajten: %s" % src, src
        if self.live:
            url = "%s/%s" % (self.bas, sokvag)
            fraga = urllib.parse.urlsplit(urllib.parse.urljoin(
                "http://rot/" + essa_rel.lstrip("/"), src)).query
            if fraga:
                url = "%s?%s" % (url, fraga)
            huvud = hamta(url, metod="HEAD", timeout=self.timeout)
            if huvud["status"] in (405, 501):     # HEAD nekat: mat med GET
                huvud = hamta(url, intervall="bytes=0-0", timeout=self.timeout)
                if huvud["status"] not in (200, 206):
                    return False, "ljudfilen svarar HTTP %d" % huvud["status"], url
            elif huvud["status"] != 200:
                return False, "ljudfilen svarar HTTP %d" % huvud["status"], url
            bit = hamta(url, intervall="bytes=0-1023", timeout=self.timeout)
            if bit["status"] != 206:
                return (False,
                        "ljudfilen svarar HTTP %d pa range-request, forvantat 206 "
                        "- spelaren kan inte spola i den" % bit["status"], url)
            return True, "200 och range 206 (%d byte i provet)" % bit["byte"], url
        filsokvag = self.ref(sokvag)
        if not os.path.isfile(filsokvag):
            return False, "ljudfilen finns inte pa disk", filsokvag
        storlek = os.path.getsize(filsokvag)
        if storlek == 0:
            return False, "ljudfilen ar 0 byte", filsokvag
        return True, "finns pa disk (%d byte)" % storlek, filsokvag


# ------------------------------------------------------------------- ljudkortet

def ser_ut_som_ljud(src):
    bana = urllib.parse.urlsplit(src).path.lower()
    return bana.endswith(LJUDTYPER)


def granska_ljudkort(text):
    """Las ljudkortet ur essafilens faktiska innehall.

    lage: "helt"   - news-audio + <audio> + <source src> mot en ljudfil
          "delvis" - nagot finns, nagot saknas. FALLER med egen forklaring.
                     Ett halvt kort ar inget kort, och far aldrig tyst passera.
          "saknas" - inget element med class="news-audio" alls
    Flera kort provas, och det mest kompletta vinner - en sida med tva kort dar
    det ena ar trasigt ska inte falla pa det trasiga om det finns ett helt.
    """
    ren = tysta_kod(text)
    kort = list(element(ren, lambda n, t: "news-audio" in klasser(t), flera=True))
    if not kort:
        return {"lage": "saknas", "src": None,
                "skal": "inget element med class=\"news-audio\" i filen"}
    utfall = []
    for _helt, inne, _start in kort:
        _a_helt, a_inne, _a_start = forsta(inne, lambda n, t: n == "audio")
        if a_inne is None:
            utfall.append({"lage": "delvis", "src": None, "rang": 1,
                           "skal": "ljudkortet har inget <audio>-element inuti"})
            continue
        _s_helt, _s_inne, s_start = forsta(a_inne, lambda n, t: n == "source")
        if s_start is None:
            utfall.append({"lage": "delvis", "src": None, "rang": 2,
                           "skal": "<audio>-elementet har ingen <source> inuti"})
            continue
        src = (attribut(s_start, "src") or "").strip()
        if not src:
            utfall.append({"lage": "delvis", "src": None, "rang": 3,
                           "skal": "<source> utan src-attribut"})
            continue
        if not ser_ut_som_ljud(src):
            utfall.append({"lage": "delvis", "src": src, "rang": 3,
                           "skal": "<source src=\"%s\"> pekar inte pa en ljudfil" % src})
            continue
        utfall.append({"lage": "helt", "src": src, "rang": 4, "skal": ""})
    basta = max(utfall, key=lambda u: u["rang"])
    basta.pop("rang", None)
    return basta


def sprakvaxlarlankar(essatext, sv_rel):
    """en- och no-sokvagarna, lasta ur sprakvaxlaren i den svenska filen.

    Slugen antas ALDRIG vara densamma pa alla tre sprak. Den engelska versionen
    av "Sa mycket, sa fort" ligger pa samma slug, men globala-scenarier.html
    heter global-scenarios.html pa engelska och globale-scenarioer.html pa
    norska. Hittas ingen lank blir sprakraden OVERIFIERAD - aldrig gissad.
    """
    _helt, inne, _start = forsta(essatext, lambda n, t: "lang-switcher" in klasser(t))
    if inne is None:
        return {}, "ingen sprakvaxlare (class=\"lang-switcher\") i filen"
    hittade = {}
    for m in re.finditer(r"<a\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*>", inne, re.I):
        tagg = m.group(0)
        lost = rotrelativ(sv_rel, attribut(tagg, "href"))
        if not lost or not lost.endswith(".html"):
            continue
        katalog = lost.split("/")[0]
        kod = (attribut(tagg, "lang") or "").lower().split("-")[0]
        if kod in ("nb", "nn", "no") or katalog == "no":
            hittade.setdefault("no", lost)
        elif kod == "en" or katalog == "en":
            hittade.setdefault("en", lost)
    saknade = [s for s in ("en", "no") if s not in hittade
               or not hittade[s].startswith(s + "/")]
    for s in saknade:
        hittade.pop(s, None)
    skal = ""
    if saknade:
        skal = "sprakvaxlaren saknar en foljbar lank till %s" % ", ".join(saknade)
    return hittade, skal


def lankad(sidtext, sid_rel, essa_rel):
    """Den matchande hrefen om essafilen lankas fran sidan, annars None.

    Matchar bade pa hela den rotrelativa sokvagen och pa filnamnet, sa att
    bade href="sa-mycket-sa-fort.html" och href="/en/sa-mycket-sa-fort.html"
    raknas. Tvetydigheten faller medvetet mot "lankad": det ar den sidan av
    felet som leder till en fallning, inte till ett tyst godkannande.
    """
    mal = essa_rel.lstrip("/")
    basnamn = mal.rsplit("/", 1)[-1]
    for h in alla_href(sidtext):
        lost = rotrelativ(sid_rel, h.split("#")[0])
        if lost is None:
            continue
        if lost == mal or lost.rsplit("/", 1)[-1] == basnamn:
            return h
    return None


# ----------------------------------------------------------------- bedomningen

def bedom_sprak(kalla, sprak, essa_rel):
    """En rad: utfallet for ett sprak och en essa. Kontrollfel -> OVERIFIERAD.

    Utfallsmatrisen, och ingenting annat:
      lankad + helt spelbart ljudkort        -> OK
      lankad + ljudkort saknas eller trasigt -> FALLD
      ej lankad + ljudkort saknas            -> OK med anmarkning (mellanlaget)
      ej lankad + ljudkort finns             -> OK
    """
    rad = {"sprak": sprak, "fil": essa_rel, "utfall": "OVERIFIERAD",
           "lank": None, "lankkalla": None, "kortlage": "-", "src": None,
           "ljudtext": "-", "ljudurl": None, "matt": kalla.ref(essa_rel),
           "etag": "-", "lm": "-", "skal": "", "anmarkning": ""}
    try:
        sida = kalla.sida(essa_rel)
        bib = kalla.delad_sida(BIBLIOTEK[sprak])
        forsta_sidan = kalla.delad_sida(FORSTASIDA[sprak])
    except Kontrollfel as fel:
        rad["skal"] = str(fel)
        return rad

    rad["matt"], rad["etag"], rad["lm"] = sida["visad"], sida["etag"], sida["lm"]
    rad["_text"] = sida["text"]       # ateranvands av sprakvaxlaren

    traff = lankad(bib["text"], BIBLIOTEK[sprak], essa_rel)
    kalla_namn = BIBLIOTEK[sprak]
    if traff is None:
        traff = lankad(forsta_sidan["text"], FORSTASIDA[sprak], essa_rel)
        kalla_namn = FORSTASIDA[sprak]
    rad["lank"], rad["lankkalla"] = traff, (kalla_namn if traff else None)

    kort = granska_ljudkort(sida["text"])
    rad["kortlage"], rad["src"] = kort["lage"], kort["src"]
    spelbart = kort["lage"] == "helt"
    if spelbart:
        try:
            ok, forklaring, ljudurl = kalla.mat_ljudkalla(kort["src"], essa_rel)
        except Kontrollfel as fel:
            rad["skal"] = "ljudkallan gick inte att mata: %s" % fel
            return rad
        rad["ljudtext"], rad["ljudurl"] = forklaring, ljudurl
        if not ok:
            spelbart = False
            rad["kortlage"] = "trasigt"
            kort["skal"] = forklaring
    else:
        rad["ljudtext"] = "ej matt (inget komplett kort)"

    if traff and spelbart:
        rad["utfall"] = "OK"
    elif traff:
        rad["utfall"] = "FALLD"
        rad["skal"] = ("lankad fran %s via href=\"%s\", men %s"
                       % (kalla_namn, traff, kort["skal"] or rad["ljudtext"]))
    elif spelbart:
        rad["utfall"] = "OK"
        rad["anmarkning"] = "ej lankad an, ljudkortet pa plats"
    else:
        rad["utfall"] = "OK"
        rad["anmarkning"] = ("ej lankad fran %s eller %s - %s. Legitimt mellanlage "
                             "under publicering, men lank den INTE forran kortet "
                             "finns." % (BIBLIOTEK[sprak], FORSTASIDA[sprak],
                                         kort["skal"]))
    return rad


def bedom_essa(kalla, slug):
    """Tre rader - sv, en, no. en/no-sokvagarna lases ur sprakvaxlaren."""
    sv_rel = slug if slug.endswith(".html") else slug + ".html"
    sv_rel = sv_rel.lstrip("/")
    rader = [bedom_sprak(kalla, "sv", sv_rel)]
    if rader[0]["utfall"] == "OVERIFIERAD":
        for sprak in ("en", "no"):
            rader.append({"sprak": sprak, "fil": "(okand)", "utfall": "OVERIFIERAD",
                          "lank": None, "lankkalla": None, "kortlage": "-",
                          "src": None, "ljudtext": "-", "ljudurl": None,
                          "matt": "-", "etag": "-", "lm": "-",
                          "skal": "den svenska filen gick inte att lasa, sa "
                                  "sprakvaxlaren kunde inte foljas",
                          "anmarkning": ""})
        return rader
    sidtext = rader[0]["_text"]
    lankar, brist = sprakvaxlarlankar(sidtext, sv_rel)
    for sprak in ("en", "no"):
        if sprak in lankar:
            rader.append(bedom_sprak(kalla, sprak, lankar[sprak]))
        else:
            rader.append({"sprak": sprak, "fil": "(okand)", "utfall": "OVERIFIERAD",
                          "lank": None, "lankkalla": None, "kortlage": "-",
                          "src": None, "ljudtext": "-", "ljudurl": None,
                          "matt": kalla.ref(sv_rel), "etag": "-", "lm": "-",
                          "skal": brist or "sprakvaxlaren pekar inte pa %s/" % sprak,
                          "anmarkning": ""})
    return rader


def essaslugar(kalla):
    """Slugarna biblioteket lankar som essay-card. Svepets omfang.

    Svepet ar det som hittar GAMLA fel. En kontroll som bara kan provas mot
    dagens slug hade aldrig funnit nagot annat an dagens misstag.
    """
    bib = kalla.delad_sida(BIBLIOTEK["sv"])
    slugar, sedda = [], set()
    for m in re.finditer(r"<a\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*>", bib["text"], re.I):
        if ESSAKORT not in klasser(m.group(0)):
            continue
        lost = rotrelativ(BIBLIOTEK["sv"], (attribut(m.group(0), "href") or "").split("#")[0])
        if not lost or not lost.endswith(".html"):
            continue                 # t.ex. valguiden-2026/ - en katalog, ingen essafil
        # OBS: en href till en .html-fil i en UNDERKATALOG ger har en slug som
        # sedan slas upp i roten och darmed inte hittas. Utfallet blir
        # OVERIFIERAD och exit 2 - alltsa blockering, aldrig tyst gront. Finns
        # sadana essaer i framtiden ska uppslagningen bara med katalogdelen.
        slug = lost.rsplit("/", 1)[-1][:-len(".html")]
        if slug in sedda:
            continue
        sedda.add(slug)
        slugar.append(slug)
    return slugar


# -------------------------------------------------------------------- utskriften

def rad_text(rad):
    """En rad per sprak, med den matta URL:en och bevisen pa samma rad."""
    bitar = ["  %-2s  %-11s" % (rad["sprak"], rad["utfall"]),
             "lankad=%s" % (rad["lankkalla"] or "nej"),
             "ljudkort=%s" % rad["kortlage"],
             "ljud=%s" % rad["ljudtext"],
             "matt=%s" % rad["matt"],
             "etag=%s" % rad["etag"],
             "last-modified=%s" % rad["lm"]]
    if rad["skal"]:
        bitar.append("skal=%s" % rad["skal"])
    elif rad["anmarkning"]:
        bitar.append("anm=%s" % rad["anmarkning"])
    return "  ".join(bitar)


def skriv_rapport(kalla, grupper, strom=sys.stdout):
    fallda, overifierade, ok = [], [], 0
    print("Publiceringskontroll ljudkort - lage: %s" % kalla.beskrivning(), file=strom)
    print("Regel: en essa som ar lankad fran bibliotek eller forstasida maste ha "
          "ett spelbart ljudkort i den publicerade filen.", file=strom)
    print("", file=strom)
    for slug, rader in grupper:
        print("%s" % slug, file=strom)
        for rad in rader:
            print(rad_text(rad), file=strom)
            if rad["utfall"] == "FALLD":
                fallda.append((slug, rad))
            elif rad["utfall"] == "OVERIFIERAD":
                overifierade.append((slug, rad))
            else:
                ok += 1
        print("", file=strom)

    if kalla.bevis:
        print("Bevis - delade listsidor, %s:"
              % ("hamtade en gang per korning med egen cache-bustare"
                 if kalla.live else "lasta fran disk"), file=strom)
        for rel, visad, etag, lm, byte in kalla.bevis:
            print("  %-16s %s  etag=%s  last-modified=%s  %d byte"
                  % (rel, visad, etag, lm, byte), file=strom)
        print("", file=strom)

    if fallda:
        print("FALLDA RADER - PUBLICERA INTE, OCH AVLANKA OM DET REDAN AR "
              "PUBLICERAT:", file=strom)
        for slug, rad in fallda:
            print("  %s [%s]  %s" % (slug, rad["sprak"], rad["fil"]), file=strom)
            print("      matt sida:  %s" % rad["matt"], file=strom)
            if rad["ljudurl"]:
                print("      matt ljud:  %s" % rad["ljudurl"], file=strom)
            print("      skal:       %s" % rad["skal"], file=strom)
        print("", file=strom)

    if overifierade:
        print("OVERIFIERADE RADER - kontrollen kunde inte mata dem. Det ar INTE "
              "ett godkannande:", file=strom)
        for slug, rad in overifierade:
            print("  %s [%s]  %s" % (slug, rad["sprak"], rad["fil"]), file=strom)
            print("      matt:       %s" % rad["matt"], file=strom)
            print("      skal:       %s" % rad["skal"], file=strom)
        print("", file=strom)

    antal = ok + len(fallda) + len(overifierade)
    print("Summa: %d kontrollerade, %d OK, %d fallda, %d overifierade"
          % (antal, ok, len(fallda), len(overifierade)), file=strom)
    return antal, ok, len(fallda), len(overifierade)


def main():
    p = argparse.ArgumentParser(
        description="Publiceringskontroll ai-skiftet.se: ingen lankad essa utan "
                    "spelbart ljudkort. Matter filernas innehall, aldrig "
                    "commit-loggar eller exitkoder fran tidigare steg.")
    p.add_argument("--live", action="store_true",
                   help="hamta fran den publicerade sajten (forval)")
    p.add_argument("--local", metavar="REPO-ROT",
                   help="las filerna fran disk i stallet. Forkontroll fore push.")
    p.add_argument("--slug", action="append", metavar="SLUG",
                   help="prova en essa (sv-slugen). Kan upprepas. Utan --slug "
                        "svepas alla essaer biblioteket lankar.")
    p.add_argument("--bas", default=LIVE_BAS, help="bas-URL i live-lage")
    p.add_argument("--timeout", type=float, default=30, metavar="SEK")
    p.add_argument("--json", action="store_true", help="maskinlasbart")
    args = p.parse_args()

    if args.live and args.local:
        print("KONTROLLFEL: --live och --local utesluter varandra.", file=sys.stderr)
        return 2

    kalla = Kalla(rot=args.local, bas=args.bas, timeout=args.timeout)
    try:
        slugar = [s.strip("/") for s in (args.slug or [])] or essaslugar(kalla)
    except Kontrollfel as fel:
        print("KONTROLLFEL: omfanget kunde inte harledas ur %s: %s"
              % (BIBLIOTEK["sv"], fel), file=sys.stderr)
        return 2

    grupper = [(slug, bedom_essa(kalla, slug)) for slug in slugar]
    for _slug, rader in grupper:
        for rad in rader:
            rad.pop("_text", None)

    if args.json:
        antal = sum(len(r) for _s, r in grupper)
        fallda = [dict(r, slug=s) for s, rader in grupper for r in rader
                  if r["utfall"] == "FALLD"]
        overif = [dict(r, slug=s) for s, rader in grupper for r in rader
                  if r["utfall"] == "OVERIFIERAD"]
        print(json.dumps({"lage": kalla.beskrivning(),
                          "kontrollerade": antal,
                          "ok": antal - len(fallda) - len(overif),
                          "fallda": len(fallda), "overifierade": len(overif),
                          "essaer": [{"slug": s, "rader": r} for s, r in grupper],
                          "bevis": kalla.bevis},
                         ensure_ascii=False, indent=2))
    else:
        antal, _ok, antal_fallda, antal_overif = skriv_rapport(kalla, grupper)
        fallda, overif = [1] * antal_fallda, [1] * antal_overif

    sys.stdout.flush()      # rapporten fore domen, aven i en pipe

    # Tackningsgrind. Noll kontrollerade rader ar inte ett rent resultat - det ar
    # en kontroll som inte last det den ska skydda. Samma lektion som
    # sprakkontrollens --minst (2026-08-24).
    if not grupper:
        print("KONTROLLFEL: noll essaer i omfanget. Kontrollen har inte matt "
              "nagot - publicera INTE.", file=sys.stderr)
        return 2

    if fallda:
        print("FALLER: %d rad(er) ar lankade utan spelbart ljudkort. Ljudkortet "
              "ska in i samma commit som essan, och spelaren ska vara publicerad "
              "fore bibliotek och forstasida." % len(fallda), file=sys.stderr)
        return 1
    if overif:
        print("KONTROLLFEL: %d rad(er) gick inte att mata. Ett kontrollfel ar "
              "inte ett godkannande - atgarda och kor om." % len(overif),
              file=sys.stderr)
        return 2
    print("RENT: alla kontrollerade essarader har antingen spelbart ljudkort "
          "eller ar annu inte lankade.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

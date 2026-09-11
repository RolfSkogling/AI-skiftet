#!/usr/bin/env python3
"""Halla forstasidans "Senast uppdaterat" bundet till sidans egna nyheter.

Bakgrund (2026-09-11): startsideombyggnaden 2026-09-08 (85d104d) la in

    <time datetime="2026-09-08">Senast uppdaterat 8 september 2026</time>

som en hardkodad strang i sect-head. Inget skript skrev den, sa den fros fast
vid ombyggnadsdatumet medan nyheterna rullade vidare. Den 11 september pastod
sidan "8 september" med 10 september overst i listan.

Feltypen: ett falt som pastar nagot om systemets tillstand men mater nagot
annat. Har matte det nar NAGON SENAST RORDE MALLEN, inte nar nyheterna
publicerades. Ett sadant falt blir fel forr eller senare, hur noga man an
fyller i det for hand.

Losningen ar samma som for essay-count: faltet raknar sig sjalvt ur det det
beskriver. Sidan har redan dagens datum i klartext i den oversta dagsgruppens
etikett, pa ratt sprak. Datumfaltet KOPIERAR den strangen i stallet for att
formatera ett eget datum - da finns ingen sprakspecifik datumlogik som kan
glida isar, och ingen siffra att fylla i for hand.

Tre lager, i den ordningen:
  1. HTML-fallbacken i filen (det som visas utan JavaScript) - satts av `fix`.
  2. Ett inline-skript pa sidan som skriver om faltet i webblasaren.
  3. Den har kontrollen, som fallerar om lager 1 glidit isar fran nyheterna.

Kontrollen granskar aven ljudnotisen, men som ETT EGET matvarde: den ska
stamma med ljudfilens ?v=-version, INTE med nyhetsdatumet. Ett ljud som ar tva
dygn gammalt ska sta som tva dygn gammalt - att datera om notisen till dagens
datum vore att dolja ett storre fel bakom ett snyggare falt.

Anvandning:
    updated_date.py check <fil> [...]     exit 1 vid isarglidning
    updated_date.py fix   <fil> [...]     skriver om HTML-fallbacken
    updated_date.py check --live          mot ai-skiftet.se
"""
import re
import sys

LIVE_PAGES = [
    "https://ai-skiftet.se/index.html",
    "https://ai-skiftet.se/en/index.html",
    "https://ai-skiftet.se/no/index.html",
]

# Oversta dagsgruppen + dess synliga etikett.
DAY_GROUP_RE = re.compile(
    r'<div[^>]*\bclass="[^"]*\bnews-date-group\b[^"]*"[^>]*\bdata-date="(\d{4}-\d{2}-\d{2})"[^>]*>\s*'
    r'<p[^>]*\bclass="[^"]*\bnews-date\b[^"]*"[^>]*>(.*?)</p>',
    re.S,
)
TIME_RE = re.compile(
    r'(<time\b[^>]*\bdatetime=")(\d{4}-\d{2}-\d{2})("[^>]*>)(.*?)(</time\s*>)', re.S
)
STATED_DATE_RE = re.compile(
    r'(<span[^>]*\bclass="[^"]*\bsect-updated__date\b[^"]*"[^>]*>)(.*?)(</span>)', re.S
)
AUDIO_SRC_RE = re.compile(r"/audio/dagens\.m4a\?v=(\d{4}-\d{2}-\d{2})")
# Notisen ar en <div> pa de riktiga sidorna, inte en <span>. Forsta versionen
# av den har raden lette bara efter <span> och matchade darfor ALDRIG i
# produktion - ljudkontrollen returnerade None och passerade tyst. Exakt den
# feltyp verktyget finns for att fanga. Matcha element brett och pa klasslista.
AUDIO_NOTE_RE = re.compile(
    r'<(?:div|span|p)[^>]*\bclass="[^"]*\bnews-audio__note\b[^"]*"[^>]*>(.*?)</(?:div|span|p)>',
    re.S,
)


def newest_day(html):
    """(iso, synlig etikett) for den oversta dagsgruppen, eller None."""
    m = DAY_GROUP_RE.search(html)
    return (m.group(1), m.group(2).strip()) if m else None


def stated(html):
    """(datetime-attribut, synligt datum) i sect-head-faltet, eller None.

    Andra ledet ar None nar faltet saknar <span class="sect-updated__date">,
    alltsa nar sidan annu inte har den bindbara formen.
    """
    m = TIME_RE.search(html)
    if not m:
        return None
    inner = STATED_DATE_RE.search(m.group(4))
    return m.group(2), (inner.group(2).strip() if inner else None)


def audio_dates(html):
    """(version i ljudkallan, datumtext i ljudnotisen) - endera kan vara None."""
    src = AUDIO_SRC_RE.search(html)
    note = AUDIO_NOTE_RE.search(html)
    note_date = None
    if note:
        tail = note.group(1).rsplit("&middot;", 1)[-1].rsplit("·", 1)[-1]
        note_date = tail.strip() or None
    return (src.group(1) if src else None), note_date


def _same_day(note_text, iso):
    """Grov jamforelse mellan "8 september 2026" och "2026-09-08".

    Jamfor dagsiffra och artal. Det racker for att fanga en glidning pa dagar
    utan att bygga en datumparser for tre sprak - och en grov kontroll som
    haller ar battre an en exakt som maste stangas av.
    """
    y, _m, d = iso.split("-")
    nums = re.findall(r"\d+", note_text)
    return str(int(d)) in nums and y in nums


def check(html, name="<html>"):
    """Lista med problemtexter. Tom lista = faltet stammer med nyheterna."""
    problems = []
    day, said = newest_day(html), stated(html)

    if day is None:
        problems.append("%s: hittar ingen dagsgrupp med data-date" % name)
    if said is None:
        problems.append("%s: hittar inget <time>-falt i sect-head" % name)
    if day is None or said is None:
        return problems

    iso, label = day
    said_iso, said_text = said

    if said_iso != iso:
        problems.append('%s: datetime="%s" men oversta dagsgruppen ar %s'
                        % (name, said_iso, iso))
    if said_text is None:
        problems.append('%s: <time> saknar <span class="sect-updated__date"> - '
                        "faltet kan inte bindas till nyheterna" % name)
    elif said_text != label:
        problems.append('%s: faltet visar "%s" men oversta dagsgruppen heter "%s"'
                        % (name, said_text, label))

    # Ljudnotisen mats mot ljudfilen, aldrig mot nyhetsdatumet.
    src_v, note_date = audio_dates(html)
    if src_v and note_date and not _same_day(note_date, src_v):
        problems.append('%s: ljudnotisen sager "%s" men spelaren laddar ?v=%s'
                        % (name, note_date, src_v))
    return problems


def fix(html):
    """Skriv om HTML-fallbacken ur sidans egen oversta dagsgrupp."""
    day = newest_day(html)
    if day is None:
        raise ValueError("ingen dagsgrupp med data-date - vagrar gissa")
    iso, label = day

    def repl(m):
        open_a, _old, open_b, inner, close = m.groups()
        if not STATED_DATE_RE.search(inner):
            raise ValueError('saknar <span class="sect-updated__date"> - '
                             "lagg in spans i HTML forst")
        new_inner = STATED_DATE_RE.sub(lambda s: s.group(1) + label + s.group(3),
                                       inner, count=1)
        return open_a + iso + open_b + new_inner + close

    new_html, n = TIME_RE.subn(repl, html, count=1)
    if n != 1:
        raise ValueError("hittade inget <time>-falt att skriva om")
    return new_html


def _read_live(url):
    import urllib.request
    with urllib.request.urlopen(url, timeout=30) as r:
        if r.status != 200:
            raise IOError("%s gav HTTP %s" % (url, r.status))
        return r.read().decode("utf-8")


def main(argv):
    if len(argv) < 2 or argv[1] not in ("check", "fix"):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    mode, args = argv[1], [a for a in argv[2:] if a != "--live"]
    live = "--live" in argv[2:]

    if live:
        if mode == "fix":
            print("[datum] fix gar inte att kora mot live", file=sys.stderr)
            return 2
        sources = [(u, _read_live(u)) for u in LIVE_PAGES]
    else:
        if not args:
            print("[datum] ange minst en fil", file=sys.stderr)
            return 2
        sources = [(p, open(p, encoding="utf-8").read()) for p in args]

    if mode == "fix":
        for path, html in sources:
            new = fix(html)
            if new != html:
                open(path, "w", encoding="utf-8").write(new)
                print("[datum] %s: satt till %s" % (path, newest_day(new)[0]))
            else:
                print("[datum] %s: redan korrekt" % path)
        return 0

    problems = []
    for name, html in sources:
        problems.extend(check(html, name))
    print("[datum] %d sidor granskade" % len(sources))
    if not sources:
        print("[datum] BLOCKERAD: noll sidor granskade", file=sys.stderr)
        return 1
    for p in problems:
        print("[datum] FEL %s" % p, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

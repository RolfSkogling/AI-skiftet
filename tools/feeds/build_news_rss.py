#!/usr/bin/env python3
"""build_news_rss.py — bygger RSS-flodet for de dagliga nyhetsnotiserna.

Ett flode per sprak: /rss.xml, /en/rss.xml, /no/rss.xml.
Motivering till tre floden i stallet for ett: notiserna finns i tre fullstandiga
sprakversioner, och en lasare vill ha ETT sprak i sin lasare. Ett gemensamt flode
skulle leverera varje notis tre ganger. hreflang pa sidorna foljer samma logik.

Kalla ar arkivfilerna (nyheter/index.html, en/..., no/...), inte forstasidan:
arkivet innehaller hela historiken inklusive dagens notiser, sa flodet blir
oberoende av hur mycket forstasidan visar. Det gor ocksa att en framtida
forkortning av forstasidan (DEL 2) inte ror flodet.

En <item> per NOTIS, inte per dag. guid byggs pa den SVENSKA rubrikens slug och
ar darfor identisk over de tre floden — samma slug som permalankarna kommer att
anvanda, sa att guid overlever nar <link> byter fran dagsankare till permalank.

Kor:  python3 tools/feeds/build_news_rss.py --repo . [--days 20] [--check]
"""
import argparse
import html
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

BASE = "https://ai-skiftet.se"
TZ = timezone(timedelta(hours=2))

LANGS = {
    "sv": {"archive": "nyheter/index.html", "out": "rss.xml", "code": "sv-SE",
           "title": "AI-skiftet — Nyheter",
           "desc": "Daglig bevakning av AI-utvecklingen med nordisk vinkel: modeller, "
                   "forskning, fysisk AI, hardvara, kvant, arbetsmarknad, reglering och debatt.",
           "link": BASE + "/#nyheter", "archive_url": BASE + "/nyheter/",
           "source_label": "Kalla"},
    "en": {"archive": "en/nyheter/index.html", "out": "en/rss.xml", "code": "en",
           "title": "AI-skiftet — News",
           "desc": "Daily coverage of AI from a Nordic vantage point: models, research, "
                   "physical AI, hardware, quantum, labour market, regulation and debate.",
           "link": BASE + "/en/#nyheter", "archive_url": BASE + "/en/nyheter/",
           "source_label": "Source"},
    "no": {"archive": "no/nyheter/index.html", "out": "no/rss.xml", "code": "nb-NO",
           "title": "AI-skiftet — Nyheter",
           "desc": "Daglig dekning av KI-utviklingen med nordisk vinkling: modeller, "
                   "forskning, fysisk AI, maskinvare, kvante, arbeidsmarked, regulering og debatt.",
           "link": BASE + "/no/#nyheter", "archive_url": BASE + "/no/nyheter/",
           "source_label": "Kilde"},
}

GROUP_RE = re.compile(
    r'<div class="news-date-group"[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*>(.*?)(?=<div class="news-date-group"|\Z)',
    re.S)
CARD_RE = re.compile(r'<div class="news-card"[^>]*data-tags="([^"]*)"[^>]*>(.*?)</div>\s*</div>', re.S)
H3_RE = re.compile(r"<h3>\s*<a[^>]*>(.*?)</a>\s*</h3>", re.S)
P_RE = re.compile(r"<p>(.*?)</p>", re.S)
# CARD_RE ater upp kortets sista </div>-par, sa kallradens egen sluttagg kan
# saknas i `inner`. Ta darfor allt som ateratar och stad bort en ev. sluttagg.
SRC_RE = re.compile(r'<div class="news-card__source">(.*)', re.S)


def source_text(inner):
    m = SRC_RE.search(inner)
    if not m:
        return ""
    s = m.group(1).strip()
    return s[: -len("</div>")].strip() if s.endswith("</div>") else s
TAG_STRIP = re.compile(r"<[^>]+>")


def text_of(fragment):
    """HTML-fragment -> ren text med riktiga tecken (for <title>)."""
    return html.unescape(TAG_STRIP.sub("", fragment)).replace("\xa0", " ").strip()


def slugify(title_text):
    s = title_text.lower()
    for a, b in (("å", "a"), ("ä", "a"), ("ö", "o"), ("æ", "ae"), ("ø", "o"),
                 ("é", "e"), ("ü", "u"), ("&", " och ")):
        s = s.replace(a, b)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    words = [w for w in re.split(r"[^a-z0-9]+", s) if w]
    return "-".join(words[:8]) or "notis"


def parse_archive(path):
    """-> [(datum, [ {tags,title_html,title,paras,source,href} ... ]) ] nyast forst."""
    with open(path, encoding="utf-8") as fh:
        doc = fh.read()
    days = []
    for date, body in GROUP_RE.findall(doc):
        cards = []
        for tags, inner in CARD_RE.findall(body):
            h3 = H3_RE.search(inner)
            if not h3:
                continue
            href = re.search(r'<h3>\s*<a href="([^"]+)"', inner)
            paras = [p for p in P_RE.findall(inner)]
            cards.append({
                "tags": tags.split(),
                "title": text_of(h3.group(1)),
                "href": href.group(1) if href else "",
                "paras": paras,
                "source": source_text(inner),
            })
        if cards:
            days.append((date, cards))
    days.sort(key=lambda d: d[0], reverse=True)
    return days


ENT_RE = re.compile(r"&(?!lt;|gt;|amp;)(#\d+|#x[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]*);")


def entities_to_utf8(fragment):
    """HTML-entiteter -> riktiga tecken, men lamna &lt; &gt; &amp; ororda.

    Sidorna skriver aoo som &aring;/&auml;/&ouml;. I ett RSS-flode ska de vara
    riktiga UTF-8-tecken: alla lasare renderar inte entiteter i <description>,
    och de som gor det gor det olika. Markupentiteterna maste daremot sta kvar
    som entiteter, annars gar HTML:en i beskrivningen sonder."""
    return ENT_RE.sub(lambda m: html.unescape("&%s;" % m.group(1)), fragment)


def build_description(card, conf):
    parts = ["<p>%s</p>" % entities_to_utf8(p.strip()) for p in card["paras"]]
    if card["source"]:
        parts.append('<p class="news-card__source">%s</p>' % entities_to_utf8(card["source"]))
    return "\n".join(parts)


def cdata(s):
    return "<![CDATA[%s]]>" % s.replace("]]>", "]]&gt;")


def xesc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_feed(lang, days, sv_slugs, build_time):
    conf = LANGS[lang]
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:content="http://purl.org/rss/1.0/modules/content/">',
        "  <channel>",
        "    <title>%s</title>" % xesc(conf["title"]),
        "    <link>%s</link>" % conf["link"],
        '    <atom:link href="%s/%s" rel="self" type="application/rss+xml" />'
        % (BASE, conf["out"]),
        "    <description>%s</description>" % xesc(conf["desc"]),
        "    <language>%s</language>" % conf["code"],
        "    <copyright>© 2026 Rolf Skogling</copyright>",
        "    <lastBuildDate>%s</lastBuildDate>" % format_datetime(build_time),
        "    <generator>tools/feeds/build_news_rss.py</generator>",
    ]
    for date, cards in days:
        # Notiserna inom en dag saknar egen tidsstampel. De far 06:00 + 1 min per
        # notis sa att lasarens sortering foljer sidans ordning.
        base_dt = datetime.strptime(date, "%Y-%m-%d").replace(hour=6, tzinfo=TZ)
        for i, card in enumerate(cards):
            slug = sv_slugs[(date, i)]
            guid = "ai-skiftet-notis-%s-%s" % (date, slug)
            link = "%s#dag-%s" % (conf["archive_url"], date)
            out += [
                "    <item>",
                "      <title>%s</title>" % xesc(card["title"]),
                "      <link>%s</link>" % link,
                '      <guid isPermaLink="false">%s</guid>' % guid,
                "      <pubDate>%s</pubDate>"
                % format_datetime(base_dt + timedelta(minutes=len(cards) - i)),
                "      <dc:creator>Rolf Skogling</dc:creator>",
            ]
            for t in card["tags"]:
                out.append("      <category>%s</category>" % xesc(t))
            out += [
                "      <description>%s</description>" % cdata(build_description(card, conf)),
                "    </item>",
            ]
    out += ["  </channel>", "</rss>", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--days", type=int, default=20, help="antal dagar i flodet")
    ap.add_argument("--check", action="store_true",
                    help="bygg men skriv inte — misslyckas om nagot skiljer sig")
    args = ap.parse_args()

    parsed, problems = {}, []
    for lang, conf in LANGS.items():
        path = os.path.join(args.repo, conf["archive"])
        if not os.path.isfile(path):
            problems.append("arkivfilen saknas: %s" % path)
            continue
        parsed[lang] = parse_archive(path)[: args.days]

    if problems:
        for p in problems:
            print("FEL: %s" % p)
        return 1

    # Strukturkontroll: samma dagar och samma antal notiser per dag i alla tre sprak.
    sv_days = parsed["sv"]
    sv_shape = [(d, len(c)) for d, c in sv_days]
    for lang in ("en", "no"):
        shape = [(d, len(c)) for d, c in parsed[lang]]
        if shape != sv_shape:
            diff = [x for x in zip(sv_shape, shape) if x[0] != x[1]][:5]
            problems.append("%s avviker fran sv i dagar/antal notiser: %s" % (lang, diff))
    if problems:
        for p in problems:
            print("FEL: %s" % p)
        print("AVBRUTET — floden byggdes inte. Sprakversionerna maste ha samma struktur.")
        return 1

    sv_slugs, seen = {}, {}
    for date, cards in sv_days:
        for i, card in enumerate(cards):
            slug = slugify(card["title"])
            key = (date, slug)
            if key in seen:  # tva notiser samma dag med samma slug
                seen[key] += 1
                slug = "%s-%d" % (slug, seen[key])
            else:
                seen[key] = 1
            sv_slugs[(date, i)] = slug

    build_time = datetime.now(TZ)
    changed = []
    for lang, conf in LANGS.items():
        xml = build_feed(lang, parsed[lang], sv_slugs, build_time)
        out_path = os.path.join(args.repo, conf["out"])
        old = ""
        if os.path.isfile(out_path):
            with open(out_path, encoding="utf-8") as fh:
                old = fh.read()
        # lastBuildDate andras varje korning; jamfor utan den raden
        norm = lambda s: re.sub(r"<lastBuildDate>.*?</lastBuildDate>", "", s)
        if norm(old) != norm(xml):
            changed.append(conf["out"])
        if not args.check:
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(xml)
        n = sum(len(c) for _, c in parsed[lang])
        print("%-3s %-12s %3d notiser / %2d dagar" % (lang, conf["out"], n, len(parsed[lang])))
    print("andrade floden: %s" % (", ".join(changed) if changed else "inga"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

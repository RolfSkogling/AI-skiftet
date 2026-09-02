#!/usr/bin/env python3
"""podcast_feed.py — underhall och validering av podcast.xml.

Bakgrund (2026-09-02): fram till detta datum innehol podcast.xml ENBART
essabaserade tvapersonspoddar, och vecko-/manadsjobbens checklista (V3/V6)
sa uttryckligen att flodet skulle lamnas orort. Rolf beslutade 2026-09-02 att
vecko- och manadsutgavorna ska in i SAMMA flode. Reglerna ar omskrivna i
veckan-i-ai och manaden-i-ai. Ateranfor inte det gamla forbudet.

Kommandon
---------
  add       Lagg in ETT avsnitt. Idempotent: finns guid redan gors inget.
  validate  Kontrollera flodet mot podcast-RSS-kraven (Apple/Spotify).

Designval: `add` gor TEXTINFOGNING, inte omskrivning av hela XML-tradet.
Skalet ar att diffen ska visa exakt det tillagda avsnittet och inget annat.
"""
import argparse
import os
import re
import sys
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
from xml.etree import ElementTree as ET

ITUNES = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM = "http://www.w3.org/2005/Atom"
BASE = "https://ai-skiftet.se"

ESC = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def esc(text):
    return "".join(ESC.get(c, c) for c in text)


def hhmmss(seconds):
    seconds = int(round(float(seconds)))
    return "%02d:%02d:%02d" % (seconds // 3600, (seconds % 3600) // 60, seconds % 60)


def audio_duration(path):
    """Langd i sekunder via afinfo (macOS). Returnerar None om det inte gar."""
    import subprocess
    try:
        out = subprocess.run(["afinfo", path], capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"estimated duration:\s*([0-9.]+)", out)
    return float(m.group(1)) if m else None


def build_item(guid, title, description, link, pubdate, audio_url, length, duration,
               episode_type="full", indent="    "):
    lines = [
        "<item>",
        "  <title>%s</title>" % esc(title),
        "  <description>%s</description>" % esc(description),
        "  <link>%s</link>" % esc(link),
        '  <guid isPermaLink="false">%s</guid>' % esc(guid),
        "  <pubDate>%s</pubDate>" % pubdate,
        '  <enclosure url="%s" length="%d" type="audio/mp4" />' % (esc(audio_url), length),
        "  <itunes:duration>%s</itunes:duration>" % duration,
        "  <itunes:episodeType>%s</itunes:episodeType>" % episode_type,
        "  <itunes:explicit>false</itunes:explicit>",
        "</item>",
    ]
    return "\n".join(indent + ln for ln in lines)


ITEM_RE = re.compile(r"[ \t]*<item>.*?</item>\n?", re.S)
GUID_RE = re.compile(r"<guid[^>]*>(.*?)</guid>", re.S)
PUB_RE = re.compile(r"<pubDate>(.*?)</pubDate>", re.S)


def insert_item(xml_text, item_block, guid, pubdate):
    """Infoga item kronologiskt (nyast forst). Idempotent pa guid."""
    if ">%s<" % guid in xml_text or ">" + guid + "</guid>" in xml_text:
        return xml_text, False
    want = parsedate_to_datetime(pubdate)
    for m in ITEM_RE.finditer(xml_text):
        pm = PUB_RE.search(m.group(0))
        if pm and parsedate_to_datetime(pm.group(1).strip()) < want:
            return xml_text[:m.start()] + item_block + "\n" + xml_text[m.start():], True
    # aldst av alla -> sist, precis fore </channel>
    idx = xml_text.rindex("</channel>")
    return xml_text[:idx] + item_block + "\n" + xml_text[idx:], True


def cmd_add(args):
    path = args.feed
    with open(path, encoding="utf-8") as fh:
        xml_text = fh.read()

    audio_path = args.audio_file or os.path.join(os.path.dirname(path), "audio",
                                                 os.path.basename(args.audio_url))
    if not os.path.isfile(audio_path):
        sys.exit("FEL: hittar inte ljudfilen %s — enclosure length maste vara sann." % audio_path)
    length = os.path.getsize(audio_path)

    duration = args.duration
    if not duration:
        secs = audio_duration(audio_path)
        if secs is None:
            sys.exit("FEL: kunde inte lasa langden ur %s — ange --duration HH:MM:SS." % audio_path)
        duration = hhmmss(secs)

    if args.pubdate:
        dt = datetime.fromisoformat(args.pubdate)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    pubdate = format_datetime(dt)

    url = args.audio_url if args.audio_url.startswith("http") else BASE + "/" + args.audio_url.lstrip("/")
    block = build_item(args.guid, args.title, args.description, args.link, pubdate,
                       url, length, duration, args.episode_type)
    new_text, changed = insert_item(xml_text, block, args.guid, pubdate)
    if not changed:
        print("OFORANDRAD: guid %s finns redan i flodet." % args.guid)
        return 0
    if args.dry_run:
        print(block)
        return 0
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new_text)
    print("TILLAGT: %s (%s, %d bytes, %s)" % (args.guid, url, length, duration))
    return 0


REQUIRED_CHANNEL = ["title", "link", "description", "language"]


def cmd_validate(args):
    path = args.feed
    with open(path, "rb") as fh:
        raw = fh.read()
    problems, notes = [], []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        print("OGILTIG XML: %s" % exc)
        return 1

    if root.tag != "rss" or root.get("version") != "2.0":
        problems.append('rotelementet ska vara <rss version="2.0">')
    ns = re.findall(rb'xmlns:(\w+)="([^"]+)"', raw[:1200])
    nsmap = {k.decode(): v.decode() for k, v in ns}
    if nsmap.get("itunes") != ITUNES:
        problems.append("namnrymden xmlns:itunes saknas eller ar fel")
    if nsmap.get("atom") != ATOM:
        problems.append("namnrymden xmlns:atom saknas eller ar fel")

    ch = root.find("channel")
    if ch is None:
        print("OGILTIG: <channel> saknas")
        return 1
    for tag in REQUIRED_CHANNEL:
        if ch.findtext(tag) is None or not (ch.findtext(tag) or "").strip():
            problems.append("channel/%s saknas" % tag)
    if ch.find("{%s}image" % ITUNES) is None:
        problems.append("channel/itunes:image saknas — Apple avvisar flodet utan omslag")
    else:
        href = ch.find("{%s}image" % ITUNES).get("href")
        if not href or not href.startswith("http"):
            problems.append("itunes:image href maste vara en absolut URL")
    if ch.find("{%s}category" % ITUNES) is None:
        problems.append("channel/itunes:category saknas")
    if ch.findtext("{%s}explicit" % ITUNES) is None:
        problems.append("channel/itunes:explicit saknas")
    if ch.find("{%s}owner" % ITUNES) is None:
        notes.append("channel/itunes:owner saknas — flodet ar giltig RSS anda och fungerar "
                     "i Spotify och vanliga poddappar, men Apple Podcasts kraver en "
                     "kontakt-e-post vid inskickning. Publiceras e-posten blir den offentlig; "
                     "det ar Rolfs beslut, inte ett tekniskt fel.")
    if ch.find("{%s}link" % ATOM) is None:
        notes.append("atom:link rel=self saknas (rekommenderat)")

    guids, items = {}, ch.findall("item")
    if not items:
        problems.append("flodet innehaller inga <item>")
    for i, it in enumerate(items, 1):
        who = it.findtext("title") or "item %d" % i
        g = it.findtext("guid")
        if not g or not g.strip():
            problems.append("%s: guid saknas" % who)
        elif g.strip() in guids:
            problems.append("%s: guid ar en dubblett av %s" % (who, guids[g.strip()]))
        else:
            guids[g.strip()] = who
        pd = it.findtext("pubDate")
        if not pd:
            problems.append("%s: pubDate saknas" % who)
        else:
            try:
                parsedate_to_datetime(pd.strip())
            except (TypeError, ValueError):
                problems.append("%s: pubDate ar inte giltig RFC 822 (%r)" % (who, pd))
        enc = it.find("enclosure")
        if enc is None:
            problems.append("%s: enclosure saknas" % who)
            continue
        if not (enc.get("url") or "").startswith("http"):
            problems.append("%s: enclosure url maste vara absolut" % who)
        if enc.get("type") != "audio/mp4":
            problems.append("%s: enclosure type ar %r, ska vara audio/mp4" % (who, enc.get("type")))
        try:
            ln = int(enc.get("length") or 0)
        except ValueError:
            ln = 0
        if ln <= 0:
            problems.append("%s: enclosure length saknas eller ar 0" % who)
        elif args.repo:
            local = os.path.join(args.repo, enc.get("url").split(BASE + "/")[-1].split("?")[0])
            if os.path.isfile(local):
                real = os.path.getsize(local)
                if real != ln:
                    problems.append("%s: enclosure length %d != faktisk filstorlek %d"
                                    % (who, ln, real))
            else:
                notes.append("%s: ljudfilen finns inte lokalt (%s)" % (who, local))
        if not it.findtext("{%s}duration" % ITUNES):
            notes.append("%s: itunes:duration saknas (rekommenderat)" % who)

    print("%d avsnitt granskade, %d unika guid" % (len(items), len(guids)))
    for n in notes:
        print("  NOT: %s" % n)
    if problems:
        for p in problems:
            print("  FEL: %s" % p)
        print("VALIDERING MISSLYCKADES (%d fel)" % len(problems))
        return 1
    print("VALIDERING OK")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="lagg in ett avsnitt (idempotent)")
    a.add_argument("--feed", required=True)
    a.add_argument("--guid", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--description", required=True)
    a.add_argument("--link", required=True)
    a.add_argument("--audio-url", required=True, help="t.ex. /audio/veckan-2026-W36.m4a")
    a.add_argument("--audio-file", help="lokal sokvag; annars <repo>/audio/<filnamn>")
    a.add_argument("--pubdate", help="ISO 8601, t.ex. 2026-09-06T20:00:00+02:00")
    a.add_argument("--duration", help="HH:MM:SS; annars lases den ur ljudfilen")
    a.add_argument("--episode-type", default="full", choices=["full", "trailer", "bonus"])
    a.add_argument("--dry-run", action="store_true")
    a.set_defaults(func=cmd_add)

    v = sub.add_parser("validate", help="validera flodet")
    v.add_argument("--feed", required=True)
    v.add_argument("--repo", help="repo-rot; kontrollerar da enclosure length mot filstorlek")
    v.set_defaults(func=cmd_validate)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bygger sitemap.xml och robots.txt för ai-skiftet.se.

Sitemap:en är GENERERAD — skriv aldrig i den för hand. Kör om efter varje
publicering som lägger till eller tar bort en sida:

    python3 tools/feeds/build_sitemap.py --repo . --write

lastmod hämtas från git (senaste commit som rörde filen), inte från filsystemets
mtime, eftersom en klon får dagens mtime på allt vid checkout.

Sidorna bär redan <link rel="alternate" hreflang="..."> i <head>, vilket är det
sökmotorerna använder för språkkoppling. Sitemap:en håller sig därför till loc +
lastmod och duplicerar inte den informationen — ett fält mindre som kan bli fel.
"""
import argparse
import os
import subprocess
import sys
from xml.sax.saxutils import escape

BASE = "https://ai-skiftet.se"

# Sidor som inte ska indexeras: fragment, mallar, arbetsfiler.
SKIP_DIRS = {".git", "tools", "node_modules", "assets"}
SKIP_FILES = set()


def git_lastmod(repo, rel):
    try:
        out = subprocess.run(
            ["git", "-C", repo, "log", "-1", "--format=%cs", "--", rel],
            capture_output=True, text=True, timeout=30)
        d = out.stdout.strip()
        if len(d) == 10 and d[4] == "-":
            return d
    except Exception:
        pass
    return None


def collect(repo):
    pages = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in sorted(files):
            if not f.endswith(".html"):
                continue
            rel = os.path.relpath(os.path.join(root, f), repo).replace(os.sep, "/")
            if rel in SKIP_FILES:
                continue
            pages.append(rel)
    return sorted(pages)


def loc_for(rel):
    if rel == "index.html":
        return BASE + "/"
    if rel.endswith("/index.html"):
        return BASE + "/" + rel[: -len("index.html")]
    return BASE + "/" + rel


def build(repo):
    pages = collect(repo)
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for rel in pages:
        lines.append("  <url>")
        lines.append("    <loc>%s</loc>" % escape(loc_for(rel)))
        lm = git_lastmod(repo, rel)
        if lm:
            lines.append("    <lastmod>%s</lastmod>" % lm)
        lines.append("  </url>")
    lines.append("</urlset>")
    sitemap = "\n".join(lines) + "\n"
    robots = ("User-agent: *\n"
              "Allow: /\n\n"
              "Sitemap: %s/sitemap.xml\n" % BASE)
    return sitemap, robots, pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)
    sitemap, robots, pages = build(repo)
    if not pages:
        print("BLOCKERAD: inga sidor hittades — kontrollera --repo", file=sys.stderr)
        return 1
    if a.write:
        open(os.path.join(repo, "sitemap.xml"), "w", encoding="utf-8").write(sitemap)
        open(os.path.join(repo, "robots.txt"), "w", encoding="utf-8").write(robots)
        print("Skrev sitemap.xml (%d sidor) och robots.txt" % len(pages))
    else:
        print("%d sidor (torrkörning, inget skrivet)" % len(pages))
    return 0


if __name__ == "__main__":
    sys.exit(main())

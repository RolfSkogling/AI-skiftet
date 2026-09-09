#!/usr/bin/env python3
"""Regressionsprov for audio_embed_check.

Kanslan i provet: den gamla kontrollen ("news-audio" i HTML) ska ge FEL
svar pa fall 1, den nya ska ge RATT. Provet slar alltsa fast exakt den
defekt som lat Sjattedelen publiceras utan spelare 2026-09-09.
"""
import unittest

from audio_embed_check import (
    ABSENT,
    DUPLICATE,
    PRESENT,
    classify,
    classify_podcast,
    essay_player_count,
    malformed_audio_tags,
    podcast_player_count,
)

BASE = "sjattedelen"

# Den CSS som essamallen numera skickar med pa varje sida. Innehaller
# strangen "news-audio" sju ganger men inget <audio-element.
CSS_BLOCK = (
    "  .news-audio{background:var(--surface);border:1px solid var(--line)}"
    ".news-audio__row{display:flex}"
    ".news-audio__icon{font-size:1.5rem}"
    ".news-audio__title{font-weight:700}"
    ".news-audio__note{font-size:.8rem}"
    ".news-audio__player{width:100%}"
    "/*news-audio-css*/\n"
)

PLAYER = (
    '      <div class="news-audio" role="region" aria-label="Lyssna">\n'
    '        <div class="news-audio__row"><span class="news-audio__icon">&#127911;</span></div>\n'
    '        <audio class="news-audio__player" controls preload="none">'
    '<source src="/audio/{}.m4a?v=2026-09-09" type="audio/mp4"></audio>\n'
    "      </div>\n"
).format(BASE)

PODCAST_PLAYER = (
    '      <div class="news-audio news-audio--podcast" role="region" aria-label="Lyssna">\n'
    '        <audio class="news-audio__player" controls preload="none">'
    '<source src="/audio/{}-podcast.m4a?v=2026-09-09" type="audio/mp4"></audio>\n'
    "      </div>\n"
).format(BASE)


def page(body_extra="", css=CSS_BLOCK):
    return (
        "<!doctype html><html><head><style>\n"
        + css
        + "</style></head><body>\n<h1>Sjattedelen</h1>\n"
        + body_extra
        + "<p>Text.</p>\n</body></html>\n"
    )


def old_check(html):
    """Kontrollen som den sag ut fore fixen. Finns har for att provet ska
    kunna visa att den faktiskt ger fel svar, inte bara pastas gora det."""
    return "news-audio" in html


class SidaMedEndastCss(unittest.TestCase):
    """Fall 1: news-audio bara i CSS. Ingen spelare finns."""

    def setUp(self):
        self.html = page()

    def test_gamla_kontrollen_ger_fel_svar(self):
        # Gamla kontrollen sager "spelare finns" — det ar defekten.
        self.assertTrue(old_check(self.html))

    def test_nya_kontrollen_ser_saknad_spelare(self):
        self.assertEqual(classify(self.html, BASE), ABSENT)

    def test_inga_audio_element(self):
        self.assertEqual(essay_player_count(self.html, BASE), 0)


class SidaMedRiktigSpelare(unittest.TestCase):
    """Fall 2: ett riktigt <audio>-element. Spelaren ar inbaddad."""

    def setUp(self):
        self.html = page(PLAYER)

    def test_gamla_kontrollen_rakar_ha_ratt(self):
        self.assertTrue(old_check(self.html))

    def test_nya_kontrollen_ser_befintlig_spelare(self):
        self.assertEqual(classify(self.html, BASE), PRESENT)


class Dubbelinbaddning(unittest.TestCase):
    """Fall 3: tva essaspelare. Gamla kontrollen kan inte se skillnad."""

    def setUp(self):
        self.html = page(PLAYER + PLAYER)

    def test_gamla_kontrollen_ser_ingen_skillnad(self):
        # Identiskt svar som for en spelare och for noll spelare.
        self.assertTrue(old_check(self.html))

    def test_nya_kontrollen_fangar_dubbletten(self):
        self.assertEqual(classify(self.html, BASE), DUPLICATE)


class PoddspelareRaknasInte(unittest.TestCase):
    """En podd-m4a ar inte essans uppläsning och far inte maskera att
    essaspelaren saknas."""

    def test_endast_podd_raknas_som_saknad_essaspelare(self):
        self.assertEqual(classify(page(PODCAST_PLAYER), BASE), ABSENT)

    def test_essa_plus_podd_ar_inte_dubblett(self):
        self.assertEqual(classify(page(PLAYER + PODCAST_PLAYER), BASE), PRESENT)


class FelBasename(unittest.TestCase):
    """En spelare som pekar pa fel ljudfil ar inte den har essans spelare."""

    def test_annan_essas_spelare_raknas_inte(self):
        self.assertEqual(classify(page(PLAYER), "overhanget"), ABSENT)


class Mallrester(unittest.TestCase):
    """Kommentarer och mallplatshallare far inte trigga kontrollen."""

    def test_kommentar_triggar_inte(self):
        html = page('<!-- news-audio: spelare laggs in av pipelinen -->\n')
        self.assertTrue(old_check(html))
        self.assertEqual(classify(html, BASE), ABSENT)

    def test_mallplatshallare_triggar_inte(self):
        html = page('<div class="news-audio"><!--AUDIO-SLOT--></div>\n')
        self.assertTrue(old_check(html))
        self.assertEqual(classify(html, BASE), ABSENT)


class Poddspelaren(unittest.TestCase):
    """Poddspelaren har samma CSS-klass men egen ljudfil och maste kunna
    raknas separat — annars kan markoren falla bort och ge dubbelpodd."""

    def test_css_ensam_ar_inte_poddspelare(self):
        self.assertEqual(classify_podcast(page(), BASE), ABSENT)

    def test_essaspelare_ensam_ar_inte_poddspelare(self):
        self.assertEqual(classify_podcast(page(PLAYER), BASE), ABSENT)

    def test_en_poddspelare_ses(self):
        self.assertEqual(classify_podcast(page(PODCAST_PLAYER), BASE), PRESENT)

    def test_tva_poddspelare_ar_dubblett(self):
        html = page(PODCAST_PLAYER + PODCAST_PLAYER)
        self.assertEqual(classify_podcast(html, BASE), DUPLICATE)
        self.assertEqual(podcast_player_count(html, BASE), 2)

    def test_essa_och_podd_stor_inte_varandra(self):
        html = page(PLAYER + PODCAST_PLAYER)
        self.assertEqual(classify(html, BASE), PRESENT)
        self.assertEqual(classify_podcast(html, BASE), PRESENT)


class TrasigHtml(unittest.TestCase):
    def test_oparad_audiotagg_flaggas(self):
        html = page('<audio class="news-audio__player">\n')
        self.assertEqual(malformed_audio_tags(html), 1)

    def test_hel_sida_flaggas_inte(self):
        self.assertEqual(malformed_audio_tags(page(PLAYER)), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

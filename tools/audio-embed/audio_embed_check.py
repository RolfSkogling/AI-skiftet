#!/usr/bin/env python3
"""Avgor om en essasida faktiskt har ljudspelaren inbaddad.

Bakgrund: den gamla kontrollen letade efter strangen "news-audio" i HTML.
Sedan essamallen borjade skicka med .news-audio-CSS i sitt <style>-block
matchar den strangen aven pa sidor helt utan spelare. Kontrollen matte
alltsa sin egen bokforing i stallet for det tillstand den skulle skydda.

Den har modulen tittar pa sjalva elementet: <audio> vars <source> pekar
pa /audio/<basename>.m4a. CSS, kommentarer och mallrester kan inte
trigga den.

Anvandning:
    audio_embed_check.py <html_fil> <basename>

Skriver ett av orden absent | present | duplicate till stdout.
Exitkod 0 for absent/present, 3 for duplicate.
"""
import re
import sys

# Ett <audio>-element med sitt innehall. DOTALL: <source> ligger pa egen rad.
AUDIO_BLOCK_RE = re.compile(r"<audio\b[^>]*>.*?</audio\s*>", re.S | re.I)
AUDIO_OPEN_RE = re.compile(r"<audio\b", re.I)

ABSENT = "absent"
PRESENT = "present"
DUPLICATE = "duplicate"


def audio_blocks(html):
    """Alla kompletta <audio>...</audio>-element i HTML."""
    return AUDIO_BLOCK_RE.findall(html)


def essay_player_count(html, basename):
    """Antal ljudspelare som pekar pa den har essans ljudfil.

    Poddspelaren pekar pa /audio/<basename>-podcast.m4a och raknas inte,
    eftersom strangen skiljer sig fore .m4a.
    """
    needle = "/audio/{}.m4a".format(basename)
    return sum(1 for block in audio_blocks(html) if needle in block)


def podcast_player_count(html, basename):
    """Antal poddspelare (/audio/<basename>-podcast.m4a) pa sidan."""
    needle = "/audio/{}-podcast.m4a".format(basename)
    return sum(1 for block in audio_blocks(html) if needle in block)


def classify_podcast(html, basename):
    """absent | present | duplicate for poddspelaren pa sidan."""
    return _verdict(podcast_player_count(html, basename))


def classify(html, basename):
    """absent | present | duplicate for essaspelaren pa sidan."""
    return _verdict(essay_player_count(html, basename))


def _verdict(n):
    if n == 0:
        return ABSENT
    if n == 1:
        return PRESENT
    return DUPLICATE


def malformed_audio_tags(html):
    """Antal <audio-oppningar utan matchande </audio>.

    Ett positivt varde betyder att sidan ar trasig pa ett satt som
    classify() inte kan resonera om. Anroparen bor larma, inte gissa.
    """
    return len(AUDIO_OPEN_RE.findall(html)) - len(audio_blocks(html))


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        html = f.read()
    basename = sys.argv[2]

    stray = malformed_audio_tags(html)
    if stray > 0:
        print(
            "[check] VARNING {} oparad <audio-tagg i {}".format(stray, sys.argv[1]),
            file=sys.stderr,
        )

    status = classify(html, basename)
    print(status)
    return 3 if status == DUPLICATE else 0


if __name__ == "__main__":
    sys.exit(main())

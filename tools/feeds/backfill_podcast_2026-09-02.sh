#!/usr/bin/env bash
# Engangsatgard 2026-09-02: for in de vecko- och manadsutgavor som redan finns
# publicerade pa veckan.html i podcast.xml. Skriptet ar idempotent (guid-kontroll)
# och kan koras om utan att skapa dubbletter. Sparas i repot som spar av vad som
# gjordes, inte som ett skript att kora regelbundet — nya utgavor laggs in av
# vecko-/manadsjobbets egna publiceringssteg (V3 i veckan-i-ai).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
FEED="$REPO/podcast.xml"
PY="${PY:-python3}"
ADD="$PY $REPO/tools/feeds/podcast_feed.py add --feed $FEED --link https://ai-skiftet.se/en/veckan.html"

$ADD --guid ai-skiftet-veckan-2026-W32 \
  --title "Week 32 - The Week in AI: Calibration, cost hunting and Norwegian power" \
  --description "Four lines shaped the week of August 4-10, 2026: safety moved from theory into day-to-day operations, costs began to steer the hardware, the Nordics stepped forward as the engine room of the AI build-out, and regulation and the labour market kept falling out of step." \
  --audio-url /audio/veckan-2026-W32.m4a --pubdate 2026-08-11T20:00:00+02:00

$ADD --guid ai-skiftet-veckan-2026-W33 \
  --title "Week 33 - The Week in AI: Arendal week, capital and the burden of proof" \
  --description "Five lines shaped the week of August 10-16, 2026: Norwegian AI policy gathered in Arendal, costs kept redrawing the hardware, labelling and safety limits left the level of principle, the burden of proof on AI's benefits caught up - and the quantum field delivered three results in a single week." \
  --audio-url /audio/veckan-2026-W33.m4a --pubdate 2026-08-16T20:00:00+02:00

$ADD --guid ai-skiftet-veckan-2026-W34 \
  --title "Week 34 - The Week in AI: The school year, the safety limits and the power" \
  --description "Five lines shaped the week of August 17-23, 2026: the new school year made children and teenagers the front line of regulation, safety work became visible, the burden of proof on AI cut both ways, the Nordics became a construction site while public opinion cooled - and capital tied itself together more tightly as the thresholds fell." \
  --audio-url /audio/veckan-2026-W34.m4a --pubdate 2026-08-23T20:00:00+02:00

$ADD --guid ai-skiftet-veckan-2026-W35 \
  --title "Week 35 - The Week in AI: The chip giant, the ownership changes and the machines" \
  --description "Five lines shaped the week of August 24-30, 2026: Nvidia set the pace in both directions, ownership changes reached Norwegian robotics and Nordic language models, agents left the screen and took hold of physical machines, labour-market effects got numbers while the measurement base turned out to be thin - and the rulebooks diverged while the technology tested them." \
  --audio-url /audio/veckan-2026-W35.m4a --pubdate 2026-08-31T20:00:00+02:00

$ADD --guid ai-skiftet-manaden-2026-08 \
  --title "August 2026 - The Month in AI: The labs hit the brakes, the capital hit the gas" \
  --description "August 2026 was the month when the industry's two forces pulled hard in opposite directions. Safety incidents made the labs brake their own models while capital poured into infrastructure faster than ever. In between, the EU transparency rules took effect in earnest, the Nordics became one of the world's most sought-after places to build AI - and the question of what all this AI actually delivers got its first uncomfortable numbers." \
  --audio-url /audio/manaden-2026-08.m4a --pubdate 2026-09-01T07:00:00+02:00

$PY "$REPO/tools/feeds/podcast_feed.py" validate --feed "$FEED" --repo "$REPO"

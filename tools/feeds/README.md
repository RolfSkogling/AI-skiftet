# tools/feeds — RSS, poddflöde och Nordentagg

Tillagt 2026-09-02. Tre verktyg som hänger ihop med publiceringen av ai-skiftet.se.

## build_news_rss.py — nyhetsflödet

Bygger `rss.xml`, `en/rss.xml` och `no/rss.xml` ur **arkivfilerna**
(`nyheter/index.html`, `en/nyheter/index.html`, `no/nyheter/index.html`).

```bash
python3 tools/feeds/build_news_rss.py --repo . --days 20          # bygg
python3 tools/feeds/build_news_rss.py --repo . --days 20 --check  # bygg inte, jämför bara
```

**Ett flöde per språk, inte ett gemensamt.** Notiserna finns i tre fullständiga
språkversioner. Ett gemensamt flöde skulle leverera varje notis tre gånger till
samma läsare. `hreflang` på sidorna följer redan samma logik.

**En `<item>` per notis, inte per dag.** `guid` byggs på den svenska rubrikens
slug och är identisk över de tre flödena. Det är samma slug som permalänkarna
ska använda — när `<link>` byter från dagsankare till permalänk är `guid`
oförändrad, så ingen läsare får om notiserna som nya.

**Källan är arkivet, inte förstasidan.** Arkivet har hela historiken inklusive
dagens notiser. Flödet blir därmed oberoende av hur mycket förstasidan visar,
och en framtida förkortning av förstasidan rör inte flödet.

**Strukturkontroll.** Skriptet avbryter om språkversionerna inte har samma dagar
med samma antal notiser. Det är också en användbar kontroll av att den dagliga
publiceringen faktiskt gick igenom i alla tre språk.

Notiserna saknar egen tidsstämpel. De får 06:00 lokal tid plus en minut per
notis, så att läsarens sortering följer sidans ordning.

### Steg i den dagliga pipelinen

Kör efter att de sex HTML-filerna är pushade, innan verifieringen:

```bash
python3 tools/feeds/build_news_rss.py --repo <arbetskopia> --days 20
# PUT rss.xml, en/rss.xml, no/rss.xml
```

## podcast_feed.py — poddflödet

**Regeländring 2026-09-02.** Fram till detta datum innehöll `podcast.xml` enbart
essäbaserade tvåpersonspoddar, och vecko-/månadsjobbens checklista sa uttryckligen
att flödet skulle lämnas orört (V3/V6). Rolf beslutade 2026-09-02 att vecko- och
månadsutgåvorna ska in i **samma** flöde — ett flöde, inte två. Reglerna är
omskrivna i `veckan-i-ai` och `manaden-i-ai`. Återinför inte det gamla förbudet.

```bash
python3 tools/feeds/podcast_feed.py add --feed podcast.xml \
  --guid ai-skiftet-veckan-2026-W36 \
  --title "Week 36 - The Week in AI: <rubrik>" \
  --description "<ingress>" \
  --link https://ai-skiftet.se/en/veckan.html \
  --audio-url /audio/veckan-2026-W36.m4a \
  --pubdate 2026-09-06T20:00:00+02:00

python3 tools/feeds/podcast_feed.py validate --feed podcast.xml --repo .
```

- `add` är **idempotent** på `guid` och infogar i kronologisk ordning.
- `add` gör textinfogning, inte omskrivning av hela XML-trädet, så diffen visar
  exakt det tillagda avsnittet och inget annat.
- `--duration` läses ur ljudfilen med `afinfo` om den inte anges.
- `enclosure length` läses ur den **faktiska filen** — aldrig gissad. Fel längd
  får poddappar att avbryta nedladdningen i förtid.
- `validate` kontrollerar namnrymder, obligatoriska kanalelement, unika guid,
  RFC 822-datum, `audio/mp4` och att `length` stämmer med filstorleken.

`backfill_podcast_2026-09-02.sh` är engångskörningen som förde in W32–W35 och
augustimånaden. Den ligger kvar som spår av vad som gjordes.

**Öppen punkt:** `itunes:owner` med kontakt-e-post saknas. Flödet är giltig RSS
utan den och fungerar i Spotify och vanliga poddappar, men Apple Podcasts kräver
en e-postadress vid inskickning, och den blir offentlig. Det är ett beslut för
Rolf, inte ett tekniskt fel — validatorn rapporterar det som NOT, inte FEL.

`assets/podcast-cover.png` (1400×1400) är ett platshållaromslag i sajtens
formspråk. Byt gärna ut bilden; `itunes:image href` behöver inte ändras.

## tag_norden.py — Nordentaggen

Varje notis slutar redan med ett "För Norden"-stycke, så en filtrering på
"nämner Norden" skulle träffa alla notiser. Filtret ska i stället fånga notiser
med **nordisk primärvinkel** — där den nordiska händelsen är själva nyheten.

Det var inte maskinellt identifierbart i den gamla uppmärkningen. Lösningen är
tvådelad:

1. **Framåt:** den dagliga pipelinen skriver `norden` i `data-tags` när notisen
   har nordisk primärvinkel. Bedömningen görs redan — redaktionella linjen kräver
   minst en sådan notis per dag. Det som saknades var att skriva ned den.
2. **Bakåt:** skriptet gör en heuristisk gallring av arkivet. Heuristiken läser
   **bara rubriken och första stycket**, aldrig "För Norden"-stycket, och matchar
   mot en lista av nordiska egennamn plus landsord i rubriken.

```bash
python3 tools/feeds/tag_norden.py --repo . --rapport   # visa träffar, ändra inget
python3 tools/feeds/tag_norden.py --repo . --skriv     # sätt taggen i alla 6 filer
```

Körningen 2026-09-02 gav 170 träffar av 1 319 notiser (13 procent, ungefär en per
dag). Träffarna granskades manuellt innan de skrevs. Skriptet är idempotent.

`norden` får ingen egen färgad bricka på kortet — det är en tvärgående dimension,
inte en tionde kategori. En notis kan vara både `reglering` och `norden`.
Filterknappen står därför separerad direkt efter "Alla".

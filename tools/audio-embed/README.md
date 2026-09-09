# audio-embed — kontroll av ljudspelaren i essäsidor

## Varför modulen finns

Publiceringspipelinen för essäljud avgjorde om spelaren redan var
inbäddad genom att leta efter strängen `news-audio` i sidans HTML:

```bash
elif grep -q "news-audio" "$out"; then      # run_one.sh
```

```python
if 'news-audio' in html:                     # embed_player.py
```

Sedan essämallen började skicka med `.news-audio`-CSS i sitt
`<style>`-block finns den strängen på **varje** sida — även på sidor
helt utan spelare. Kontrollen mätte alltså sin egen bokföring i stället
för det tillstånd den skulle skydda.

Resultat vid publiceringen av *Sjättedelen* 2026-09-09: sidorna hade sju
`news-audio`-träffar och noll `<audio>`-element. Pipelinen rapporterade
`embed sv/en/no already present` och `DONE`. Ingen spelare publicerades,
och inget larmade.

## Vad kontrollen gör i stället

`audio_embed_check.py` räknar själva elementet: `<audio>` vars `<source>`
pekar på `/audio/<basename>.m4a`. CSS, kommentarer och mallplatshållare
kan inte trigga den.

```
absent     ingen spelare  -> bädda in
present    exakt en       -> lämna orörd
duplicate  fler än en     -> avbryt, rensa för hand
```

Poddspelaren (`/audio/<basename>-podcast.m4a`) räknas separat via
`classify_podcast()`, så de två inte maskerar varandra.

## Användning

```bash
python3 tools/audio-embed/audio_embed_check.py <html-fil> <basename>
bash   tools/audio-embed/verifiera.sh                     # regressionsprovet
bash   tools/audio-embed/verifiera.sh --live sjattedelen  # publicerade sidor
```

Exitkod 3 betyder dubbelinbäddning.

## Regressionsprovet

`test_audio_embed_check.py` innehåller den gamla kontrollen som
`old_check()` och slår fast att den ger **fel** svar på en sida med
`news-audio` enbart i CSS, medan den nya ger rätt. Provet skyddar alltså
mot att genvägen återinförs, inte bara mot symtomet.

## Var koden körs

Den körande pipelinen ligger i `~/AI/audiobook/essays-batch/` och är
**inte versionerad**. Den katalogen innehåller en kopia av den här
modulen som `run_one.sh`, `embed_player.py` och `embed_podcast_player.py`
importerar.

Det betyder att repot och körmiljön kan glida isär. En enda hemvist bör
beslutas — antingen flyttas pipelinen hit, eller så symlänkas
`essays-batch`-kopian mot den här filen. Tills dess: kopiera hit vid
varje ändring och kör `verifiera.sh`.

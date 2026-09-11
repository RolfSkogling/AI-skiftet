# datumkontroll

Håller förstasidans **"Senast uppdaterat"** bundet till sidans egna nyheter.

## Varför verktyget finns

Startsideombyggnaden 2026-09-08 (`85d104d`) la in datumet som en hårdkodad
sträng i `sect-head`:

```html
<time datetime="2026-09-08">Senast uppdaterat 8 september 2026</time>
```

Inget skript skrev fältet, så det frös fast vid ombyggnadsdatumet medan
nyheterna rullade vidare. Den 11 september påstod sidan "8 september" med
10 september överst i listan — i alla tre språken.

Feltypen är den återkommande: **ett fält som påstår något om systemets
tillstånd men mäter något annat.** Här mätte det när någon senast rörde mallen,
inte när nyheterna publicerades. Ett sådant fält blir fel förr eller senare,
hur noga man än fyller i det för hand.

## Hur det är löst

Samma princip som `essay-count`: fältet räknar sig självt ur det det beskriver.
Sidan har redan dagens datum i klartext i den översta dagsgruppens etikett, på
rätt språk. Datumfältet **kopierar den strängen** i stället för att formatera
ett eget datum — då finns ingen språkspecifik datumlogik som kan glida isär,
och ingen siffra att fylla i för hand.

Tre lager:

1. **HTML-fallbacken** i filen (det som visas utan JavaScript) — sätts av `fix`.
2. **Inline-skriptet** sist i `<body>` som skriver om fältet i webbläsaren.
3. **Den här kontrollen**, som fallerar om lager 1 glidit isär från nyheterna.

## Användning

```bash
# i pipelinen, EFTER att dagens grupp lagts in men FÖRE push:
python3 tools/datumkontroll/updated_date.py fix index.html en/index.html no/index.html
python3 tools/datumkontroll/updated_date.py check index.html en/index.html no/index.html

# efter push:
python3 tools/datumkontroll/updated_date.py check --live

# allt på en gång i en lokal klon:
bash tools/datumkontroll/verifiera.sh
```

Exit 1 vid isärglidning. `check` utan filer och utan `--live` är också exit 1 —
noll granskade sidor är inte ett rent resultat.

## Ljudnotisen är ett eget mätvärde

Kontrollen granskar även `news-audio__note`, men mot **ljudfilens `?v=`-version**,
aldrig mot nyhetsdatumet. Ett ljud som är två dygn gammalt ska stå som två dygn
gammalt. Att datera om notisen till dagens datum vore att dölja ett större fel
bakom ett snyggare fält — och just den förväxlingen var vad som gjorde felet
den 11 september svårläst: datumfältet ljög, men ljudnotisen talade sanning.

`fix` rör därför aldrig ljudblocket. Ljudnotisen ägs av
`~/AI/ai-skiftet-audio/publish_audio.py` och ska sättas där, vid varje
ljudpublicering.

## Regressionsprov

```bash
python3 tools/datumkontroll/test_updated_date.py
```

Det prov som betyder något är `test_glidning_fangas`: det återskapar exakt
felet från 2026-09-11 — fältet säger 8 september, översta dagsgruppen är den
10:e — och kräver att kontrollen fallerar. Utan det provet kan spärren tyst
sluta fungera vid nästa malländring utan att någon märker det.

`test_ljudnotis_mats_mot_ljudfilen_inte_nyheterna` låser fast den andra halvan:
äldre ljud än nyheter är **inte** ett fel, men en notis som ljuger om ljudet är det.

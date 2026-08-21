# Sprakkontroll — mekanisk sparr mot spraklackage

## Problemet

Norska ord i svensk text laser flytande. Orden ser rimliga ut, boejningen kanns
bekant, och en granskare som laser efter sprakkansla glider forbi dem. Det ar en
strukturell blind flack, inte slarv — darfor hjalper det inte att korrekturlasa
en gang till.

Grundorsaken ar sourcen: nar en notis bygger pa norska primarkallor
(Regjeringen.no, Utdanningsdirektoratet, NRK) folj er terminologin med rakt in i
den svenska texten. `trinn` overlever dar `aarskurs` skulle statt, och
`videregaaende opplaering` dar det skulle statt `gymnasiet`.

Upptackt 2026-08-21 i skolnotisen om norska AI-rad. Arkivsvepet visade att det
inte var ett engangsfel: 95 traffar over hela arkivet, inklusive systematisk
anvandning av norskans `KI-` dar svenskan har `AI-`, och `milliard` dar svenskan
har `miljard`.

## Losningen

Mekanisk kontroll i stallet for mer korrekturlasning.

| Fil | Roll |
|---|---|
| `ordbok.json` | Bade ordlista OCH oversattningsordbok. Varje post har `no` / `sv` / `en`-former. Formerna under `no` far aldrig forekomma i svensk text, formerna under `sv` aldrig i norsk. `en`-formen anvands vid oversattning sa framtida korningar oversatter konsekvent i stallet for att improvisera. |
| `check_language.py` | Granskaren. Exit 0 = rent, exit 1 = traffar. Kollar aven mojibake. |
| `verifiera.sh` | Tunn wrapper for anvandning som verifieringssteg. |

```bash
bash tools/sprakkontroll/verifiera.sh            # hela repot
bash tools/sprakkontroll/verifiera.sh --live     # de sex publicerade sidorna
bash tools/sprakkontroll/verifiera.sh --json     # maskinlasbart
bash tools/sprakkontroll/verifiera.sh index.html no/index.html
```

Sprak bestams av sokvagen: `en/...` = engelska, `no/...` = norska, ovrigt = svenska.

## Sa undviks falska positiver

Kontrollen tar bort foljande innan matchning:

- `<script>`, `<style>`, HTML-kommentarer
- alla taggar och attribut (URL:er innehaller norska slugs)
- `news-card__source`-divar och sprakvaljaren (bestar av egennamn per definition)
- alla fraser i `tillatna_egennamn` (Dagens Naeringsliv, Nasjonal sikkerhetsmyndighet,
  Regeringen.se, Innovasjon Norge, KI-Norge, fylkesnamn ...)
- ALL-VERSALA traffar pa hogst 5 tecken (akronymer: FRA, LO, NHO)

Termpar dar formen ar identisk i bada spraken (`forskning`, `befolkningen`,
`pensjon`) hoppas over automatiskt.

Poster med `"handhavs": false` star kvar i ordboken for oversattningens skull men
fallerar inte bygget. Det galler korta funktionsord (`og`/`och`, `fra`/`fran`,
`til`/`till`) som standigt forekommer i korrekta egennamn
("Likestillings- og diskrimineringsombudet", "Post- och telestyrelsen"), samt
`KI`/`AI` — eftersom KI ocksa ar Karolinska Institutet och statistikens
konfidensintervall pa svenska. KI-sammansattningar i svensk text kontrolleras
darfor manuellt: de ska normalt vara AI-.

## Avsedda citat pa annat sprak

Ska en norsk fras sta kvar i svensk text — ett citat, en rapporttitel — markera
den med `lang`-attribut, sa hoppar kontrollen over innehallet:

```html
<p>Statnett skriver att man &rdquo;<span lang="nb">opptrer n&aelig;ringsn&oslash;ytralt</span>&rdquo;.</p>
```

Det ar korrekt HTML-semantik och gor undantaget synligt i diffen i stallet for
att gomma det i en allowlist.

## Nar ordboken ska utokas

Nar en ny term slinker igenom: lagg till termparet i `ordbok.json` med alla tre
sprakformerna, kor `verifiera.sh` mot hela repot, och kontrollera att traffarna
ar akta innan du rattar. Precision gar fore tackning — en sparr som skriker varg
blir avstangd.

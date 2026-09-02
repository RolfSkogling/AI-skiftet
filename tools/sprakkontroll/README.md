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
| `check_language.py` | Granskaren. Exit 0 = rent, exit 1 = traffar ELLER for fa granskade filer. Kollar aven mojibake. |
| `verifiera.sh` | Tunn wrapper for anvandning som verifieringssteg i en lokal klon. |
| `hamta_och_kor.sh` | Hamtar granskaren ur repot med hard felkontroll och kor den. For korningar utan klon (schemalagda Cowork-korningar). |
| `test_sprakkontroll.py` | Regressionstest. Kor gammal och ny logik mot samma indata och kraver att den gamla slappte igenom felet och den nya fangar det. |

## Tva grindar, inte en (bada tillagda 2026-08-24)

**1. Sprakkod normaliseras, och rotelementet ar inget citat.** Citatregeln nedan
jamforde tidigare lang-attributet med sokvagsspraket rakt av. Sidorna markerar sig
med `<html lang="nb">` medan sokvagsspraket heter `no` — alltsa raknades HELA det
norska dokumentet som ett frammandespraakigt citat och tomdes fore granskning.
`no/index.html` gick in som 103 267 tecken och kom ut som 0. Spaerren gav gront pa
46 norska sidor utan att ha last ett tecken av dem. Nu normaliseras `nb`, `nb-NO`
och `nn` till norska, `<html>` undantas fran regeln, och en OKAND sprakkod
granskas i stallet for att tomas — en felstavad `lang` far aldrig tysta innehall.

**2. Noll granskade filer ar inte ett rent resultat.** `--minst N` (standard 1)
fallerar om farre an N filer granskades. Utan den gav en tom filmangd — fel
katalog, misslyckad nedladdning, sidor skrivna pa fel plats — exit 0, och
publiceringen slapptes igenom av en sparr som aldrig last nagot. Satt `--minst`
till antalet sidor som faktiskt ska publiceras.

Kor `python3 tools/sprakkontroll/test_sprakkontroll.py` efter varje andring i
granskaren. Testet kraver att den gamla logiken slappte igenom felet — gar aven
den igenom ar testet trasigt, inte fixen bevisad.

```bash
bash tools/sprakkontroll/verifiera.sh            # hela repot
bash tools/sprakkontroll/verifiera.sh --live     # de sex publicerade sidorna
bash tools/sprakkontroll/verifiera.sh --json     # maskinlasbart
bash tools/sprakkontroll/verifiera.sh index.html no/index.html
```

Sprak bestams av sokvagen: `en/...` = engelska, `no/...` = norska, ovrigt = svenska.

## Tre detektorer, inte tva (den tredje tillagd 2026-09-02)

Granskaren har nu tre oberoende detektorer. Hall isar dem — de fangar olika saker:

| Detektor | Fangar | Kalla |
|---|---|---|
| Termlistan | RIKTIGA ord pa FEL sprak (norskt `trinn` i svensk text) | `ordbok.json` -> `termer` |
| Felstavningslistan | strangar som inte ar ord pa NAGOT sprak (`ocksa` med a-umlaut) | `ordbok.json` -> `felstavningar` |
| Mojibake | trasig teckenkodning (`Ã¤`, `Ã¶`) | `MOJIBAKE` i granskaren |

### Varfor den tredje behovdes

Den 28 augusti 2026 publicerades stavfelet **ocks{a-umlaut}** (for *ocksa* med a-ring) och
passerade den blockerande grinden orort. Bada de gamla detektorerna var blinda
av konstruktion:

* **Termlistan** letar efter riktiga ord pa fel sprak. `ocks{a-umlaut}` ar inget ord pa
  vare sig svenska eller norska och kan darfor inte sta i nagon ordlista.
* **Mojibake-listan** letar efter trasiga bytesekvenser. `&auml;` ar valformad
  UTF-8 — tecknet ar korrekt kodat, det ar bara fel tecken.

Kontrollen het sprakkontroll men tackte bara EN sorts sprakfel. Felstavnings-
listan tacker den feltyp en engelskspraakig modell producerar oftast: ratt
konsonanter, fel omljudsvokal.

### Regeln for felstavningslistan

Listan ar **sluten** och far bara innehalla strangar som inte ar ord pa nagot av
spraken. Ar strangen korrekt svenska men fel i norsk text hor den hemma i
termlistan, inte har — annars dubbelrapporteras samma trafk. `test_10` haller
kontraktet och fallerar om listorna overlappar; den fangade `forst` och
`losning` nar listan skrevs.

Lagg **aldrig** in ett ord som existerar pa malspraket. Precision gar fore
tackning: en sparr som skriker varg blir avstangd.

## Live-lage granskar hela sajten (2026-09-02)

`--live` hade en hardkodad lista pa sex nyhetssidor. Foljden var att
essasidorna aldrig granskades mot live — fem spraktraffar i `no/delningen.html`,
`no/minnet-som-vager-ewmc.html` och `no/turbulenta-aren.html` lag opptackta tills
ett fullrepo-svep gjordes for hand. En hardkodad lista vaxer inte med sajten.

`live_sidor()` harleder nu listan ur repot: de sex nyhetssidorna ar alltid med
(de maste granskas aven utan klon), och varje `.html` i arbetstradet laggs till.
Varje ny essa tacks automatiskt fran och med att den finns i repot.

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

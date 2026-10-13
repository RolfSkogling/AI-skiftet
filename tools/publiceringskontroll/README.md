# Publiceringskontroll — ingen lankad essa utan spelare

## Regeln som galler framat

1. **Ljudkortet gar in i samma commit som essan.** Inte i en commit efter. Inte
   i tre commits efter. Samma commit.
2. **Under alla omstandigheter publiceras spelaren fore bibliotek och
   forstasida.** Gar det av nagot skal inte att fa in kortet i samma commit, ar
   ordningen tvingande: essafil med spelare forst, lankarna sedan. Aldrig
   omvant.
3. **Den har kontrollen ar ett BLOCKERANDE steg.** Den kors som forkontroll
   (`--local`) fore push OCH mot live efter push. Faller nagon av de tva, ar
   publiceringen inte klar — oavsett vad commit-loggen sager.

## Varfor regeln finns, matt

Essan "Sa mycket, sa fort" publicerades 2026-10-13 i tre sprakversioner
10:33:50–10:33:57 **utan ljudkortet i filen**. Bibliotek och forstasidor lankade
essan 10:34:00–10:34:14. Ljudkortet lades in forst 10:38:07–10:38:11, i separata
commits.

Under fyra minuter lag essan alltsa lankad fran forstasidan utan spelare. Och
eftersom GitHub Pages serverar HTML med `cache-control: max-age=600` kunde en
lasare som hamnade pa sidan under de fyra minuterna fa den spelarlosa versionen
i upp till tio minuter till.

Korningen rapporterade **gront**. Varje commit hade lyckats, varje steg hade
exitkod 0. Den matte sin egen bokforing — inte sidans tillstand.

Det ar den feltypen den har kontrollen finns for. Den laser filernas faktiska
innehall och drar aldrig nagon slutsats ur commit-loggar, ur exitkoder fran
tidigare steg eller ur lokal bokforing.

## Kommandorader

```bash
# Forkontroll fore push — las arbetstradet pa disk. Tar inga sekunder.
python3 tools/publiceringskontroll/check_ljudkort.py --local . --slug sa-mycket-sa-fort

# Efter push — mot den publicerade sajten, med egen cache-bustare per hamtning.
python3 tools/publiceringskontroll/check_ljudkort.py --live --slug sa-mycket-sa-fort

# Svepet: alla essaer biblioteket lankar, alla tre sprak. Sa hittas GAMLA fel.
python3 tools/publiceringskontroll/check_ljudkort.py --live

# Bada stegen i ratt ordning, med hard grind pa vart och ett.
bash tools/publiceringskontroll/kor.sh --slug sa-mycket-sa-fort
bash tools/publiceringskontroll/kor.sh                     # svepet, bada lagena

# Maskinlasbart, for loggning eller vidare granskning.
python3 tools/publiceringskontroll/check_ljudkort.py --live --slug X --json
```

`--live` ar forval. `--local <repo-rot>` laser fran disk i stallet. `--slug` kan
upprepas. Utan `--slug` svepas allt biblioteket lankar.

## Exitkoder

| Kod | Betydelse |
|---|---|
| 0 | Ingen rad fallde och ingen rad ar overifierad. Publicera. |
| 1 | Minst en rad **FALLD**: lankad essa utan spelbart ljudkort. Publicera INTE — och avlanka om det redan ligger ute. |
| 2 | **KONTROLLFEL**: en sida gick inte att hamta, en sprakvaxlarlank gick inte att folja, ett ovantat svar, eller noll essaer i omfanget. |

Exit 2 ar inte ett godkannande. Det ar en kontroll som inte har kunnat mata det
den ska skydda, och det ska behandlas som ett hinder precis som exit 1. Samma
lektion som sprakkontrollens `--minst`: noll granskade filer ar inte ett rent
resultat.

## Vad som raknas som ett ljudkort

Allt detta, i essafilen:

- ett element med `class="news-audio"` (exakt klasstoken, inte delstrang — annars
  raknas `news-audio__row` som ett kort),
- ett `<audio>`-element inuti det,
- en `<source src="...">` inuti `<audio>` som pekar pa en ljudfil.

Och i `--live`-lage dessutom:

- ljudfilens URL svarar **200**,
- och svarar **206 pa en range-request**. Det ar beviset att den gar att spela:
  en spelare som inte kan begara ett byteintervall kan inte spola, och pa en
  del plattformar inte starta alls.

I `--local`-lage mats i stallet att ljudfilen finns pa disk och inte ar 0 byte.

**Delvis narvaro faller, med egen forklaring.** Kort men inget `<audio>`.
`<audio>` men ingen `<source>`. `<source>` utan `src`. Kalla som svarar 404.
Inget av det passerar tyst — ett halvt ljudkort ar inget ljudkort.

Utkommenterad markup raknas aldrig. `<script>`, `<style>` och HTML-kommentarer
blankas fore granskningen, sa en `<!-- <div class="news-audio"> ... -->` ger
inte gront.

## Vad som raknas som lankat

Essafilens filnamn forekommer som `href` i biblioteket eller forstasidan **for
samma sprak**:

| Sprak | Essafil | Bibliotek | Forstasida |
|---|---|---|---|
| sv | `<slug>.html` | `essaer.html` | `index.html` |
| en | `en/<slug>.html` | `en/essays.html` | `en/index.html` |
| no | `no/<slug>.html` | `no/essays.html` | `no/index.html` |

Hrefen loses mot sidans egen plats, och matchar bade pa hel sokvag och pa
filnamn. Tvetydigheten faller medvetet mot "lankad" — det ar den sidan av felet
som leder till en fallning i stallet for till ett tyst godkannande.

## Utfallsmatrisen

| Lankad | Ljudkort | Utfall |
|---|---|---|
| ja | helt och spelbart | **OK** |
| ja | saknas eller trasigt | **FALLD** (exit 1) |
| nej | saknas | **OK med anmarkning** — det legitima mellanlaget under publicering |
| nej | finns | **OK** |

Mellanlaget ar legitimt i exakt en riktning: essafilen far ligga ute utan att
vara lankad. Den far aldrig vara lankad utan att vara spelbar.

## Egen slug per sprak

Den engelska och norska versionen kan ligga pa en annan slug an den svenska —
`globala-scenarier.html` heter `global-scenarios.html` pa engelska och
`globale-scenarioer.html` pa norska. Kontrollen **gissar aldrig** att slugen ar
densamma. Den laser sprakvaxlaren (`class="lang-switcher"`) i den svenska filen
och foljer `<a href="/en/...">` och `<a href="/no/...">`.

Finns ingen sprakvaxlare, eller pekar den inte pa `en/` respektive `no/`,
rapporteras raden som **OVERIFIERAD** och korningen slutar pa exit 2. En
overifierad rad ar inte en godkand rad.

## Svepet

Omfanget harleds ur biblioteket: varje `<a class="essay-card" href="...">` i
`essaer.html`. Ingen hardkodad lista. En hardkodad lista vaxer inte med sajten,
och det var precis sa essasidorna undslapp sprakkontrollens live-lage till
2026-09-02.

Svepet ar det som hittar gamla fel. En kontroll som bara kan provas mot dagens
slug finner aldrig nagot annat an dagens misstag.

### Svepet kan vara rott utan att nagot nytt ar fel

Aldre sidor i biblioteket kan sakna ljudkort av redaktionella skal, och vissa av
dem saknar ocksa sprakvaxlare, vilket gor deras en- och no-rader omatbara. Da
faller svepet, och det ar ratt: en lankad sida utan spelare ar antingen en sida
som ska fa en spelare, eller en sida som inte hor hemma i `essay-card`-listan.

Ingen undantagslista finns, och ingen ska laggas in. En undantagslista ar precis
den mekanism som gor en kontroll tandlos — den flyttar beslutet fran den som
publicerar till en fil ingen laser.

Grinden for en **ny** publicering ar darfor `--slug`. Kor den. Svepet utan
`--slug` ar en aterkommande granskning av hela biblioteket, inte en grind, och
dess utfall ar en arbetslista.

Kor `check_ljudkort.py --live` nar du vill ha den listan. Den regenereras ur
sajtens faktiska tillstand varje gang och behover darfor inte sta nedskriven
nagonstans.

## Cache-bustningen

Varje enskild hamtning i `--live`-lage far en unik parameter
`?kontroll=<nanosekunder>.<pid>.<lopnummer>`, plus `Cache-Control: no-cache` och
`Pragma: no-cache`. Varken Fastly, GitHub Pages eller en mellanliggande proxy kan
svara pa den URL:en med nagot aldre — den har aldrig efterfragats forut. Utan
det matte kontrollen cachen i stallet for sidan, och det ar exakt den cachen
(`max-age=600`) som forlangde felet 2026-10-13 fran fyra minuter till fjorton.

Bibliotek och forstasidor hamtas en gang per korning och ateranvands inom
korningen. Det ar ingen cache i den mening kontrollen forbjuder: sidan hamtas med
egen cache-bustare i samma matogonblick som allt annat, och att hamta
`essaer.html` 50 ganger i ett svep mater inte nagot mer. `etag` och
`last-modified` for varje hamtad sida skrivs ut som bevis.

## Beroenden

Bara Pythons standardbibliotek (`urllib`, `re`, `argparse`, `json`, `sys`,
`os`, `time`, `itertools`). Python 3.9+. Ingen token, ingen autentisering, inga
tredjepartspaket. Kontrollen laser bara publika sidor.

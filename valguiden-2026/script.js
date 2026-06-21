const parties = [
  {
    short: "S",
    name: "Socialdemokraterna",
    leader: "Magdalena Andersson",
    color: "#b73442",
    block: "Opposition",
    filters: ["valfard", "trygghet", "ekonomi"],
    foundation: "Demokratisk socialism och socialdemokrati: frihet genom jämlikhet, starkt samhälle, skattefinansierad välfärd och demokratisk kontroll över marknadens effekter.",
    scenario: {
      image: "assets/scenarier/socialdemokraterna-scenario.jpg",
      alt: "Sverige som samhällslandskap med välfärdsinstitutioner, grön industri, bostäder och kollektivtrafik.",
      title: "Ett starkare gemensamt samhälle",
      summary: "Sverige blir mer institutionsburet: vård, skola, omsorg, bostäder och klimatomställning hålls ihop av offentlig investering och arbetslivets organisering.",
      points: [
        "Välfärdsstaten och progressiva skatter bär mer av samhällsbygget.",
        "Arbete, facklig organisering och social rörlighet blir centrum.",
        "Klimatomställningen kopplas till industri, jobb och rättvisa."
      ]
    },
    pitch: "Vill stärka välfärden, hålla ihop arbetslinjen och kombinera trygghetspolitik med mer offentlig kontroll.",
    tags: ["välfärd", "jobb", "trygghet", "klimat"],
    stances: { "Offentlig välfärd": 9, "Marknad/skatt": 4, "Klimatomställning": 7 },
    ai: "Bejakar AI för tillväxt och välfärd, men vill se demokratisk kontroll, skydd mot deepfakes, starkare upphovsrätt och arbetstagarperspektiv.",
    cooperation: "Trolig kärna i ett regeringsskifte. Behöver sannolikt stöd från MP, V och/eller C beroende på mandatläget.",
    watch: ["Hur långt partiet går i migrations- och rättspolitiken", "Balansen mellan V, MP och C i ett S-lett underlag"]
  },
  {
    short: "M",
    name: "Moderaterna",
    leader: "Ulf Kristersson",
    color: "#1f5f9f",
    block: "Tidö",
    filters: ["trygghet", "ekonomi", "migration"],
    foundation: "Liberal konservatism: individens frihet, äganderätt och företagande kombineras med stark stat i kärnuppgifter som rättsstat, försvar och trygghet.",
    scenario: {
      image: "assets/scenarier/moderaterna-scenario.jpg",
      alt: "Ordnat svenskt samhälle med rättsstat, företagande, vägar, handel och effektiva offentliga kärnverksamheter.",
      title: "Frihet med stark kärnstat",
      summary: "Sverige organiseras runt arbete, ägande och företagande, medan staten koncentreras tydligare till trygghet, försvar, rättsväsende och välfärdens kärna.",
      points: [
        "Polis, domstolar och försvar får en mer framträdande roll.",
        "Företagande, arbete och lägre trösklar blir huvudmotorer.",
        "Välfärden ska vara tydlig, mätbar och mer resultatstyrd."
      ]
    },
    pitch: "Betonar brottsbekämpning, arbete, lägre trösklar, stram migration och borgerlig ekonomisk politik.",
    tags: ["lag och ordning", "arbete", "migration", "energi"],
    stances: { "Offentlig välfärd": 5, "Marknad/skatt": 8, "Klimatomställning": 5 },
    ai: "Har en tydligt teknikoptimistisk linje: AI för tillväxt, välfärdsteknik, kortare vårdköer, regulatoriska testmiljöer och stärkt brottsbekämpning.",
    cooperation: "Regeringsledande parti i Tidösamarbetet. Mest sannolika samarbeten finns med KD, L och SD.",
    watch: ["Hur stor roll SD får efter valet", "Om L och KD klarar spärr och mandat"]
  },
  {
    short: "SD",
    name: "Sverigedemokraterna",
    leader: "Jimmie Åkesson",
    color: "#d6a12f",
    block: "Tidö",
    filters: ["migration", "trygghet", "valfard"],
    foundation: "Socialkonservatism med nationalistisk grundsyn: nationell gemenskap, kulturell kontinuitet, restriktiv migration, lag och ordning och välfärd inom en stark samhällsgemenskap.",
    scenario: {
      image: "assets/scenarier/sverigedemokraterna-scenario.jpg",
      alt: "Sverige med småstäder, kulturmiljöer, trygghetsinstitutioner, vård och kustnära gränskontroll.",
      title: "Ett mer sammanhållet folkhem",
      summary: "Sverige betonar nationell sammanhållning, trygghet och social konservatism: färre snabba samhällsförändringar, hårdare ordning och välfärd inom en tydligare nationell ram.",
      points: [
        "Migration och integration blir mer restriktiva och kravorienterade.",
        "Polis, straff och gränskontroll får större politisk tyngd.",
        "Välfärd, pensioner och lokalsamhälle kopplas till nationell solidaritet."
      ]
    },
    pitch: "Profilerar sig på restriktiv migration, kriminalitet, nationell sammanhållning och välfärd före nya åtaganden.",
    tags: ["migration", "trygghet", "välfärd", "kultur"],
    stances: { "Offentlig välfärd": 7, "Marknad/skatt": 5, "Klimatomställning": 3 },
    ai: "Pragmatisk nationell linje: AI kan hjälpa vård, tolkning och brottsbekämpning, men tekniken ska tjäna vanligt folk och inte styras av Big Tech eller överstatlighet.",
    cooperation: "Samarbetsparti till regeringen 2022-2026. Fortsatt Tidösamarbete är den tydligaste vägen till inflytande.",
    watch: ["Krav på regeringsmedverkan", "Relationen till Liberalernas väljare och partilinje"]
  },
  {
    short: "V",
    name: "Vänsterpartiet",
    leader: "Nooshi Dadgostar",
    color: "#8f2638",
    block: "Opposition",
    filters: ["valfard", "klimat", "ekonomi"],
    foundation: "Socialistiskt, feministiskt och antirasistiskt parti på ekologisk grund: jämlikhet, gemensamt ägande, välfärd utan vinstjakt och demokratisk makt över ekonomin.",
    scenario: {
      image: "assets/scenarier/vansterpartiet-scenario.jpg",
      alt: "Sverige med kooperativ, offentliga bostäder, gemensam energi, välfärd och grön kollektivtrafik.",
      title: "Jämlikhet före vinstintresse",
      summary: "Sverige blir mer omfördelande och demokratiserat ekonomiskt: offentliga och gemensamma lösningar tränger undan vinstlogik i välfärd, bostäder, energi och arbetsliv.",
      points: [
        "Offentlig välfärd, bostadspolitik och gemensamt ägande byggs ut.",
        "Arbetstagarmakt, kortare arbetstid och ekonomisk jämlikhet prioriteras.",
        "Klimatomställning drivs med social rättvisa som villkor."
      ]
    },
    pitch: "Vill minska ekonomiska klyftor, stoppa vinstjakt i välfärden och driva klimatomställning med jämlikhetsfokus.",
    tags: ["jämlikhet", "välfärd", "klimat", "arbetsliv"],
    stances: { "Offentlig välfärd": 10, "Marknad/skatt": 2, "Klimatomställning": 8 },
    ai: "Vill att AI-vinster ska komma anställda och medborgare till del, med konsekvensanalyser mot diskriminering, digitalt utanförskap och nedskärningar.",
    cooperation: "Söker främst samarbete med S och MP och kan även behöva hitta former med C för att få majoritet.",
    watch: ["C:s hållning till V i regering eller budgetunderlag", "Hur mycket inflytande partiet kräver"]
  },
  {
    short: "C",
    name: "Centerpartiet",
    leader: "Elisabeth Thand Ringqvist",
    color: "#1d7a5c",
    block: "Opposition",
    filters: ["klimat", "ekonomi", "valfard"],
    foundation: "Grön liberal decentralism: individens självbestämmande, företagande, landsbygd, klimat genom innovation och beslut nära människor.",
    scenario: {
      image: "assets/scenarier/centerpartiet-scenario.jpg",
      alt: "Decentraliserat Sverige med byar, gårdar, småföretag, grön energi, digital infrastruktur och regionala städer.",
      title: "Hela landet som grön tillväxtzon",
      summary: "Sverige blir mer decentraliserat, företagsamt och grönt: landsbygd, småföretag, lokal service och elektrifierad industri binds ihop av infrastruktur och valfrihet.",
      points: [
        "Företagande, jobb och lägre trösklar betonas i hela landet.",
        "Klimatpolitiken kopplas till innovation, el, industri och transporter.",
        "Lokal service, digital infrastruktur och landsbygd får större vikt."
      ]
    },
    pitch: "Driver grön liberal politik med fokus på företagande, landsbygd, decentralisering och klimat.",
    tags: ["landsbygd", "företag", "klimat", "välfärd"],
    stances: { "Offentlig välfärd": 6, "Marknad/skatt": 7, "Klimatomställning": 8 },
    ai: "Vill se innovation, öppna data och utbildning, men drar en tydlig integritetsgräns mot biometrisk massövervakning och godtycklig AI-användning.",
    cooperation: "Kan bli vågmästare i ett S-lett skifte, men relationen till V är den stora friktionspunkten.",
    watch: ["Om partiet kan ingå i eller stödja ett underlag där V behövs", "Hur tydligt partiet binder sig före valet"]
  },
  {
    short: "KD",
    name: "Kristdemokraterna",
    leader: "Ebba Busch",
    color: "#294f86",
    block: "Tidö",
    filters: ["valfard", "trygghet", "ekonomi"],
    foundation: "Kristdemokrati: människovärde, familj, civilsamhälle, subsidiaritet, förvaltarskap och solidaritet med fokus på vård, äldre och trygghet.",
    scenario: {
      image: "assets/scenarier/kristdemokraterna-scenario.jpg",
      alt: "Sverige med familjer, äldreomsorg, vårdcentral, civilsamhälle, lekplatser och lokalt ansvar.",
      title: "Omsorg nära människan",
      summary: "Sverige formas kring familj, omsorg och civilsamhälle: vård, äldreomsorg, trygghet och lokala gemenskaper blir mer centrala än stora systemlösningar.",
      points: [
        "Vård och äldreomsorg ges tydligare ansvar, tillgänglighet och värdighet.",
        "Familj, föreningsliv och civilsamhälle ses som bärande samhällsinstitutioner.",
        "Subsidiaritet: beslut ska tas så nära människan som möjligt."
      ]
    },
    pitch: "Profilerar sig på sjukvård, äldre, familjepolitik, trygghet och ett värderingsbaserat borgerligt perspektiv.",
    tags: ["vård", "äldre", "familj", "trygghet"],
    stances: { "Offentlig välfärd": 7, "Marknad/skatt": 6, "Klimatomställning": 4 },
    ai: "Driver digitalisering med hjärta: AI ska kapa byråkrati, frigöra tid för mänskliga möten och stärka vård, äldreomsorg och kommunal service.",
    cooperation: "Naturlig del av Tidösamarbetet tillsammans med M, L och SD.",
    watch: ["Spärrläget", "Vilken tyngd vårdfrågan får mot kriminalitet och ekonomi"]
  },
  {
    short: "L",
    name: "Liberalerna",
    leader: "Simona Mohamsson",
    color: "#3d78bf",
    block: "Tidö",
    filters: ["klimat", "migration", "ekonomi"],
    foundation: "Socialliberalism: frihet genom kunskap, rättsstat, integration, jämställdhet, EU och statligt ansvar för likvärdig skola och möjligheter.",
    scenario: {
      image: "assets/scenarier/liberalerna-scenario.jpg",
      alt: "Sverige med skola, bibliotek, universitet, rättsstat, forskning, Europa-kopplingar och olika livsvägar.",
      title: "Kunskap som frihetsmotor",
      summary: "Sverige byggs runt skola, bildning och rättsstat: staten ska ge människor verktyg att bli fria, medan internationalism, EU och teknikoptimism driver framtidstro.",
      points: [
        "Skola, studiero, läsning och lärarauktoritet blir frihetsfrågor.",
        "Rättsstat, jämställdhet och skydd mot förtryck får stark profil.",
        "EU, forskning, innovation och säkerhetspolitisk förankring betonas."
      ]
    },
    pitch: "Sätter skolan först, driver integration, liberal rättsstat, EU-linje och teknikoptimistisk klimatpolitik.",
    tags: ["skola", "integration", "EU", "klimat"],
    stances: { "Offentlig välfärd": 5, "Marknad/skatt": 7, "Klimatomställning": 7 },
    ai: "Framstegsoptimistisk linje med fokus på nationell AI-strategi, livslångt lärande, omskolning samt skydd mot cyberhot och desinformation.",
    cooperation: "Ingår i Tidöregeringen. Partiets spärrläge och syn på SD:s roll är centralt efter valet.",
    watch: ["Om partiet når över fyra procent", "Hur partiet hanterar SD i regeringsfrågan"]
  },
  {
    short: "MP",
    name: "Miljöpartiet",
    leader: "Amanda Lind och Daniel Helldén",
    color: "#2f8a45",
    block: "Opposition",
    filters: ["klimat", "valfard", "migration"],
    foundation: "Grön ideologi: liv inom planetens gränser, solidaritet med människor, natur och framtida generationer, klimat, biologisk mångfald och jämlikhet.",
    scenario: {
      image: "assets/scenarier/miljopartiet-scenario.jpg",
      alt: "Grönt Sverige med spårtrafik, cyklar, sol- och vindkraft, våtmarker, biologisk mångfald och cirkulära verkstäder.",
      title: "Samhälle inom planetens gränser",
      summary: "Sverige ställs om ekologiskt och socialt: klimat, natur, transporter, mat, energi och välfärd organiseras för att rymmas inom planetens gränser.",
      points: [
        "Klimat, biologisk mångfald och ren miljö blir överordnade styrprinciper.",
        "Städer, transporter och energi görs mer fossilfria och resurseffektiva.",
        "Jämlikhet, fred och internationell solidaritet kopplas till omställningen."
      ]
    },
    pitch: "Har klimat och natur som kärna, kombinerat med jämlikhet, välfärd och en mer human migrationspolitik.",
    tags: ["klimat", "natur", "jämlikhet", "migration"],
    stances: { "Offentlig välfärd": 8, "Marknad/skatt": 4, "Klimatomställning": 10 },
    ai: "Vill ha grön AI-politik med transparens, mänskliga rättigheter, digital suveränitet, energieffektiv AI och AI som verktyg för klimat och natur.",
    cooperation: "Trolig partner i ett S-lett regeringsskifte och nära V i flera klimat- och välfärdsfrågor.",
    watch: ["Hur klimatfrågan vägs mot ekonomi och energi", "Relationen till C och S i ett regeringsunderlag"]
  }
];

const grid = document.querySelector("#party-grid");
const chips = document.querySelectorAll(".chip");
const selectA = document.querySelector("#compare-a");
const selectB = document.querySelector("#compare-b");
const compareOutput = document.querySelector("#compare-output");
const compassForm = document.querySelector("#compass-form");
const compassResult = document.querySelector("#compass-result");
const answeredCount = document.querySelector("#answered-count");
const progressBar = document.querySelector("#progress-bar");
const resetCompass = document.querySelector("#reset-compass");
const scenarioFeature = document.querySelector("#scenario-feature");
const scenarioList = document.querySelector("#scenario-list");

const compassQuestions = [
  {
    id: "welfare",
    title: "Hur ska välfärden utvecklas?",
    options: [
      { label: "Mer skattefinansierad välfärd och mindre privat vinstuttag", weights: { V: 3, S: 2, MP: 2, SD: 1, KD: 1 } },
      { label: "Stärk vård och skola, men behåll blandade utförare", weights: { S: 2, KD: 2, C: 2, L: 1, M: 1 } },
      { label: "Mer valfrihet, effektivitet och tydligare krav på resultat", weights: { M: 3, L: 2, C: 2, KD: 1 } }
    ]
  },
  {
    id: "tax",
    title: "Vilken ekonomisk linje ligger närmast dig?",
    options: [
      { label: "Höginkomsttagare och kapital bör bidra mer", weights: { V: 3, S: 2, MP: 1 } },
      { label: "Balans mellan investeringar i välfärd och ansvar för statsfinanserna", weights: { S: 2, C: 2, KD: 1, L: 1 } },
      { label: "Lägre skatter och starkare drivkrafter för arbete och företag", weights: { M: 3, C: 2, L: 2, KD: 1, SD: 1 } }
    ]
  },
  {
    id: "climate",
    title: "Hur viktig ska klimatomställningen vara?",
    options: [
      { label: "Mycket hög prioritet, även om det kräver nya regler och investeringar", weights: { MP: 3, V: 2, C: 2, S: 1 } },
      { label: "Viktig, men måste vägas mot ekonomi, energi och hushållens kostnader", weights: { S: 2, L: 2, C: 1, M: 1, KD: 1 } },
      { label: "Klimatpolitik ska vara försiktig och inte driva upp kostnader i onödan", weights: { SD: 3, M: 2, KD: 2 } }
    ]
  },
  {
    id: "crime",
    title: "Vad är viktigast i kriminalpolitiken?",
    options: [
      { label: "Hårdare straff, fler poliser och kraftigare verktyg mot gäng", weights: { M: 3, SD: 3, KD: 2, L: 1, S: 1 } },
      { label: "Både hårdare tag och mer social prevention", weights: { S: 3, L: 2, C: 1, KD: 1 } },
      { label: "Förebyggande arbete, skola och sociala insatser bör väga tyngst", weights: { V: 3, MP: 2, S: 1, C: 1 } }
    ]
  },
  {
    id: "migration",
    title: "Vilken migrationslinje föredrar du?",
    options: [
      { label: "Betydligt stramare migration och högre krav för integration", weights: { SD: 3, M: 2, KD: 2, L: 1 } },
      { label: "Stram men rättssäker migration med fokus på arbete och integration", weights: { S: 2, L: 2, C: 1, M: 1 } },
      { label: "Mer human politik och större ansvar för skyddssökande", weights: { MP: 3, V: 2, C: 1, S: 1 } }
    ]
  },
  {
    id: "school",
    title: "Vad bör skolpolitiken prioritera?",
    options: [
      { label: "Kunskapskrav, studiero, lärarauktoritet och tydligare uppföljning", weights: { L: 3, M: 2, KD: 2, S: 1 } },
      { label: "Likvärdighet, fler vuxna och minskad segregation", weights: { S: 3, V: 2, MP: 1, L: 1 } },
      { label: "Valfrihet, små skolor och bättre villkor i hela landet", weights: { C: 3, KD: 1, M: 1, L: 1 } }
    ]
  },
  {
    id: "countryside",
    title: "Hur ser du på stad och landsbygd?",
    options: [
      { label: "Landsbygd, jordbruk och lokal service behöver tydligare prioritet", weights: { C: 3, SD: 2, KD: 1, M: 1 } },
      { label: "Hela landet ska fungera, men välfärden är viktigast", weights: { S: 2, V: 1, KD: 1, C: 1 } },
      { label: "Städer och regioner behöver driva klimatsmart tillväxt", weights: { MP: 2, L: 2, C: 1, M: 1 } }
    ]
  },
  {
    id: "government",
    title: "Vilket regeringsunderlag känns mest rimligt?",
    options: [
      { label: "Fortsatt borgerligt/Tidö-nära samarbete", weights: { M: 3, KD: 2, SD: 2, L: 1 } },
      { label: "Ett S-lett regeringsskifte med grönt och vänsterinriktat stöd", weights: { S: 3, MP: 2, V: 2, C: 1 } },
      { label: "Mittenlösningar och blocköverskridande kompromisser", weights: { C: 3, L: 2, S: 1, M: 1 } }
    ]
  },
  {
    id: "energy",
    title: "Vilken energipolitik föredrar du?",
    options: [
      { label: "Bygg ut kärnkraft och stabil elproduktion snabbare", weights: { M: 3, KD: 3, L: 2, SD: 2 } },
      { label: "Kombinera planerbar el med förnybart och effektivisering", weights: { S: 2, C: 2, L: 1, M: 1 } },
      { label: "Satsa främst på förnybart, energisparande och snabb klimatomställning", weights: { MP: 3, V: 2, C: 1, S: 1 } }
    ]
  },
  {
    id: "eu",
    title: "Vilken syn på EU ligger närmast dig?",
    options: [
      { label: "Sverige bör samarbeta mer i EU kring klimat, säkerhet och ekonomi", weights: { L: 3, C: 2, MP: 2, S: 1, M: 1 } },
      { label: "EU är viktigt, men Sverige ska vara återhållsamt med ny makt till Bryssel", weights: { M: 2, KD: 2, S: 1, C: 1 } },
      { label: "Sverige bör försvara mer nationellt självbestämmande mot EU", weights: { SD: 3, V: 2, KD: 1 } }
    ]
  },
  {
    id: "defense",
    title: "Vad bör Sverige prioritera i försvar och säkerhet?",
    options: [
      { label: "Stärk totalförsvaret snabbt och lägg mer resurser på militär förmåga", weights: { M: 3, KD: 2, SD: 2, L: 2, S: 1 } },
      { label: "Kombinera starkt försvar med diplomati, beredskap och civil säkerhet", weights: { S: 3, C: 2, MP: 1, L: 1 } },
      { label: "Mer fokus på fredsarbete, civil beredskap och klimatrelaterade risker", weights: { MP: 3, V: 2, S: 1 } }
    ]
  },
  {
    id: "housing",
    title: "Hur bör bostadspolitiken förändras?",
    options: [
      { label: "Bygg fler hyresrätter och pressa boendekostnader med aktiv politik", weights: { V: 3, S: 2, MP: 1 } },
      { label: "Förenkla byggande och korta planprocesser så fler bostäder kommer fram", weights: { C: 3, M: 2, L: 2, KD: 1 } },
      { label: "Stärk ägande, trygghet i bostadsområden och familjers boendemöjligheter", weights: { KD: 3, M: 2, SD: 2, S: 1 } }
    ]
  },
  {
    id: "work",
    title: "Vad är viktigast för arbetsmarknaden?",
    options: [
      { label: "Starkare anställningstrygghet, bättre villkor och högre löner i välfärden", weights: { V: 3, S: 2, MP: 1 } },
      { label: "Fler ska arbeta genom utbildning, matchning och krav på egen försörjning", weights: { S: 2, L: 2, M: 1, KD: 1 } },
      { label: "Sänk trösklarna för företag att anställa och växa", weights: { C: 3, M: 3, L: 2, KD: 1 } }
    ]
  },
  {
    id: "healthcare",
    title: "Vad bör vara huvudspåret för vården?",
    options: [
      { label: "Mer nationell styrning, kortare köer och tydligare ansvar", weights: { KD: 3, M: 2, L: 1, S: 1 } },
      { label: "Mer resurser till personal, vårdplatser och jämlik vård i hela landet", weights: { S: 3, V: 2, MP: 1, C: 1 } },
      { label: "Bättre tillgänglighet med både offentliga och privata utförare", weights: { M: 2, C: 2, L: 2, KD: 1 } }
    ]
  },
  {
    id: "elderly",
    title: "Hur ska äldreomsorgen stärkas?",
    options: [
      { label: "Mer personal, bättre arbetsvillkor och mindre vinstjakt", weights: { V: 3, S: 2, MP: 1 } },
      { label: "Större trygghet, fast omsorgskontakt och mer familjenära stöd", weights: { KD: 3, SD: 2, M: 1, S: 1 } },
      { label: "Mer valfrihet och bättre uppföljning av kvalitet", weights: { M: 2, L: 2, C: 2, KD: 1 } }
    ]
  },
  {
    id: "democracy",
    title: "Vilken demokratifråga väger tyngst?",
    options: [
      { label: "Stärk rättsstat, domstolar, medier och skydd mot korruption", weights: { L: 3, C: 2, MP: 2, S: 1 } },
      { label: "Mer ordning, ansvar och tydligare krav på myndigheter", weights: { M: 2, KD: 2, SD: 2, S: 1 } },
      { label: "Öka jämlikhet, inflytande och skydd för civilsamhälle och minoriteter", weights: { V: 3, MP: 2, S: 1, C: 1 } }
    ]
  },
  {
    id: "culture",
    title: "Hur ser du på kultur och public service?",
    options: [
      { label: "Kultur och public service ska ha stark offentlig finansiering och armlängds avstånd", weights: { MP: 3, V: 2, S: 2, L: 1 } },
      { label: "Kulturen är viktig men behöver tydliga prioriteringar och ansvar", weights: { C: 2, KD: 2, S: 1, M: 1 } },
      { label: "Kulturpolitiken bör fokusera mer på kärnuppdrag och nationell sammanhållning", weights: { SD: 3, M: 2, KD: 2 } }
    ]
  },
  {
    id: "transport",
    title: "Vad bör transportpolitiken prioritera?",
    options: [
      { label: "Mer kollektivtrafik, järnväg och minskade utsläpp från transporter", weights: { MP: 3, V: 2, S: 1, C: 1 } },
      { label: "Både väg och järnväg behövs för att hela landet ska fungera", weights: { C: 3, S: 2, KD: 1, M: 1 } },
      { label: "Bil, vägar och rimliga drivmedelskostnader måste prioriteras tydligare", weights: { SD: 3, M: 2, KD: 2 } }
    ]
  },
  {
    id: "ai",
    title: "Vilken AI-politik ligger närmast dig?",
    options: [
      { label: "Snabbare AI-införande för tillväxt, vård, skola och minskad byråkrati", weights: { M: 3, KD: 3, L: 2, SD: 1, C: 1 } },
      { label: "AI måste först styras av etik, arbetstagares trygghet, upphovsrätt och rättssäkerhet", weights: { S: 3, V: 2, MP: 2, C: 1 } },
      { label: "AI är viktigt, men massövervakning, utländsk datakontroll och Big Tech-makt måste begränsas", weights: { MP: 3, C: 3, V: 1, SD: 1, L: 1 } }
    ]
  }
];

const compassAnswers = {};
const importantQuestions = new Set();

function renderParties(filter = "alla") {
  grid.innerHTML = "";
  parties
    .filter((party) => filter === "alla" || party.filters.includes(filter))
    .forEach((party) => {
      const card = document.createElement("article");
      card.className = "party-card";
      card.style.setProperty("--party-color", party.color);
      card.innerHTML = `
        <div class="party-top">
          <div>
            <h3>${party.name}</h3>
            <p class="leader">${party.leader} · ${party.block}</p>
          </div>
          <span class="party-badge">${party.short}</span>
        </div>
        <p>${party.pitch}</p>
        <p class="party-foundation"><strong>Programkärna:</strong> ${party.foundation}</p>
        <div class="tags">${party.tags.map((tag) => `<span>${tag}</span>`).join("")}</div>
        <p class="ai-summary"><strong>AI:</strong> ${party.ai}</p>
        <div class="stance">
          ${Object.entries(party.stances)
            .map(([label, value]) => `
              <div class="meter">
                <span>${label}</span>
                <div class="bar" aria-label="${label}: ${value} av 10"><span style="--value:${value}"></span></div>
              </div>
            `)
            .join("")}
        </div>
      `;
      grid.append(card);
    });
}

function populateSelects() {
  parties.forEach((party, index) => {
    const optionA = new Option(`${party.short} · ${party.name}`, party.short);
    const optionB = new Option(`${party.short} · ${party.name}`, party.short);
    selectA.add(optionA);
    selectB.add(optionB);
    if (index === 0) optionA.selected = true;
    if (index === 1) optionB.selected = true;
  });
}

function renderCompare() {
  const selected = [selectA.value, selectB.value].map((short) => parties.find((party) => party.short === short));
  compareOutput.innerHTML = selected
    .map((party) => `
      <article class="compare-card" style="--party-color:${party.color}">
        <h3>${party.name}</h3>
        <p>${party.pitch}</p>
        <p><strong>Programkärna:</strong> ${party.foundation}</p>
        <p><strong>Bildligt scenario:</strong> ${party.scenario.summary}</p>
        <p><strong>Samarbete:</strong> ${party.cooperation}</p>
        <ul>
          ${party.watch.map((item) => `<li>${item}</li>`).join("")}
        </ul>
      </article>
    `)
    .join("");
}

let activeScenario = parties[0].short;

function renderScenario(short = activeScenario) {
  const party = parties.find((item) => item.short === short) || parties[0];
  activeScenario = party.short;
  scenarioFeature.style.setProperty("--party-color", party.color);
  scenarioFeature.innerHTML = `
    <img src="${party.scenario.image}" alt="${party.scenario.alt}" width="1672" height="941" loading="lazy" decoding="async">
    <div class="scenario-feature-body">
      <div class="scenario-title-row">
        <div>
          <p class="eyebrow">${party.name}</p>
          <h3>${party.scenario.title}</h3>
        </div>
        <span class="party-badge" style="--party-color:${party.color}">${party.short}</span>
      </div>
      <p class="scenario-summary">${party.scenario.summary}</p>
      <ul class="scenario-points">
        ${party.scenario.points.map((point) => `<li>${point}</li>`).join("")}
      </ul>
    </div>
  `;

  scenarioList.querySelectorAll(".scenario-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.short === party.short);
    button.setAttribute("aria-pressed", button.dataset.short === party.short ? "true" : "false");
  });
}

function renderScenarioList() {
  scenarioList.innerHTML = parties
    .map((party) => `
      <button class="scenario-button" type="button" data-short="${party.short}" style="--party-color:${party.color}" aria-pressed="false">
        <span class="party-badge">${party.short}</span>
        <span>
          <strong>${party.name}</strong>
          <span>${party.scenario.title}</span>
        </span>
      </button>
    `)
    .join("");

  scenarioList.addEventListener("click", (event) => {
    const button = event.target.closest(".scenario-button");
    if (!button) return;
    renderScenario(button.dataset.short);
  });
}

function renderCompassQuestions() {
  compassForm.innerHTML = compassQuestions
    .map((question, questionIndex) => `
      <fieldset class="question-card">
        <div class="question-top">
          <legend>
            <span>Fråga ${questionIndex + 1}</span>
            ${question.title}
          </legend>
          <label class="important-toggle">
            <input type="checkbox" name="important-${question.id}" data-important="${question.id}">
            <span>Extra viktig</span>
          </label>
        </div>
        <div class="answer-grid">
          ${question.options
            .map((option, optionIndex) => `
              <label class="answer-option">
                <input type="radio" name="${question.id}" value="${optionIndex}">
                <span>${option.label}</span>
              </label>
            `)
            .join("")}
        </div>
      </fieldset>
    `)
    .join("");
}

function calculateCompassScores() {
  const scores = Object.fromEntries(parties.map((party) => [party.short, 0]));
  const answered = Object.entries(compassAnswers);

  answered.forEach(([questionId, optionIndex]) => {
    const question = compassQuestions.find((item) => item.id === questionId);
    const option = question.options[Number(optionIndex)];
    const multiplier = importantQuestions.has(questionId) ? 2 : 1;
    Object.entries(option.weights).forEach(([short, points]) => {
      scores[short] += points * multiplier;
    });
  });

  const maxPossible = answered.reduce((total, [questionId]) => {
    return total + (importantQuestions.has(questionId) ? 6 : 3);
  }, 0);
  const ranked = parties
    .map((party) => ({
      ...party,
      score: scores[party.short],
      percent: maxPossible ? Math.round((scores[party.short] / maxPossible) * 100) : 0
    }))
    .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name, "sv"));

  return { ranked, answeredCount: answered.length };
}

function renderCompassResult() {
  const result = calculateCompassScores();
  const progress = Math.round((result.answeredCount / compassQuestions.length) * 100);
  answeredCount.textContent = `${result.answeredCount} av ${compassQuestions.length} svarade`;
  progressBar.style.width = `${progress}%`;

  if (result.answeredCount < 6) {
    compassResult.innerHTML = `
      <h3>Ditt resultat visas här</h3>
      <p>Svara på minst sex frågor för att få en första matchning.</p>
    `;
    return;
  }

  const topParties = result.ranked.slice(0, 3);
  compassResult.innerHTML = `
    <h3>Närmast dina svar</h3>
    <div class="result-list">
      ${topParties
        .map((party, index) => `
          <article class="result-item" style="--party-color:${party.color}">
            <div class="result-rank">${index + 1}</div>
            <div>
              <strong>${party.short} · ${party.name}</strong>
              <p>${party.percent}% matchning i guiden</p>
              <div class="result-meter"><span style="width:${party.percent}%"></span></div>
            </div>
          </article>
        `)
        .join("")}
    </div>
    <p class="result-note">
      Läs partiernas egna program innan du bestämmer dig. En valkompass fångar inte kandidater,
      lokala frågor eller alla nyanser i partiernas faktiska förslag.
    </p>
  `;
}

function wireCompass() {
  compassForm.addEventListener("change", (event) => {
    if (event.target.matches('input[type="radio"]')) {
      compassAnswers[event.target.name] = event.target.value;
      renderCompassResult();
    }

    if (event.target.matches("[data-important]")) {
      const questionId = event.target.dataset.important;
      if (event.target.checked) {
        importantQuestions.add(questionId);
      } else {
        importantQuestions.delete(questionId);
      }
      renderCompassResult();
    }
  });

  resetCompass.addEventListener("click", () => {
    Object.keys(compassAnswers).forEach((key) => delete compassAnswers[key]);
    importantQuestions.clear();
    compassForm.reset();
    renderCompassResult();
  });
}

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    chips.forEach((item) => item.classList.remove("active"));
    chip.classList.add("active");
    renderParties(chip.dataset.filter);
  });
});

selectA.addEventListener("change", renderCompare);
selectB.addEventListener("change", renderCompare);

renderParties();
renderScenarioList();
renderScenario();
populateSelects();
renderCompare();
renderCompassQuestions();
wireCompass();
renderCompassResult();

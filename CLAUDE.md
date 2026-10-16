# HR-dashbord – people analytics porteføljeprosjekt

## Om prosjektet

Et people analytics-dashbord bygget som porteføljeprosjekt. Målet er å vise frem
ferdigheter til arbeidsgivere ved søknad på HR- og people analytics-roller i
mindre selskaper. Dashbordet skal derfor være ryddig, forståelig og vise
relevante HR-innsikter, ikke bare teknikk.

## Teknologi (stack)

- **Python** – programmeringsspråket
- **pandas** – for å jobbe med tabelldata (tilsvarer regneark i Excel)
- **Streamlit** – for å lage selve dashbordet som en nettside

Hold oss til denne stacken. Ikke legg til nye biblioteker uten å spørre først.

## Data

- Alle data er **syntetiske** (oppdiktede) – ingen ekte personopplysninger.
- Fiktivt **norsk tech-selskap** med ca. **230 ansatte** fordelt på **7 team**.
- Teamnavnene skal skrives **nøyaktig slik** overalt i data og kode (små
  bokstaver, samme stavemåte). Størrelsene er omtrentlige:

  | Team                | Ca. antall ansatte |
  |---------------------|-------------------:|
  | `teknologi`         | 85 |
  | `produktutvikling`  | 20 |
  | `salg`              | 40 |
  | `kundesuksess`      | 45 |
  | `markedsføring`     | 18 |
  | `økonomi og hr`     | 16 |
  | `ledergruppen`      | 4  |

- `ledergruppen` skal **bevisst ha færre enn 5 personer**, slik at dashbordet
  viser et eksempel på at sykefravær og eNPS skjules av personvernhensyn (se
  «Personvern» under).
- Dataene skal være realistiske for en norsk kontekst (kroner, norske
  stillingstitler, arbeidsforhold osv.).
- Ansatte identifiseres **kun med ansatt-ID**. Datasettet skal aldri inneholde
  navn.

## Personvern (gjelder alltid)

- **Prinsipp:** Sensitive tall vises bare i faste, ikke-overlappende visninger.
  Fritt filter brukes bare på tall som ikke er sensitive.
  - **Sensitive tall:** sykefravær, eNPS (inkl. svarandel), turnoverfordelingen
    (uønsket og sluttårsak), kostnad ved uønsket turnover (bygger på lønn) og
    rekrutteringstall (tid til ansettelse, andel strukturert, kvalitet på
    ansettelser, bruk av tilleggsmetoder) og forfremmelser (ledelsens vurdering
    av enkeltpersoner).
  - **Ikke sensitive:** totalt antall avganger, total turnover, «kontrakt
    utløpt» (antall) og bemanning (antall ansatte, plan, ansettelser, avganger).
  - To visninger som overlapper (to perioder, to utvalg av team), kan trekkes
    fra hverandre og avsløre en liten gruppe. Derfor finnes hvert sensitivt tall
    i én fast visning per periode og team.
- Dashbordet skal **aldri vise data om enkeltpersoner** – bare tall for grupper
  (team, avdeling, aldersgruppe osv.).
- **Femregelen:** grupper med **færre enn 5** skjules for:
  - **sykefravær** – antall ansatte i gruppa
  - **eNPS** – `antall_svar` (ikke teamstørrelsen)
  - **turnover per team**:
    - totalt antall avganger og antall `kontrakt utløpt` vises alltid, også for
      ledergruppen – at noen har sluttet er ikke sensitivt
    - team med færre enn 5 ansatte (snitt i perioden): alt annet skjules
    - fordeling på **uønsket og sluttårsak** (frivillig, ufrivillig, pensjon)
      vises bare når teamet har **minst 5 avganger** i perioden; ellers bare for
      hele selskapet. Det sensitive er ledelsens vurdering av enkeltpersoner.
    - **Avganger per måned** vises bare som total, aldri fordelt på uønsket
      eller sluttårsak (én måned er ofte én person).
  - **kvalitet på ansettelser** – både per team, per rekrutteringsmetode og per
    nivå (antall ansatte som inngår i beregningen)
  - **tid til ansettelse og andel strukturert** – median og andel skjules når
    de bygger på under 5 ansettelser (totalt, per team og per kvartal)
  - **median tid til tiltredelse** på Bemanning – skjules under 5 ansettelser
  - **antall tilleggsmetoder** – under 5 skjules, også for hele selskapet
    (ellers kan «1 personlighetstest» peke mot én kandidat)
  - **trendgrafer** for sykefravær (per måned) og eNPS (per kvartal) –
    femregelen gjelder **per punkt** (se under)
  - **utvikling** (siden Utvikling): opplæring og 1:1 skjules for team med
    under 5 ansatte (snitt), og jevnlige 1:1 når under 5 var ansatt hele
    perioden. Intern besettelsesgrad vises med minst 5 besatte stillinger.
    **Forfremmelser** er sensitive: vises bare med minst 5 interne endringer og
    minst 5 ansatte (samme logikk som fordelingen av turnover).
  - **1:1 per team er i praksis tall om én leder.** Siden sier det åpent, og
    tallene skal brukes til samtale med lederen, ikke til rangering.
  
  Dette gjelder også når filtre gjør en gruppe mindre enn 5.
- **Sekundær prikking:** en skjult gruppe må ikke kunne regnes ut som «total minus
  de synlige gruppene». For **sensitive tall** – sykefravær, eNPS (inkl.
  svarandel), turnoverfordelingen (uønsket og sluttårsak), kvalitet på
  ansettelser og forfremmelser (`utenfor_forfremmelser()`) – gjelder:
  - Hvis de skjulte teamene **til sammen** er under 5 (ansatte, svar eller
    avganger), holdes de **utenfor totalen**. Er de til sammen 5 eller flere,
    kan totalen ta med alle (de kan ikke skilles fra hverandre).
  - Totaler som holder noen utenfor, merkes tydelig, f.eks. «Hele selskapet
    (uten ledergruppen)».
  - Gjelder også når filteret blander skjulte og synlige team, og for perioden
    det sammenlignes med (samme team holdes utenfor i begge perioder).
  - **Ikke sensitivt** – totalen tar alltid med alle: totalt antall avganger,
    total turnover og bemanning.
  - Regelen ligger i `sekundar_prikking()` i `beregninger.py`. For kvalitet på
    ansettelser prikkes hver celle (nivå × mål) for seg i
    `kvalitet_per_nivaa_prikket()`, og cellen vises som «skjult (sekundær
    prikking)».
  - Sekundær prikking gjelder **totaler** (visningen «hele selskapet»). Når ett
    team er valgt, gjelder vanlig femregel for den viste perioden.
  - Prikkingen er **lik i alle periodevalg**: et team som må holdes utenfor i én
    av de faste periodene (eller periodene det sammenlignes med), holdes utenfor
    i alle (`alle_sammenligningsperioder()`).
- **Begrenset filter på sider med sensitive tall** (turnover, sykefravær,
  rekruttering, eNPS, utvikling), `vis_filtre_sensitiv()` i `filtre.py`:
  - **Team:** enten «Hele selskapet» eller **ett team om gangen** – ikke fritt
    flervalg (to utvalg som skiller seg med én liten gruppe kan trekkes fra
    hverandre).
  - **Periode:** bare **to faste, ikke-overlappende perioder** – siste 12 mnd
    og forrige 12 mnd (`FASTE_PERIODER`) – ikke fri månedsglider og ikke
    perioder som overlapper (som siste 24 mnd eller kalenderår).
  - Bare **Bemanning** har fritt filter (`vis_filtre()`), fordi ingen av
    tallene der er sensitive (medianen for tiltredelse følger femregelen).
- **Trendgrafer** for sykefravær (per måned) og eNPS (per kvartal, også grafene
  for kobling mot langtidsfravær) viser **alltid hele dataperioden**
  (`TRENDPERIODE`), uansett periodevalg – én fast visning. Femregelen gjelder
  **per punkt**: et punkt med under 5 (ansatte eller svar) vises ikke, og små
  team holdes utenfor punktet når de til sammen er under 5
  (`sykefravaer_per_maaned()`, `langtid_per_kvartal()`).
- **Hva reglene ikke gjør:** Faste perioder, femregelen og sekundær prikking reduserer risikoen for at tall om små grupper kan utledes, men de hindrer den ikke. Ingen tekniske regler kan helt hindre det i et interaktivt verktøy. Den som kjenner organisasjonen, kan dessuten koble tallene med egen kunnskap, for eksempel om hvem som sluttet i en bestemt måned. Den viktigste beskyttelsen er derfor tilgangsstyring: i drift skal bare HR-ledelse og ledergruppen ha tilgang. Skriv det like ærlig overalt (README, dashbordet): aldri at reglene «hindrer» eller «sikrer» noe.
- **Lønn** vises aldri per team. Den brukes bare i kostnadsberegningen, og
  kostnaden vises bare i **én fast visning**: hele selskapet, **siste 12 mnd**
  (`er_siste_12()`), sammenlignet med forrige 12 mnd (den andre faste perioden),
  avrundet til nærmeste 0,1 mill. kr (`millioner()`), og bare med minst 5
  uønskede avganger. Endringen regnes på de avrundede tallene
  (`endring_millioner()`), så den ikke avslører mer enn tallene selv.
- **Stilling** blir aldri et filter i dashbordet (stilling + team kan peke ut
  én person).
- Selv om dataene er syntetiske, skal dashbordet bygges som om de var ekte.

## Presentasjon i dashbordet (gjelder alltid)

- **Vis alltid n ved siden av prosenter for små grupper**, f.eks.
  «12,5 % (1 av 8)». Én person mer eller mindre kan flytte en liten gruppe
  mange prosentpoeng, og leseren må kunne se det.
- **Avrunding som i Excel:** tall som vises, rundes med 5 opp (bort fra null),
  som AVRUND i Excel – 31,25 % vises som 31,3 %. Pythons `round()` runder 5 mot
  nærmeste partall og skal **ikke** brukes til visning. Bruk alltid
  `avrund()` (eller `prosent()`, `endring_pp()`, `kroner()`) fra `beregninger.py`.
- **Forskning om rekrutteringsmetoder:** validitetstall vises i en egen
  forskningsboks.
  - **Sackett mfl. (2022), tabell 3** (doi.org/10.1037/apl0000994) er
    **verifisert av brukeren** og vises med kilde og DOI-lenke.
  - **Schmidt og Hunter (1998)** vises ved siden av, så endringen i forskningen
    synes. Kilde: «gjengitt i Sackett mfl. (2022), tabell 3» – verifisert av
    brukeren.
  - Nye forskningstall skrives aldri inn uten verifisering; tall som ikke er
    funnet vises som «ikke fylt inn». Boksen nevner at noen forskere mener
    estimatene i Sackett mfl. er for lave.
  - Case study kobles til nærmeste kategori, arbeidsprøve (work sample).
    Personlighet vises for alle fem Big Five-trekk, med merknad om at
    relevansen avhenger av stillingen.
  - Siden skal også si at et selskap på denne størrelsen ikke kan evaluere
    metoder statistisk på egne data alene, og ha en personvernmerknad om testbruk.
- **Tankestrek:** bruk aldri lang tankestrek (—). Bruk kort tankestrek med
  mellomrom på hver side ( – ), og bruk den **sparsomt** – skriv heller om
  setningen (punktum, komma, «fordi», «så») der det blir naturlig. Gjelder all
  tekst i dashbordet og README. Negative tall bruker minustegn (−14). Tekst
  brukeren selv har formulert, gjengis ordrett.
- **Intervaller og perioder skrives med bindestrek** (-) uten mellomrom, ikke
  tankestrek: 10-15 %, 50-500 ansatte, 01.10.2025-30.09.2026 (Tanias valg
  16.10.2026, fordi tankestreken ser lang ut i skriften). «–» brukes bare alene,
  som tegn for «ingen verdi». Sjekkes av en test.
- **En-endinger, ikke a-endinger:** «pilen», «linjen», «filen», «mappen», ikke
  «pila», «linja», «fila», «mappa». Gjelder all tekst i dashbordet, README,
  CLAUDE.md og kommentarer i koden. Sjekkes av en test.
- **Dataene er syntetiske – si det tydelig.** Både dashbordet og README skal
  klart opplyse at dataene er oppdiktet og konstruert for å illustrere
  metodikk, og at de **ikke bygger på data fra noe ekte selskap**. Teksten i
  dashbordet (`SYNTETISK_MERKNAD`, vist på alle sider): «Alle tall i dette
  dashbordet er oppdiktet og konstruert for å illustrere metodikk, og bygger ikke
  på data fra noe ekte selskap.»
- **Skjulte tall i KPI-kort:** aldri tekst som verdi (lang tekst får stor tallskrift
  og blir kuttet). Bruk `skjult_kort()` i `utseende.py`: «–» som verdi og
  forklaringen i liten tekst under. En test sjekker at ingen verdi i et KPI-kort
  er lengre enn 12 tegn.

## Datamodell

Gjelder alle ark:
- Datoer skrives ÅÅÅÅ-MM-DD.
- Teamnavn skrives alltid med små bokstaver (se tabellen under «Data»).
- Alle metrikker beregnes i Python, og alltid for en valgt periode
  (periodestart og periodeslutt).
- `Datamodell.xlsx` er brukerens Excel-utkast og **fasit for de 20
  testradene**. Filen oppdateres ikke (den har derfor ikke de nye kolonnene).
  Python-versjonen følger denne beskrivelsen, ikke formlene i Excel-filen.
- `kontroller_mot_excel.py` regner testradene med **de samme funksjonene som
  dashbordet** (`beregninger.py`) og sammenligner med Excel. Hvert avvik skal
  ha en forklaring i skriptet (f.eks. snitt ansatte per månedsslutt, og tid til
  ansettelse = NaN fordi ingen av testradene ble ansatt i perioden).

### Ark: Ansatte (én rad per ansatt, også de som har sluttet)

| Kolonne | Type | Lovlige verdier | Merknad |
|---|---|---|---|
| `ansatt_id` | tekst | A001, A002 … | Eneste identifikator. Aldri navn. |
| `team` | tekst | de 7 teamnavnene | |
| `stilling` | tekst | fritekst | Aldri filter i dashbordet. |
| `ansettelsesform` | tekst | fast, midlertidig | |
| `stillingsprosent` | tall | 1-100 | |
| `årslønn` | tall (kr) | | **Faktisk** lønn (ikke omregnet til 100 %). Bare til kostnadsberegning, aldri vist per team. |
| `ansattdato` | dato | | |
| `sluttdato` | dato | | Tom = fortsatt ansatt. |
| `sluttårsak` | tekst | frivillig, ufrivillig, pensjon, kontrakt utløpt | Tom hvis ikke sluttet. |
| `uønsket` | tekst | ja, nei | Bare for dem som har sluttet. «ja» bare når sluttårsak = frivillig.* |
| `rekrutteringsmetode` | tekst | strukturert, ustrukturert | Tom = ansatt før rekrutteringsdata ble registrert. |
| `strukturert_intervju` | tekst | ja, nei | **ja ⟺ rekrutteringsmetode = strukturert.** Samme tomregel. |
| `case_study` | tekst | ja, nei | Tilleggsmetode. Vises som «case study». Bare ja for strukturerte ansettelser. Samme tomregel. |
| `personlighetstest` | tekst | ja, nei | Tilleggsmetode: Big Five (alle fem trekk). Bare **om** testen ble brukt – **aldri resultater** per trekk. Samme regler. |
| `evnetest` | tekst | ja, nei | Tilleggsmetode. Samme regler. |
| `utlysningsdato` | dato | | Samme tomregel. |
| `aksept_dato` | dato | | Samme tomregel. Må ligge mellom utlysningsdato og ansattdato. |
| `prøvetid_bestått` | tekst | ja, nei | Tom = ansatt før registrering, **eller** prøvetiden (6 mnd) er ikke over ennå. Python skiller de to ved hjelp av datoene (se under). |

\* Unntak som **ikke modelleres nå**: ved nedbemanning kan en ufrivillig avgang
også være uønsket.

**Slik tolkes tom `prøvetid_bestått`:**
- `rekrutteringsmetode` er tom → ansatt før rekrutteringsdata ble registrert.
- `ansattdato` + 6 måneder er etter periodeslutt → prøvetiden er ikke over ennå.

### Ark: Fravær (én rad per team per måned)

| Kolonne | Type | Merknad |
|---|---|---|
| `team` | tekst | |
| `måned` | tekst | ÅÅÅÅ-MM |
| `tapte_dagsverk_korttid` | tall | Fravær på 1-16 dager (arbeidsgiverperioden). |
| `tapte_dagsverk_langtid` | tall | Fravær over 16 dager. |
| `avtalte_dagsverk` | tall | **Lagres ikke, men regnes ut i Python fra Ansatte**: arbeidsdager i måneden × stillingsprosent, for alle som var ansatt i måneden. Ferie er *ikke* trukket fra, så fraværsprosenten blir litt lavere enn med NAVs metode. |

### Ark: Engasjement (én rad per team per kvartal)

| Kolonne | Type | Merknad |
|---|---|---|
| `team` | tekst | |
| `kvartal` | tekst | ÅÅÅÅ-K1 … K4 |
| `enps` | tall | −100 til 100 |
| `antall_svar` | tall | Femregelen bruker dette tallet. |
| `antall_invitert` | tall | Antall ansatte som fikk undersøkelsen (alle ansatte i teamet midt i kvartalet). Brukes til svarandel. |

### Ark: Bemanningsplan (én rad per team per måned)

| Kolonne | Type | Merknad |
|---|---|---|
| `team` | tekst | |
| `måned` | tekst | ÅÅÅÅ-MM |
| `planlagt_antall` | tall | Planlagt antall ansatte i teamet ved utgangen av måneden. |

Brukes til å vise **faktisk mot plan over tid**. Planen vokser gradvis gjennom
perioden.

### Ark: Definisjoner

| Kolonne | Merknad |
|---|---|
| `Metrikk` | Navnet på metrikken. |
| `Forklaring` | Hva den betyr, med kilde for antakelser (f.eks. 75 %). |
| `Resultat` | Kontrollverdi fra Excel, for å sjekke Python-tallene. |
| `iso_område` | Etter ISO 30414:2025, der rekruttering, mobilitet og turnover er egne områder. |

### Tabeller for kompetanseutvikling (bare CSV, ikke i Datamodell.xlsx)

**opplaering.csv** (én rad per opplæringsaktivitet)

| Kolonne | Type | Merknad |
|---|---|---|
| `ansatt_id` | tekst | Kobles til Ansatte. |
| `dato` | dato | Startdato for aktiviteten. |
| `type` | tekst | kurs, sertifisering, konferanse, intern opplæring, mentorordning |
| `timer` | tall | |
| `kostnad` | tall (kr) | Direkte kostnad (kursavgift, reise). Ikke lønn i arbeidstiden. |

**en_til_en.csv** (én rad per ansatt per måned personen var ansatt)

| Kolonne | Type | Merknad |
|---|---|---|
| `ansatt_id` | tekst | |
| `måned` | tekst | ÅÅÅÅ-MM |
| `antall_1til1` | tall | Antall 1:1-samtaler med lederen den måneden. |

**stillingsendringer.csv** (én rad per forfremmelse eller intern overgang)

| Kolonne | Type | Merknad |
|---|---|---|
| `ansatt_id` | tekst | |
| `team` | tekst | Alltid personens eget team: datamodellen har ett team per person, så endringer skjer innenfor teamet. |
| `type` | tekst | forfremmelse (ny rolle, høyere nivå), intern overgang (ny rolle, samme nivå) |
| `utlysningsdato` | dato | Intern utlysning av stillingen. |
| `dato` | dato | Første dag i ny rolle. |

**Bevisst ikke med:** formelle medarbeidersamtaler (Tania mener de måler om en
rutine er fulgt, ikke om noen utvikler seg; jevnlige 1:1 brukes i stedet) og
kompetansegap per person (krever individvurderinger, sensitivt og upresist).

### Metrikker

- **Snitt ansatte** = gjennomsnittet av antall ansatte ved hver månedsslutt i
  perioden.
- **Turnover** (total, frivillig, uønsket) = antall som sluttet i perioden /
  snitt ansatte.
  - **Prinsipp: en avgang teller i turnover hvis stillingen må erstattes.**
  - Derfor teller `frivillig`, `ufrivillig` og `pensjon` i total turnover.
  - `kontrakt utløpt` telles **ikke** i turnoverratene, men rapporteres
    separat (antall).
  - Ratene **annualiseres** når perioden ikke er 12 måneder:
    rate × 12 / antall måneder i perioden.
- **eNPS** (−100 til +100) = andel anbefalere (9-10) minus andel kritikere (0-6).
  - For flere team samlet: gjennomsnitt **vektet med antall svar** (gir samme
    tall som å regne eNPS på alle svarene samlet).
  - **Svarandel** = antall svar / antall invitert. **Lav svarandel (under 50 %)
    markeres.**
  - Kvartaler som ligger helt innenfor perioden er med. Sammenlignes med samme
    kvartal i fjor og med forrige kvartal.
  - **Ingen benchmark** (ingen verifisert kilde).
  - **Kobling mot langtidsfravær** vises med merknaden: «Sammenheng, ikke
    nødvendigvis årsak – og den kan gå begge veier: lavt engasjement kan gi mer
    fravær, og høyt fravær gir mer belastning på dem som er igjen.»
- **Bemanning mot plan** = faktisk antall ansatte ved månedsslutt (alle
  ansettelsesformer) sammenlignet med `planlagt_antall`, per team og måned.
  - Antall personer, ikke årsverk (årsverk kan komme senere).
  - **Bemanningsgrad** = faktisk / plan ved periodeslutt.
  - Avvik vises i **nøytrale farger** (ikke rødt/grønt). Team med **mer enn
    5 % avvik i begge retninger** markeres (◆ og nøytral bakgrunn) – både i
    tabellen og på KPI-kortet. Regelen ligger i `over_avviksgrense()`.
  - «Herav midlertidige» vises i egen kolonne. Ledergruppen vises (antall
    ansatte er ikke sensitivt).
- **Tid til tiltredelse** = median antall dager fra `utlysningsdato` til
  `ansattdato` (inkluderer oppsigelsestid), for dem som ble ansatt i perioden.
  Skiller seg fra tid til ansettelse, som stopper ved `aksept_dato`.
- **Kompetanseutvikling** (siden Utvikling, `beregninger.py`):
  - **Opplæring per ansatt** = sum timer / snitt ansatte. **Kostnad per ansatt** =
    sum direkte kostnad / snitt ansatte.
  - **Deltatt i opplæring** = ansatte med minst én aktivitet / alle som var ansatt i
    perioden.
  - **Jevnlige 1:1** = andel med minst én 1:1 med lederen i minst 10 av 12
    måneder, blant dem som var ansatt (minst én dag) i alle månedene.
  - **Besatt internt** (intern besettelsesgrad) = interne besettelser /
    (interne + eksterne ansettelser med rekrutteringsdata).
  - **Tid til besatt:** internt = median dager fra intern utlysning til ny
    rolle; eksternt = tid til ansettelse (utlysning til aksept). Internt går
    raskere blant annet fordi det ikke er oppsigelsestid.
  - **Forfremmelser** = antall, og andel av snitt ansatte. Sensitivt (se
    «Personvern»).
  - Merknad på siden: tallene viser innsats, ikke effekt.
  - **Sammenheng:** to punktgrafer per team med jevnlige 1:1 på x-aksen, mot
    frivillig turnover og mot eNPS (`enps_periode()`: snitt for kvartalene i
    perioden, vektet med svar, bare når alle kvartalene har minst 5 svar).
    Merknad `OPPFOLGING_MERKNAD`: sammenheng, ikke nødvendigvis årsak.
- **Kostnad ved uønsket turnover** = sum årslønn for uønskede avganger × 75 %
  (antakelse). Vises bare for hele selskapet, siste 12 mnd mot forrige 12 mnd
  (se «Personvern»).
- **Sykefravær** = (tapte korttid + tapte langtid) / avtalte dagsverk.
  **Langtidsfravær** = tapte langtid / avtalte dagsverk.
- **Tid til ansettelse** = median antall dager fra `utlysningsdato` til
  `aksept_dato`, for dem som ble ansatt i perioden.
- **Kvalitet på ansettelser**, fordelt på rekrutteringsmetode:
  - **Tidlig turnover** = andel som sluttet innen 12 måneder etter
    `ansattdato`. Bare ansatte med `ansattdato` minst 12 måneder før
    periodeslutt tas med.
  - **Prøvetid bestått** = andel med `prøvetid_bestått` = ja. Bare ansatte
    med `ansattdato` minst 6 måneder før periodeslutt tas med.
  - Ansatte uten registrert rekrutteringsmetode holdes utenfor.
  - **Tre nivåer** til sammenligning: (1) ustrukturert, (2) strukturert intervju
    alene (nei på alle tilleggsmetoder), (3) strukturert + tillegg (ja på minst
    én av case study, personlighetstest, evnetest). Alltid med n og femregelen.
- **Bruk av tilleggsmetoder** = antall ansettelser i perioden per metode – bare
  antall, **aldri resultater**.

## Utseende (gjelder alle sider)

- **Retning:** rolig, profesjonelt og nordisk – et verktøy en CFO stoler på.
- **Fiktivt selskap:** «Fjordlys Tech AS», vist øverst som «fiktivt selskap».
- **Tema** i `.streamlit/config.toml`: hovedfarge dyp petrol `#0F4C5C`, lys nøytral
  bakgrunn, standard sans-serif-skrift.
- **Felles utseende** i `utseende.py`: `topp()` (selskapsnavn, tittel, spørsmålet
  siden svarer på, og diskret merking om syntetiske data), `statusmerke()` og
  `skjult_kort()`. Nye sider bruker disse.
- **Spørsmålet hver detaljside svarer på** står i `SPORSMAL` i `filtre.py` og vises
  i grått rett under tittelen. Spørsmålene knytter sidene til introduksjonen på
  forsiden.
- **Felles kode, ett sted:** data leses via `datalasting.py` (lagres i cache, så
  avtalte dagsverk regnes ut én gang). Sidestiene står bare i `SIDER` i
  `filtre.py`. Visningstekster som `enps_tekst()`, `fortegn()`, `endring_antall()`
  og «skjult»-tekstene (`SKJULT`, `SKJULT_UNDER_5`, `SKJULT_PRIKKET`) ligger i
  `beregninger.py`.
- **Verktøytips i grafer** viser ferdig formatert tekst (`prosent()`,
  `enps_tekst()`): komma og Excel-avrunding, ikke desimalpunktum og
  JavaScript-avrunding.
- **Palett for grafer** (samme på alle sider, fast rekkefølge): petrol, lys
  petrol, nøytral grå (`u.PETROL`, `u.PETROL_LYS`, `u.NOYTRAL`, `u.NOYTRAL_LYS`).
  Kontrollert for kontrast og fargeblindhet.
- **Statusfarger** (grønn/oransje/rød) brukes **bare** til status, aldri til
  vanlige serier, og alltid med ord og symbol. Merknader som ikke er status
  vises i rolige infobokser (`st.info`), ikke gule varselbokser.
- KPI-kort i `st.container(border=True)` med jevn luft. Innsikter som egne kort
  der «Mulig neste steg» er skilt fra funnet.
- **«Mulig neste steg»** har lys petrol bakgrunn (`MARKERT_BAKGRUNN`, `#E4EEF0`)
  uten ramme, og lyspæren og overskriften i petrol. Fargen settes på ett sted:
  `neste_steg_stil()` i `utseende.py` (CSS for beholdere med key `neste_steg_…`).
  Kontrast: tekst `#1E2A30` på `#E4EEF0` er 12,4 : 1.

## Oversikt (forsiden)

`sider/0_Oversikt.py` viser hele selskapet, **siste 12 mnd**, uten filter. Regler og
terskler ligger i `innsikter.py`.

**Øverst på forsiden** (under toppen, før «Nøkkeltall»):
- **Introduksjon** (`INTRO`, Tanias formulering, gjengis ordrett): hvem dashbordet
  er for (ledergruppen i et selskap med 50-500 ansatte: daglig leder,
  økonomidirektør og HR), hvilke spørsmål ledelsen og HR-leder har, og hvordan
  dashbordet brukes. Sier også at tallene gjelder grupper og at tilgangen er
  begrenset.
- **Periodelinjen:** «Tallene gjelder hele selskapet de siste 12 månedene (…).
  Velg et tema i menyen til venstre for detaljer. Data per 30.09.2026.
  Oppdateres månedlig.» Datoene hentes fra `FASTE_PERIODER` og `DATA_TIL`.

### Status for nøkkeltall (OK / Følg med / Kritisk)
Vises med ord, ikon og farge i `statusmerke()` (`utseende.py`): hake (OK), øye
(Følg med) og utropstegn (Kritisk).

Status settes på de **avrundede** tallene som vises. Tersklene er skjønn, ikke en
standard, og vises åpent på siden («Slik settes status»).

| Nøkkeltall | OK | Følg med | Kritisk | Rask forverring → minst «Følg med» |
|---|---|---|---|---|
| Total turnover | under 10 % | 10-15 % | over 15 % | +3 pp |
| Uønsket turnover | under 3 % | 3-5 % | over 5 % | +2 pp |
| Kostnad uønsket turnover | følger uønsket turnover | | | |
| Sykefravær | under 5 % | 5-6 % | over 6 % (**internt mål**; landssnittet vises bare som referanse) | +1 pp |
| eNPS | +10 eller høyere | 0 til +9 | under 0 | −10 poeng |
| Bemanning mot plan | avvik inntil 5 % | 5-10 % | over 10 % | – (nøytral, ingen pil) |
| Tid til ansettelse | inntil 45 dager | 46-60 dager | over 60 dager | +15 dager |

Sammenligning som på sidene: turnover mot forrige 12 mnd; fravær, eNPS og
rekruttering mot samme periode i fjor. Kostnaden mot forrige 12 mnd, regnet på
de avrundede tallene. Sykefravær og eNPS «uten ledergruppen»
(sekundær prikking), som på sidene.

### «Hva ledelsen bør vite nå» – regelbaserte innsikter
Teksten under overskriften (`INNSIKT_FORKLARING`, Tanias formulering): «Regelbaserte
innsikter om de største avvikene. De bruker bare tall som også vises under de andre
temaene, med de samme personvernreglene, og nevner aldri skjulte grupper.» Kommer
AI-funksjonen, må teksten skille tydelig mellom regelbasert og AI.

Maks 5, viktigste først. Hver innsikt har tekst, eventuell merknad, **«Mulig neste
steg (forslag)»** og lenke(r) som åpner siden med teamet forhåndsvalgt
(`forhandsvelg()` i `filtre.py`).

1. **Fravær og engasjement** (per team): sykefravær over 6 % eller +1 pp mot i
   fjor, og/eller eNPS under 0 eller fall ≥ 10 poeng. Samme team → én innsikt,
   med koblingsmerknaden. Lav svarandel → merknad om frafallsskjevhet.
   Neste steg: samtale med teamleder om arbeidsbelastning, og systematisk
   oppfølging av langtidssykmeldte.
2. **Bemanning**: team med over 5 % avvik. Under plan → neste steg: lys ut
   tidligere – ledetid = median tid til tiltredelse (dager / 30 ≈ måneder).
3. **Turnover**: frivillig turnover ≥ 15 % og ≥ 1,5 × selskapet, bare for team
   med minst 5 ansatte og 5 avganger. Neste steg: sluttsamtaler og gjennomgang
   av rekrutteringsmetode i teamet. **Har teamet også lite oppfølging** (jevnlige
   1:1 under 60 % og minst 20 pp under selskapet), blir innsikten «høy frivillig
   turnover og lite oppfølging», med merknaden om sammenheng
   (`OPPFOLGING_TURNOVER_MERKNAD`), lenke til Utvikling og neste steg «faste 1:1
   mellom teamleder og hver ansatt».
4. **Rekruttering**: tidlig turnover ustrukturert mot strukturert intervju
   alene, når begge er synlige (etter sekundær prikking, som på
   Rekruttering-siden) og forskjellen er ≥ 10 pp. Merknad: «Sammenheng,
   ikke nødvendigvis årsak. Peker i riktig retning, men grunnlaget er lite
   (n = …). Følg utviklingen – metodevalget støttes uansett av forskningen.»
   Neste steg: fortsett å øke andelen strukturerte prosesser.
5. **Kritiske nøkkeltall** for hele selskapet.

**Personvern:** innsiktene bruker bare tall som også vises på de andre sidene,
med de samme reglene (femregel, sekundær prikking) – skjulte grupper nevnes aldri.

## Publisering (Streamlit Community Cloud)

- Appen oppdateres av seg selv fra `main` på GitHub.
- **Start appen på nytt etter en deploy som endrer felles filer** (`filtre.py`,
  `utseende.py`, `beregninger.py`, `datalasting.py`, `innsikter.py`): Manage app → ⋮ →
  Reboot app. Ellers kan Streamlit Cloud holde de gamle versjonene i minnet, og alle
  sidene feiler med ImportError (skjedde 16.10.2026). Endringer bare i README eller
  CLAUDE.md trenger ikke omstart.

## Syntetiske data

- Lages av `lag_syntetiske_data.py` med fast tilfeldighetsfrø (`FRO = 42`), så
  dataene blir like hver gang. Lagres i `data/`: `ansatte.csv`, `fravaer.csv`,
  `engasjement.csv`, `bemanningsplan.csv`, `opplaering.csv`, `en_til_en.csv` og
  `stillingsendringer.csv` (kolonner som i «Datamodell»).
- Periode: okt 2024-sep 2026. Dataene er et øyeblikksbilde per **30.09.2026**
  (ingen framtidige sluttdatoer, ingen som ikke har startet).
- Rekrutteringsdata registreres fra **okt 2024**. Ansatt før det = tomme
  rekrutteringsfelt.
- Historien dataene skal vise (siste 12 mnd):
  1. **Kundesuksess**: langtidsfraværet stiger siste halvår, eNPS faller fra ca.
     +10 til −15. Har vikarer med `kontrakt utløpt`.
  2. **Salg**: frivillig turnover ca. 20 %, mange slutter innen 12 mnd, flest
     ansatt ustrukturert.
  3. **Strukturert rekruttering**: tidlig turnover ca. 10 % mot ca. 30 % for
     ustrukturert, høyere andel bestått prøvetid. Andelen strukturerte øker.
  4. **Teknologi**: median tid til ansettelse ca. 60 dager, under bemanningsplanen.
  5. **Totalt**: turnover ca. 14 %, sykefravær ca. 5,5 % – problemene synes bare
     per team.
  6. **Ledergruppen**: 4 personer.
  7. **Pensjon**: 2 planlagte pensjoneringer (teknologi og økonomi og hr), så
     regelen om at pensjon teller i total turnover blir testet.
  8. **Prøvetid**: én strukturert ansettelse stryker, så strukturert ikke
     ligger på 100 %.
  9. **Tilleggsmetoder**: strukturerte ansettelser utlyst fra 2026 får én eller
     flere tilleggsmetoder med sannsynlighet 25 %. I dataene ble det 4 av 15
     (ca. 27 %). Dashbordet teller etter ansattdato, og av de 20 strukturerte
     som startet i 2026 har 4 tilleggsmetoder (20 %), fordi noen ble utlyst i 2025. **Ingen innebygd
     effekt** på turnover eller prøvetid. Trekkes med egen tilfeldighetsgenerator
     (`FRO + 1`), så resten av dataene ikke endres. Gruppen er så liten at nivå 3
     i praksis vises som «for tidlig å måle» eller «skjult» – det er poenget.
  10. **Lav svarandel**: kundesuksess har ca. 45 % svarandel i 2026-K3 (resten
      72-90 %). Overstyres etter trekningen, så resten av dataene ikke endres.
  11. **Kompetanseutvikling** (egen tilfeldighetsgenerator `FRO + 2`, så resten av
      dataene er uendret): salg har minst opplæring, færrest jevnlige 1:1 (ca.
      40 % mot ca. 80 % totalt) og nesten ingen interne besettelser. Teknologi
      har mest opplæring (sertifiseringer). Ca. 15 % av stillingene siste 12 mnd
      besettes internt, og internt går raskere enn eksternt. Mønsteret er per
      team, ikke en effekt per person.

### Presiseringer av definisjonene
- **Arbeidsdager** (for avtalte dagsverk) = mandag-fredag. Helligdager og ferie
  er ikke trukket fra.
- **Kvalitet på ansettelser** beregnes bare for **faste** ansatte.
- **Tidlig turnover** teller de samme sluttårsakene som turnover (`kontrakt
  utløpt` teller ikke).

## Om meg (brukeren)

- Jeg kan **Excel godt**, men er **nybegynner i Python**.
- Jeg vil forstå koden selv, ikke bare få den levert – jeg skal kunne forklare
  prosjektet i et jobbintervju.

## Slik skal Claude jobbe i dette prosjektet

### 1. Forklar alltid koden på Excel-nivå
- Forklar hva koden gjør med enkle ord, og sammenlign med Excel der det passer.
  Eksempler:
  - En pandas **DataFrame** ≈ et regneark/en tabell
  - En **kolonne** ≈ en kolonne i Excel
  - `groupby` ≈ en pivottabell
  - `merge` ≈ XOPPSLAG / VLOOKUP
  - Filtrering ≈ autofilter
- Unngå unødvendig fagsjargong. Når et nytt begrep dukker opp, forklar det kort.
- Skriv korte, tydelige kommentarer i koden (på norsk).

### 2. Ta små steg
- Gjør én ting om gangen, slik at jeg kan følge med og teste underveis.
- Etter hvert steg: forklar hva som ble gjort, og hvordan jeg kan sjekke at det
  fungerer.
- Foreslå neste steg, men ikke gjør det før jeg sier ja.

### 3. Spør før store endringer
- Spør alltid før du:
  - oppretter flere nye filer på én gang
  - endrer strukturen i prosjektet
  - skriver om eksisterende kode i stor grad
  - installerer nye pakker/biblioteker
  - sletter noe
- Ved valg mellom flere løsninger: gi en kort anbefaling med begrunnelse.

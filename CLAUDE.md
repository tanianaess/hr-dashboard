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

- Dashbordet skal **aldri vise data om enkeltpersoner** – bare tall for grupper
  (team, avdeling, aldersgruppe osv.).
- **Femregelen:** grupper med **færre enn 5** skjules for:
  - **sykefravær** – antall ansatte i gruppa
  - **eNPS** – `antall_svar` (ikke teamstørrelsen)
  - **turnover per team**:
    - team med færre enn 5 ansatte (snitt i perioden): **alt** skjules
    - totalt antall avganger og total turnover vises ellers alltid – at noen
      har sluttet er ikke sensitivt
    - fordeling på **uønsket og sluttårsak** (inkl. `kontrakt utløpt`) vises
      bare når teamet har **minst 5 avganger** i perioden; ellers bare for hele
      selskapet. Det sensitive er ledelsens vurdering av enkeltpersoner.
    - Samme regel gjelder når filteret velger noen team, men ikke alle.
  - **kvalitet på ansettelser** – både per team og per rekrutteringsmetode
    (antall ansatte som inngår i beregningen)
  
  Dette gjelder også når filtre gjør en gruppe mindre enn 5.
- **Lønn** vises aldri per team. Den brukes bare i kostnadsberegningen, og
  kostnaden vises bare for hele selskapet (ikke når filteret velger enkeltteam).
- **Stilling** blir aldri et filter i dashbordet (stilling + team kan peke ut
  én person).
- Selv om dataene er syntetiske, skal dashbordet bygges som om de var ekte.

## Presentasjon i dashbordet (gjelder alltid)

- **Vis alltid n ved siden av prosenter for små grupper**, f.eks.
  «12,5 % (1 av 8)». Én person mer eller mindre kan flytte en liten gruppe
  mange prosentpoeng, og leseren må kunne se det.
- **Dataene er syntetiske – si det tydelig.** Både dashbordet og README skal
  klart opplyse at dataene er oppdiktet og konstruert for å illustrere
  metodikk, og at tallene **ikke er ekte funn** om noe selskap.

## Datamodell

Gjelder alle ark:
- Datoer skrives ÅÅÅÅ-MM-DD.
- Teamnavn skrives alltid med små bokstaver (se tabellen under «Data»).
- Alle metrikker beregnes i Python, og alltid for en valgt periode
  (periodestart og periodeslutt).
- `Datamodell.xlsx` er brukerens Excel-utkast og **fasit for de 20
  testradene**. Fila oppdateres ikke (den har derfor ikke de nye kolonnene).
  Python-versjonen følger denne beskrivelsen, ikke formlene i Excel-fila.

### Ark: Ansatte (én rad per ansatt, også de som har sluttet)

| Kolonne | Type | Lovlige verdier | Merknad |
|---|---|---|---|
| `ansatt_id` | tekst | A001, A002 … | Eneste identifikator. Aldri navn. |
| `team` | tekst | de 7 teamnavnene | |
| `stilling` | tekst | fritekst | Aldri filter i dashbordet. |
| `ansettelsesform` | tekst | fast, midlertidig | |
| `stillingsprosent` | tall | 1–100 | |
| `årslønn` | tall (kr) | | **Faktisk** lønn (ikke omregnet til 100 %). Bare til kostnadsberegning, aldri vist per team. |
| `ansattdato` | dato | | |
| `sluttdato` | dato | | Tom = fortsatt ansatt. |
| `sluttårsak` | tekst | frivillig, ufrivillig, pensjon, kontrakt utløpt | Tom hvis ikke sluttet. |
| `uønsket` | tekst | ja, nei | Bare for dem som har sluttet. «ja» bare når sluttårsak = frivillig.* |
| `rekrutteringsmetode` | tekst | strukturert, ustrukturert | Tom = ansatt før rekrutteringsdata ble registrert. |
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
| `tapte_dagsverk_korttid` | tall | Fravær på 1–16 dager (arbeidsgiverperioden). |
| `tapte_dagsverk_langtid` | tall | Fravær over 16 dager. |
| `avtalte_dagsverk` | tall | **Lagres ikke, men regnes ut i Python fra Ansatte**: arbeidsdager i måneden × stillingsprosent, for alle som var ansatt i måneden. Ferie er *ikke* trukket fra, så fraværsprosenten blir litt lavere enn med SSBs metode. |

### Ark: Engasjement (én rad per team per kvartal)

| Kolonne | Type | Merknad |
|---|---|---|
| `team` | tekst | |
| `kvartal` | tekst | ÅÅÅÅ-K1 … K4 |
| `enps` | tall | −100 til 100 |
| `antall_svar` | tall | Femregelen bruker dette tallet. |

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
- **Bemanning mot plan** = faktisk antall ansatte ved månedsslutt (alle
  ansettelsesformer) sammenlignet med `planlagt_antall`, per team og måned.
- **Kostnad ved uønsket turnover** = sum årslønn for uønskede avganger × 75 %
  (antakelse).
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

## Syntetiske data

- Lages av `lag_syntetiske_data.py` med fast tilfeldighetsfrø (`FRO = 42`), så
  dataene blir like hver gang. Lagres i `data/`: `ansatte.csv`, `fravaer.csv`,
  `engasjement.csv`, `bemanningsplan.csv` (kolonner som i «Datamodell»).
- Periode: okt 2024–sep 2026. Dataene er et øyeblikksbilde per **30.09.2026**
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

### Presiseringer av definisjonene
- **Arbeidsdager** (for avtalte dagsverk) = mandag–fredag. Helligdager og ferie
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

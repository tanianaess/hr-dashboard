# HR-dashbord for people analytics

[![Tester](https://github.com/tanianaess/hr-dashboard/actions/workflows/tester.yml/badge.svg)](https://github.com/tanianaess/hr-dashboard/actions/workflows/tester.yml)

> ⚠️ **Syntetiske data.** Alle tall i dette prosjektet er oppdiktet og
> konstruert for å illustrere metodikk, og bygger ikke på data fra noe ekte
> selskap. Selskapet finnes ikke. Mønstrene i dataene er lagt inn med vilje
> (se [Historien i dataene](#historien-i-dataene)).

Et people analytics-dashbord for **Fjordlys Tech AS**, et fiktivt norsk tech-selskap med ca. 230
ansatte i 7 team, okt 2024-sep 2026. Bygget med Python, pandas og Streamlit.

Prosjektet viser hvordan HR-nøkkeltall kan defineres presist, beregnes
etterprøvbart og presenteres uten å eksponere enkeltpersoner.

## Mine valg

Jeg har bygget dashbordet for å vise hvordan jeg ville jobbet med HR-data sammen med
en ledergruppe. Bakgrunnen min er organisasjonspsykologi, og det preger valgene.

- **Få nøkkeltall som ledelsen faktisk bruker.** Turnover, sykefravær, rekruttering,
  bemanning og engasjement svarer på tre spørsmål: Hvor er risikoen, hva koster den,
  og har vi folkene vi trenger? Definisjonene følger ISO 30414:2025, så tallene kan
  forklares og sammenlignes over tid.
- **Kostnad i kroner.** Turnover og sykefravær vises også i kroner, fordi det er
  språket en økonomidirektør handler på: erstatningskostnad for alle som må erstattes
  (med uønskede avganger som en del av den), og hva arbeidsgiver betaler i de første
  16 dagene av sykefravær. Antakelsene står åpent og kan justeres.
- **Små endringer er ikke alarmer.** Pilene får bare farge når endringen er stor nok
  til å bety noe, og når tallet bygger på nok personer. Ellers er de grå.
- **Personvern styrer designet.** Grupper under fem vises ikke, og sensitive tall
  vises bare i faste perioder, så ingen kan regne ut små grupper ved å sammenligne
  utvalg. Reglene reduserer risikoen, men hindrer den ikke. Derfor er tilgangsstyring
  like viktig som teknikken.
- **Regelbaserte innsikter.** Forsiden peker på de største avvikene etter faste
  regler. Hver innsikt kan etterprøves, og skjulte grupper nevnes aldri.
- **AI med måte.** Lederbriefen på forsiden er skrevet av en AI-modell, men bare ut fra
  tall som allerede står der, ferdig prikkede. Teksten leses og godkjennes av et menneske
  før den vises, den er tydelig merket, og den stiller spørsmål til ledermøtet i stedet
  for å foreslå tiltak. Tiltakene forblir regelbaserte, så de kan etterprøves.
- **Forskning før egne data.** Som organisasjonspsykolog lener jeg meg på forskning
  når det gjelder rekruttering. Et selskap med 230 ansatte ansetter for få til å
  avgjøre hvilken metode som virker best. Dashbordet viser derfor hva forskningen sier
  (Sackett mfl., 2022), og bruker egne data til å følge med.
- **Det jeg bevisst lot være:** lønn per team, testresultater og
  kompetansevurderinger av enkeltpersoner. Det er sensitivt, og nytten står ikke i
  forhold til risikoen. Jeg måler heller ikke formelle medarbeidersamtaler to ganger i
  året. De sier om en rutine er fulgt, ikke om noen utvikler seg. Jevnlige 1:1 med
  lederen sier mer.
- **Med ekte data ville jeg** først avklart definisjoner og datakvalitet med HR og
  økonomi, og latt ledergruppen sette tersklene for status.
- **Teknisk:** Python, pandas og Streamlit, med automatiske tester for beregningene,
  personvernreglene og tekstreglene. Bygget sammen med en AI-assistent (Claude Code):
  reglene i `CLAUDE.md` er skrevet av meg, koden er skrevet etter dem, og testene vokter
  at de holdes.

## Innhold

| Side | Viser |
|---|---|
| **Oversikt** (forside) | Kort introduksjon: hvem dashbordet er for (ledergruppen i et selskap med 50-500 ansatte) og hvilke spørsmål det svarer på. Nøkkeltall for hele selskapet med endring og status (OK / følg med / kritisk). «Viktigste innsikter»: opptil 5 regelbaserte funn om de største avvikene, med mulig neste steg og lenke til detaljene · «Lederbrief»: kort tekst til ledermøtet skrevet av en AI-modell ut fra tallene på siden, lest og godkjent av et menneske før den vises, med spørsmål til ledermøtet, åpen visning av hva modellen fikk, og nedlasting som Markdown |
| **Turnover** | Total, frivillig og uønsket turnover med endring mot forrige periode · erstatningskostnad for alle avganger, med uønskede som en del av den, og justerbar antakelse (hele selskapet, siste 12 mnd mot forrige 12 mnd) · regnestykke: hva er det verdt å redusere frivillig turnover (færre avganger × gjennomsnittlig erstatningskostnad, aldri lønn per team) · avganger per måned (bare totalen) · tabell per team · filter: hele selskapet eller ett team, faste perioder |
| **Sykefravær** | Totalt, korttid og langtid med endring mot samme periode i fjor · internt mål, og landssnittet 6,57 % bare som referanse (alle bransjer, annen metode) ([NAV, årsnotat sykefravær 2025](https://www.nav.no/_/attachment/inline/93423200-87fc-4941-ad03-b763066da97e:b1217b72b4bebb26ac77729528f034ab57969675/%C3%85rsnotat%20sykefrav%C3%A6r%20%C3%A5ret%202025.pdf)) · kostnad i arbeidsgiverperioden (hele selskapet) · fravær per måned over hele dataperioden · tabell per team · filter: hele selskapet eller ett team, faste perioder |
| **Rekruttering** | Antall ansettelser, median tid til ansettelse og andel strukturert rekruttering mot samme periode i fjor · kvalitet på ansettelser (tidlig turnover og bestått prøvetid) på tre nivåer: ustrukturert, strukturert intervju alene og strukturert + tilleggsmetoder · bruk av tilleggsmetoder (case study, personlighetstest, evnetest) som antall · forskningsboks med validitet fra Sackett mfl. (2022) · andel strukturert per kvartal · tid til ansettelse per team · filter: hele selskapet eller ett team, faste perioder |
| **Bemanning** | Faktisk antall ansatte (og årsverk) mot bemanningsplanen · utvikling per måned · tabell per team med avvik, bemanningsgrad, ansettelser, avganger og tid til tiltredelse · team med mer enn 5 % avvik markeres · fritt filter (ingen sensitive tall) |
| **Utvikling** | Opplæring (timer, kostnad og andel som har deltatt i opplæring) · jevnlige 1:1 med lederen · intern mobilitet (besatt internt, tid til besatt internt mot eksternt, forfremmelser) · tabell per team · sammenheng mellom oppfølging, frivillig turnover og eNPS · filter: hele selskapet eller ett team, faste perioder |
| **Engasjement** | eNPS siste kvartal mot samme kvartal i fjor og forrige kvartal · svarandel (lav markeres) · eNPS per kvartal og team over hele dataperioden · tabell per team · kobling mot langtidsfravær (sammenheng, ikke nødvendigvis årsak) · filter: hele selskapet eller ett team, faste perioder |
| **Om dashbordet** | Hvorfor det er bygget slik (valgene over), hvordan det er bygget sammen med AI, hva som måtte vært på plass med ekte data, og hva reglene ikke gjør. Ingen tall, ingen filter |

## Personvern

Dashbordet er bygget som om dataene var ekte. Grunnprinsippet:

> **Sensitive tall vises bare i faste, ikke-overlappende visninger. Fritt filter brukes
> bare på tall som ikke er sensitive.**

- **Ingen enkeltpersoner** vises, bare tall for grupper. Ansatte har bare en
  ansatt-ID, aldri navn.
- **Femregelen:** grupper med færre enn 5 skjules. For turnover per team vises
  totalen alltid (at noen har sluttet er ikke sensitivt), men fordelingen på
  sluttårsak og «uønsket» bare når teamet har minst 5 avganger. Det sensitive er
  ledelsens vurdering av enkeltpersoner. Avganger per måned vises bare som total.
  Medianer (tid til ansettelse og tiltredelse) skjules når de bygger på under 5.
- **Sekundær prikking:** en skjult gruppe skal ikke kunne regnes ut som «total minus de
  synlige». For sensitive tall (sykefravær, eNPS, fordelingen på uønsket og sluttårsak, og
  kvalitet på ansettelser)
  holdes små skjulte grupper utenfor totalen, og totalen merkes, f.eks. «Hele selskapet
  (uten ledergruppen)». Totalt antall avganger og bemanning tar med alle.
- **Begrenset filter på sider med sensitive tall:** på turnover, sykefravær, rekruttering,
  eNPS og utvikling kan du bare velge hele selskapet eller ett team, og to faste perioder som ikke
  overlapper (siste 12 mnd og forrige 12 mnd). Ellers kunne to filtervalg eller
  overlappende perioder trekkes fra hverandre. Bare bemanning har fritt filter.
- **Trendgrafer over hele dataperioden:** grafene for sykefravær per måned og eNPS per
  kvartal viser alltid hele perioden, med femregelen per punkt.
- **n vises ved siden av prosenter**, f.eks. «20,7 % (8 av 39)», så leseren ser
  hvor få personer et tall bygger på.
- **Lønn vises aldri per team.** Kostnader som bygger på lønn (turnover, fravær,
  arbeidstid til opplæring) vises bare for hele selskapet og siste 12 mnd (mot forrige
  12 mnd), avrundet til nærmeste 0,1 mill. kr.
- **Stilling er aldri et filter**, fordi stilling og team sammen kan peke ut én person.
- **Testresultater lagres aldri.** Datasettet viser bare *om* en personlighets- eller
  evnetest ble brukt, ikke resultatet.
- **AI får bare prikkede tall.** Lederbriefen skrives av en AI-modell ut fra nøkkeltallene
  og innsiktene på forsiden, som allerede følger femregelen og sekundær prikking. Aldri
  rådata, ansatt-ID eller lønn. Et menneske leser og godkjenner teksten før den vises, og
  et fingeravtrykk av grunnlaget viser om den bygger på dagens tall. Det finnes ingen fri
  «chat med dataene»: et fritt spørsmål er et fritt filter.
- **Regnestykket for frivillig turnover** bruker selskapets gjennomsnittlige
  erstatningskostnad per avgang, aldri lønn per team.

> **Hva reglene ikke gjør:** Faste perioder, femregelen og sekundær prikking **reduserer** risikoen for at tall om små grupper kan utledes, men de **hindrer den ikke**. Ingen tekniske regler kan helt hindre det i et interaktivt verktøy. Den som kjenner organisasjonen, kan dessuten koble tallene med egen kunnskap, for eksempel om hvem som sluttet i en bestemt måned. Den viktigste beskyttelsen er derfor tilgangsstyring: i drift skal bare HR-ledelse og ledergruppen ha tilgang.

## Definisjoner (utvalg)

| Nøkkeltall | Definisjon |
|---|---|
| Snitt ansatte | Gjennomsnitt av antall ansatte ved hver månedsslutt i perioden |
| Turnover | Avganger i perioden / snitt ansatte, omregnet til helår. En avgang teller hvis stillingen må erstattes: frivillig, ufrivillig og pensjon, men ikke utløpte midlertidige kontrakter |
| Uønsket turnover | Frivillige avganger der vi ville beholdt personen |
| Sykefravær | Tapte dagsverk / avtalte dagsverk. Avtalte dagsverk = hverdager × stillingsprosent, uten fradrag for ferie og helligdager. Det gir litt lavere tall enn NAVs metode |
| Tid til ansettelse | Median antall dager fra utlysning til akseptert tilbud, for ansettelser i perioden |
| Kvalitet på ansettelser | Per nivå (ustrukturert · strukturert intervju alene · strukturert + tillegg), for en kohort av faste ansatte som har vært ansatt lenge nok: tidlig turnover (slutter innen 12 mnd) og andel bestått prøvetid (6 mnd). Viser sammenheng, ikke nødvendigvis årsak |
| Bemanningsgrad | Faktisk antall ansatte (alle ansettelsesformer) / planlagt antall, ved periodeslutt |
| Tid til tiltredelse | Median antall dager fra utlysning til første arbeidsdag (inkluderer oppsigelsestid) |
| eNPS | Andel anbefalere (9-10) minus andel kritikere (0-6), fra −100 til +100. For flere team: vektet med antall svar |
| Svarandel | Antall svar / antall invitert. Under 50 % markeres som lav |
| Jevnlige 1:1 | Andel med minst én 1:1 med lederen i minst 10 av 12 måneder, blant dem som var ansatt hele perioden |
| Besatt internt | Interne besettelser (forfremmelser og overganger) / alle besatte stillinger. Forfremmelser er sensitive og vises bare med minst 5 interne endringer |
| Erstatningskostnad | Sum årslønn for alle avganger der stillingen må erstattes × antatt kostnadsandel (standard 75 %, justerbar 50-200 %), med uønskede avganger som «herav». Bare hele selskapet, siste 12 mnd mot forrige 12 mnd |
| Kostnad i arbeidsgiverperioden | Tapte dagsverk korttid (1-16 dager) × dagslønn per årsverk. Et minimum. Bare hele selskapet |

Alle definisjoner, med datamodell, står i [`CLAUDE.md`](CLAUDE.md).

## Historien i dataene

Dataene er generert med vilje slik at de inneholder noen tydelige mønstre, slik
man ofte ser i virkeligheten, for å vise hva dashbordet kan avdekke:

1. **Kundesuksess:** langtidsfraværet stiger siste halvår, og eNPS faller fra ca.
   +10 til −15.
2. **Salg:** frivillig turnover rundt 20 %, mange slutter innen 12 måneder, og
   flest er ansatt gjennom ustrukturert rekruttering.
3. **Strukturert rekruttering:** lavere tidlig turnover og høyere andel bestått
   prøvetid enn ustrukturert. Andelen strukturerte ansettelser øker.
4. **Teknologi:** lang tid til ansettelse (ca. 60 dager) og under bemanningsplanen.
5. **Totalt:** turnover ca. 14 % og sykefravær ca. 5,5 %. Problemene synes bare
   når man ser per team.
6. **Utvikling:** salg har minst opplæring og færrest med jevnlige 1:1 med lederen,
   og høyest frivillig turnover. Forsiden kobler de to, med merknad om at det er en
   sammenheng og ikke nødvendigvis årsak.

## Slik kan dette tas i bruk hos dere

Dashbordet er bygget for å kunne kobles på ekte data.

**Data som trengs** (vanligvis eksport fra HR- og lønnssystemet):
- Ansatte: ansatt-ID, team, ansettelsesform, stillingsprosent, årslønn, ansatt- og
  sluttdato og sluttårsak. Om en avgang var uønsket, registreres sjelden i dag og må
  ofte innføres.
- Sykefravær per team og måned, delt i korttid og langtid.
- Medarbeiderundersøkelse per team og kvartal: eNPS, antall svar og antall inviterte.
- Bemanningsplan per team og måned.
- Rekrutteringsdata (metode og datoer), hvis rekrutteringssiden skal brukes.
- Utvikling: opplæringsaktiviteter (timer og kostnad), 1:1 med lederen per måned, og
  forfremmelser og interne overganger. 1:1-data finnes ofte ikke i HR-systemet i dag og
  må registreres.

**Det som tilpasses:** teamnavn, tersklene for status, kostnadsandelen og hvilke sider
som er med.

**I drift:** tilgang bare for HR-ledelse og ledergruppen, lagring i Norge eller EU,
databehandleravtale med leverandøren, og en vurdering av om det trengs en
personvernkonsekvensvurdering (DPIA) før oppstart. Tall sendes ikke til en ekstern
AI-tjeneste før det er vurdert og dokumentert, selv om aggregerte, prikkede tall i
utgangspunktet ikke er personopplysninger.

**Innføring i tre steg:** kartlegge data og definisjoner, koble på dataene og
kontrollere tallene mot dagens rapporter, og gå gjennom dashbordet med ledergruppen og
justere.

## Kjør selv

Krever **Python 3.12** eller nyere (testet med 3.12 og 3.14). Velg Python 3.12 også
ved publisering på Streamlit Community Cloud.

```bash
# 1. Lag et virtuelt miljø og installer pakkene
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Start dashbordet (åpne http://localhost:8501)
streamlit run app.py
```

Dataene ligger ferdig i `data/`. Vil du lage dem på nytt:

```bash
python lag_syntetiske_data.py
```

Generatoren bruker et fast tilfeldighetsfrø, så du får nøyaktig de samme dataene
hver gang.

**Lederbriefen (AI)** lages på forhånd, på egen maskin, aldri i den publiserte appen:

```bash
pip install -r requirements-dev.txt
# Sett ANTHROPIC_API_KEY som miljøvariabel (nøkkelen ligger aldri i repoet)
python lag_lederbrief.py             # lager et utkast i data/lederbrief.json
python lag_lederbrief.py --godkjenn  # etter at du har lest teksten
```

Forsiden viser briefen bare når den er godkjent og bygger på dagens tall. Boksen
«Hva AI-modellen fikk» på forsiden viser instruksen og grunnlaget ordrett.

## Prosjektstruktur

```
app.py                    Startfil: menyen
sider/0_Oversikt.py       Oversikt (forside)
innsikter.py              Terskler for status og regler for innsikter
utseende.py               Felles utseende: palett, toppen av sidene, statusmerker, skjulte KPI-kort
sider/1_Turnover.py       Turnoversiden
sider/2_Sykefravaer.py    Sykefraværssiden
sider/3_Rekruttering.py   Rekrutteringssiden
sider/4_Bemanning.py      Bemanningssiden
sider/5_Engasjement.py    Engasjementssiden (eNPS)
sider/6_Utvikling.py      Utviklingssiden (opplæring, 1:1 og intern mobilitet)
sider/7_Om.py             Om dashbordet (valgene, AI-historien, hva som trengs med ekte data)
lederbrief.py             Lederbrief (AI): instruksen, grunnlaget, kontrollene og lesing av data/lederbrief.json
lag_lederbrief.py         Lager lederbriefen med Claude (bare på egen maskin, med API-nøkkel)
beregninger.py            Alle formler (brukes av alle sider)
filtre.py                 Felles filtre for periode og team, sidestiene (SIDER) og spørsmålene per side
.github/workflows/        Kjører testene automatisk på GitHub (GitHub Actions)
datalasting.py            Felles innlesing av data (lest én gang, deles av alle sider)
lag_syntetiske_data.py    Genererer de syntetiske dataene
data/                     CSV-filer: ansatte, fravær, engasjement, bemanningsplan, opplæring, 1:1, stillingsendringer, og lederbrief.json (AI)
kontroller_mot_excel.py   Sjekker Python-formlene mot en Excel-fasit
tests/                    Automatiske tester (pytest)
Datamodell.xlsx           Excel-utkast til datamodell med 20 testrader (fasit)
CLAUDE.md                 Prosjektregler, datamodell og definisjoner
```

## Kvalitetssikring

Automatiske tester (pytest) sjekker nøkkeltallene, personvernreglene, tekstreglene,
lederbriefen (bare tall fra forsiden, bare team som nevnes der, vises bare når den er
godkjent) og at alle sidene kjører for alle filtervalg. De kjører også automatisk på GitHub ved hver
push (GitHub Actions, se merket øverst). Slik kjører du dem selv:

```bash
pip install -r requirements-dev.txt
pytest
```

Formlene er også kontrollert mot en håndregnet Excel-fasit (`Datamodell.xlsx`, 20
testrader) med `kontroller_mot_excel.py`, som bruker de samme funksjonene som
dashbordet (`beregninger.py`). Avvikene er forklart i utskriften:

- **Snitt ansatte** (og dermed turnoverratene): Python bruker snittet av hver
  månedsslutt, Excel-utkastet (start + slutt) / 2.
- **Tid til ansettelse = NaN:** ingen av de 20 testradene ble ansatt i perioden
  (siste ansattdato er 01.09.2025), så Python gir tomt svar. Excel-utkastet tok
  medianen av alle radene (42,5 dager).

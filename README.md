# HR-dashbord for people analytics

> ⚠️ **Syntetiske data.** Alle tall i dette prosjektet er oppdiktet og
> konstruert for å illustrere metodikk. Selskapet finnes ikke, og tallene er
> **ikke ekte funn** om noe selskap. Mønstrene i dataene er lagt inn med vilje
> (se [Historien i dataene](#historien-i-dataene)).

Et people analytics-dashbord for **Fjordlys Tech AS**, et fiktivt norsk tech-selskap med ca. 230
ansatte i 7 team, okt 2024–sep 2026. Bygget med Python, pandas og Streamlit.

Prosjektet viser hvordan HR-nøkkeltall kan defineres presist, beregnes
etterprøvbart og presenteres uten å eksponere enkeltpersoner.

## Innhold

| Side | Viser |
|---|---|
| **Oversikt** (forside) | De viktigste tallene for hele selskapet med endring og status (OK / følg med / kritisk) · «Hva ledelsen bør vite nå»: opptil 5 regelbaserte innsikter om de største avvikene, med mulig neste steg og lenke til detaljene |
| **Turnover** | Total, frivillig og uønsket turnover med endring mot forrige periode · kostnad ved uønsket turnover med justerbar antakelse (hele selskapet, siste 12 mnd mot forrige 12 mnd) · avganger per måned (bare totalen) · tabell per team · filter: hele selskapet eller ett team, faste perioder |
| **Sykefravær** | Totalt, korttid og langtid med endring mot samme periode i fjor · sammenligning med landssnittet 6,57 % ([NAV, årsnotat sykefravær 2025](https://www.nav.no/_/attachment/inline/93423200-87fc-4941-ad03-b763066da97e:b1217b72b4bebb26ac77729528f034ab57969675/%C3%85rsnotat%20sykefrav%C3%A6r%20%C3%A5ret%202025.pdf)) · fravær per måned over hele dataperioden · tabell per team · filter: hele selskapet eller ett team, faste perioder |
| **Rekruttering** | Antall ansettelser, median tid til ansettelse og andel strukturert rekruttering mot samme periode i fjor · kvalitet på ansettelser (tidlig turnover og bestått prøvetid) på tre nivåer: ustrukturert, strukturert intervju alene og strukturert + tilleggsmetoder · bruk av tilleggsmetoder (case study, personlighetstest, evnetest) som antall · forskningsboks med validitet fra Sackett mfl. (2022) · andel strukturert per kvartal · tid til ansettelse per team · filter: hele selskapet eller ett team, faste perioder |
| **Bemanning** | Faktisk antall ansatte mot bemanningsplanen · utvikling per måned · tabell per team med avvik, bemanningsgrad, ansettelser, avganger og tid til tiltredelse · team med mer enn 5 % avvik markeres · fritt filter (ingen sensitive tall) |
| **Engasjement** | eNPS siste kvartal mot samme kvartal i fjor og forrige kvartal · svarandel (lav markeres) · eNPS per kvartal og team over hele dataperioden · tabell per team · kobling mot langtidsfravær (sammenheng, ikke nødvendigvis årsak) · filter: hele selskapet eller ett team, faste perioder |

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
- **Begrenset filter på sider med sensitive tall:** på turnover, sykefravær, rekruttering
  og eNPS kan du bare velge hele selskapet eller ett team, og to faste perioder som ikke
  overlapper (siste 12 mnd og forrige 12 mnd). Ellers kunne to filtervalg eller
  overlappende perioder trekkes fra hverandre. Bare bemanning har fritt filter.
- **Trendgrafer over hele dataperioden:** grafene for sykefravær per måned og eNPS per
  kvartal viser alltid hele perioden, med femregelen per punkt.
- **n vises ved siden av prosenter**, f.eks. «20,7 % (8 av 39)», så leseren ser
  hvor få personer et tall bygger på.
- **Lønn vises aldri per team.** Kostnaden ved turnover vises bare for hele
  selskapet og siste 12 mnd (mot forrige 12 mnd), avrundet til nærmeste 0,1 mill. kr.
- **Stilling er aldri et filter**, fordi stilling og team sammen kan peke ut én person.
- **Testresultater lagres aldri.** Datasettet viser bare *om* en personlighets- eller
  evnetest ble brukt, ikke resultatet.

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
| eNPS | Andel anbefalere (9–10) minus andel kritikere (0–6), fra −100 til +100. For flere team: vektet med antall svar |
| Svarandel | Antall svar / antall invitert. Under 50 % markeres som lav |
| Kostnad ved uønsket turnover | Sum årslønn for uønskede avganger × antatt kostnadsandel (standard 75 %, justerbar 50–200 %). Bare hele selskapet, siste 12 mnd mot forrige 12 mnd |

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

## Prosjektstruktur

```
app.py                    Startfil: menyen
sider/0_Oversikt.py       Oversikt (forside)
innsikter.py              Terskler for status og regler for innsikter
utseende.py               Felles utseende: palett, toppen av sidene, statusmerker
sider/1_Turnover.py       Turnoversiden
sider/2_Sykefravaer.py    Sykefraværssiden
sider/3_Rekruttering.py   Rekrutteringssiden
sider/4_Bemanning.py      Bemanningssiden
sider/5_Engasjement.py    Engasjementssiden (eNPS)
beregninger.py            Alle formler (brukes av alle sider)
filtre.py                 Felles filtre for periode og team, og sidestiene (SIDER)
datalasting.py            Felles innlesing av data (lest én gang, deles av alle sider)
lag_syntetiske_data.py    Genererer de syntetiske dataene
data/                     CSV-filer: ansatte, fravær, engasjement, bemanningsplan
kontroller_mot_excel.py   Sjekker Python-formlene mot en Excel-fasit
tests/                    Automatiske tester (pytest)
Datamodell.xlsx           Excel-utkast til datamodell med 20 testrader (fasit)
CLAUDE.md                 Prosjektregler, datamodell og definisjoner
```

## Kvalitetssikring

Automatiske tester (pytest) sjekker nøkkeltallene, personvernreglene og at alle
sidene kjører for alle filtervalg:

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

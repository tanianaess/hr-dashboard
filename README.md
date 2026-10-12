# HR-dashbord – people analytics

> ⚠️ **Syntetiske data.** Alle tall i dette prosjektet er oppdiktet og
> konstruert for å illustrere metodikk. Selskapet finnes ikke, og tallene er
> **ikke ekte funn** om noe selskap. Mønstrene i dataene er lagt inn med vilje
> (se [Historien i dataene](#historien-i-dataene)).

Et people analytics-dashbord for et fiktivt norsk tech-selskap med ca. 230
ansatte i 7 team, okt 2024–sep 2026. Bygget med Python, pandas og Streamlit.

Prosjektet viser hvordan HR-nøkkeltall kan defineres presist, beregnes
etterprøvbart og presenteres uten å eksponere enkeltpersoner.

## Innhold

| Side | Viser |
|---|---|
| **Turnover** | Total, frivillig og uønsket turnover med endring mot forrige periode · kostnad ved uønsket turnover med justerbar antakelse · avganger per måned · tabell per team · filter for team og periode |

Planlagt: sykefravær, engasjement (eNPS), rekruttering og kvalitet på
ansettelser, bemanning mot plan.

## Personvern

Dashbordet er bygget som om dataene var ekte:

- **Ingen enkeltpersoner** vises – bare tall for grupper. Ansatte har bare en
  ansatt-ID, aldri navn.
- **Femregelen:** grupper med færre enn 5 skjules. For turnover per team vises
  totalen alltid (at noen har sluttet er ikke sensitivt), men fordelingen på
  sluttårsak og «uønsket» bare når teamet har minst 5 avganger – det sensitive er
  ledelsens vurdering av enkeltpersoner.
- **n vises ved siden av prosenter**, f.eks. «20,7 % (8 av 39)», så leseren ser
  hvor få personer et tall bygger på.
- **Lønn vises aldri per team.** Kostnaden ved turnover vises bare for hele
  selskapet.
- **Stilling er aldri et filter** – stilling og team sammen kan peke ut én person.

## Definisjoner (utvalg)

| Nøkkeltall | Definisjon |
|---|---|
| Snitt ansatte | Gjennomsnitt av antall ansatte ved hver månedsslutt i perioden |
| Turnover | Avganger i perioden / snitt ansatte, omregnet til helår. En avgang teller hvis stillingen må erstattes: frivillig, ufrivillig og pensjon – ikke utløpte midlertidige kontrakter |
| Uønsket turnover | Frivillige avganger der vi ville beholdt personen |
| Kostnad ved uønsket turnover | Sum årslønn for uønskede avganger × antatt kostnadsandel (standard 75 %, justerbar 50–200 %) |

Alle definisjoner, med datamodell, står i [`CLAUDE.md`](CLAUDE.md).

## Historien i dataene

Dataene er generert med vilje slik at de inneholder noen tydelige mønstre – som
man ofte ser i virkeligheten – for å vise hva dashbordet kan avdekke:

1. **Kundesuksess:** langtidsfraværet stiger siste halvår, og eNPS faller fra ca.
   +10 til −15.
2. **Salg:** frivillig turnover rundt 20 %, mange slutter innen 12 måneder, og
   flest er ansatt gjennom ustrukturert rekruttering.
3. **Strukturert rekruttering:** lavere tidlig turnover og høyere andel bestått
   prøvetid enn ustrukturert. Andelen strukturerte ansettelser øker.
4. **Teknologi:** lang tid til ansettelse (ca. 60 dager) og under bemanningsplanen.
5. **Totalt:** turnover ca. 14 % og sykefravær ca. 5,5 % – problemene synes bare
   når man ser per team.

## Kjør selv

Krever Python 3.

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
app.py                    Startfil: meny og forside
pages/1_Turnover.py       Turnoversiden
beregninger.py            Alle formler (brukes av alle sider)
lag_syntetiske_data.py    Genererer de syntetiske dataene
data/                     CSV-filer: ansatte, fravær, engasjement, bemanningsplan
kontroller_mot_excel.py   Sjekker Python-formlene mot en Excel-fasit
Datamodell.xlsx           Excel-utkast til datamodell med 20 testrader (fasit)
CLAUDE.md                 Prosjektregler, datamodell og definisjoner
```

## Kvalitetssikring

Formlene er kontrollert mot en håndregnet Excel-fasit (`Datamodell.xlsx`, 20
testrader) med `kontroller_mot_excel.py`. Avvik mellom Excel og Python er
forklart og skyldes bevisste valg i definisjonene (f.eks. snitt ansatte per
månedsslutt i stedet for (start + slutt) / 2).

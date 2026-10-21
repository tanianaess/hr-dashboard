# Eksterne tall (offentlig statistikk)

Tabellene her brukes av selskapsnotatet (`selskapsnotat.py`, se «Selskapsnotat» i
`CLAUDE.md`). De er lastet ned fra SSBs statistikkbank med
`python lag_selskapsnotat.py --last-ned`, som også skriver `kilder.json` (tabellnavn,
adresse, SSBs oppdateringsdato, siste periode og nedlastingsdato). `kilder.json` er
fasiten: står det noe annet der enn her, gjelder `kilder.json`.

Ingen tall er skrevet inn for hånd. Alt kommer fra API-et, og hele spørringen ligger i
adressen (`api_url` i `kilder.json`), så den kan limes inn i en nettleser og kontrolleres.

| Fil | SSB-tabell | Innhold | Filter | Siste periode | Oppdatert av SSB | Lastet ned |
|---|---|---|---|---|---|---|
| `ssb_12440.csv` | [12440](https://www.ssb.no/statbank/table/12440) | Sykefravær for lønnstakere (prosent), etter næring (SN2007) og type sykefravær (egenmeldt, legemeldt, begge), per kvartal | Begge kjønn, alle næringsgrupper, de siste 5 kvartalene | 2026K2 | 03.09.2026 | 21.10.2026 |
| `ssb_12441.csv` | [12441](https://www.ssb.no/statbank/table/12441) | Det samme per år (17 næringsgrupper) | Begge kjønn, alle næringsgrupper, siste år | 2025 | 19.06.2026 | 21.10.2026 |
| `ssb_11656.csv` | [11656](https://www.ssb.no/statbank/table/11656) | Lønnstakere og jobber, etter næring (SN2007): gjennomsnittlig månedslønn, avtalt månedslønn og antall lønnstakere, per kvartal | Begge kjønn, alle aldre, alle næringsgrupper, siste kvartal | 2026K2 | 13.08.2026 | 21.10.2026 |

Kolonnene i CSV-filene er SSBs egne koder og tekster (`NACE2007` og `NACE2007_tekst`,
`Sykefraver2` og `Sykefraver2_tekst`, `Tid`) og tallet i `verdi`. Tomt tall betyr at SSB
holder det tilbake («:»), typisk for små næringer i lønnstabellen.

## Slik leses tallene

- **Sykefraværsprosent** (SSB): sykefraværsdagsverk i prosent av avtalte dagsverk, for
  lønnstakere 16-69 år. Egenmeldt fravær kommer fra en utvalgsundersøkelse blant rundt
  10 000 virksomheter, legemeldt fravær fra NAVs sykmeldingsregister. Fra 1. kvartal 2019
  publiseres seriene uten feriekorrigering. Kilde: SSB, «Om statistikken» for sykefravær
  (<https://www.ssb.no/arbeid-og-lonn/arbeidsmiljo-sykefravaer-og-arbeidskonflikter/statistikk/sykefravaer>).
- **Næringsgruppene** er forskjellige i de tre tabellene. 12440 har både hovedområder
  (bokstaver, f.eks. «J Informasjon og kommunikasjon») og utvalgte detaljerte næringer
  (f.eks. «61-63 IKT-virksomhet»). 12441 har 17 grupper av 2-sifrede næringer. 11656 har
  2-sifrede næringer og summer av dem. `finn_grupper()` i `selskapsnotat.py` velger den mest
  spesifikke gruppen selskapets næringskode hører til, og går videre til en bredere gruppe
  når tallet mangler.
- **To standarder:** Enhetsregisteret bruker SN2025 (gyldig fra 1.1.2025, f.eks. 62.100
  Dataprogrammeringstjenester), mens SSB-tabellene bruker SN2007 (62.010
  Programmeringstjenester). Verifisert i SSB Klass, klassifikasjon 6
  (<https://data.ssb.no/api/klass/v1/classifications/6>), 21.10.2026. Koblingen går på de to
  første sifrene (næringen), som i hovedsak er like i de to standardene. Notatet skriver
  hvilken SSB-gruppe som er brukt, så den kan kontrolleres.
- **Månedslønn** (SSB): gjennomsnittlig månedslønn per heltidsekvivalent, slik SSB definerer
  den i tabell 11656. I regnestykkene ganges den med 12 for å få en årslønn.

## Enhetsregisteret

Navn, næringskode og antall ansatte hentes direkte fra Enhetsregisterets åpne API
(<https://data.brreg.no/enhetsregisteret/api/dokumentasjon>) når notatet lages, og lagres
ikke her. Ingen nøkkel trengs. Antall ansatte oppgis ikke for virksomheter med 0-4 ansatte.

## Lisenser

- SSB: Creative Commons Navngivelse 4.0 Internasjonal (CC BY 4.0), med SSB som kilde
  (<https://www.ssb.no/diverse/lisens>).
- Enhetsregisteret: Norsk lisens for offentlige data (NLOD).

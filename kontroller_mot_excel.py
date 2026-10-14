# Kontrollskript: regner ut metrikkene for de 20 testradene i Datamodell.xlsx
# med de SAMME formlene som dashbordet (beregninger.py), og sammenligner med
# Excel-svarene i arket Definisjoner.
#
# Kjør slik:  python kontroller_mot_excel.py   (virker fra hvilken som helst mappe)

from pathlib import Path

import pandas as pd

import beregninger as b

# Fila ligger ved siden av dette skriptet
FIL = Path(__file__).parent / "Datamodell.xlsx"

# Perioden vi måler – samme startdato som Excel-utkastet bruker (1.10.2025).
# Disse to linjene er som egne celler for periodestart og periodeslutt i Excel.
PERIODESTART = pd.Timestamp("2025-10-01")
PERIODESLUTT = pd.Timestamp("2026-09-30")

# Kjente, bevisste forskjeller mellom Excel-utkastet og definisjonene i CLAUDE.md
FORKLARING = {
    "Snitt ansatte": "Python: snitt av hver månedsslutt. Excel: (start + nå) / 2",
    "Total turnover": "Følger av snitt ansatte",
    "Frivillig turnover": "Følger av snitt ansatte",
    "Uønsket turnover": "Følger av snitt ansatte",
    "Tid til ansettelse": "Ingen av testradene ble ansatt i perioden, så Python gir "
                          "tomt svar (NaN). Excel tar medianen av alle radene",
}


# --- 1. Les arkene -----------------------------------------------------------
# Hvert ark blir en egen tabell (DataFrame), akkurat som arkfanene i Excel.
ansatte = pd.read_excel(FIL, sheet_name="Ansatte")
fravaer = pd.read_excel(FIL, sheet_name="Fravær")
definisjoner = pd.read_excel(FIL, sheet_name="Definisjoner")


# --- 2. Regn ut med formlene i beregninger.py ---------------------------------
maanedsslutter = b.maanedsslutter(PERIODESTART, PERIODESLUTT)
t = b.turnover(ansatte, PERIODESTART, PERIODESLUTT)

# NB: Avtalte dagsverk tas fra Fravær-arket her. I dashbordet regnes de ut fra
# Ansatte, men de 20 testradene er bare et utvalg og dekker ikke hele teamene.
s = b.sykefravaer(fravaer, PERIODESTART, PERIODESLUTT)

# Tid til ansettelse: Excel-utkastet har ferdig utregnet dager_til_ansettelse i
# stedet for utlysningsdato og aksept_dato, så her brukes den kolonnen – men med
# samme utvalg som dashbordet: ansatt i perioden, med registrert rekrutteringsmetode.
i_perioden = ansatte[
    ansatte["rekrutteringsmetode"].notna()
    & (ansatte["ansattdato"] >= PERIODESTART) & (ansatte["ansattdato"] <= PERIODESLUTT)
]
tid_til_ansettelse = i_perioden["dager_til_ansettelse"].median()


# --- 3. Sammenlign med Excel --------------------------------------------------
# Python-svarene, med samme navn som i Metrikk-kolonnen i Excel.
python_svar = {
    "Sluttet totalt": t["avganger"],
    "Sa opp selv": t["frivillig"],
    "Uønsket turnover (antall)": t["uønsket"],
    "Ansatte ved periodestart": b.antall_ansatt_paa(ansatte, PERIODESTART),
    "Ansatte nå": b.antall_ansatt_paa(ansatte, PERIODESLUTT),
    "Snitt ansatte": t["snitt_ansatte"],
    "Total turnover": t["total_rate"],
    "Frivillig turnover": t["frivillig_rate"],
    "Uønsket turnover": t["uønsket_rate"],
    "Kostnad uønsket turnover": t["lønn_uønsket"] * b.KOSTNADSANDEL_STANDARD,
    "Sykefravær": s["total_rate"],
    "Langtidsfravær": s["langtid_rate"],
    "Tid til ansettelse": tid_til_ansettelse,
}

# Lag sammenligningstabellen: én rad per metrikk i Excel.
# .map() slår opp Python-svaret for hvert metrikknavn – som XOPPSLAG.
sammenligning = definisjoner[["Metrikk", "Resultat"]].rename(
    columns={"Resultat": "Excel"}
)
sammenligning["Python"] = sammenligning["Metrikk"].map(python_svar).astype(float)

# "Stemmer" hvis forskjellen er praktisk talt null (små avrundingsrester godtas).
lik = (sammenligning["Excel"] - sammenligning["Python"]).abs() < 0.0001
sammenligning["Stemmer"] = lik.map({True: "ja", False: "nei"})
sammenligning["Forklaring"] = sammenligning["Metrikk"].map(FORKLARING).fillna("")

antall_hver_maaned = [b.antall_ansatt_paa(ansatte, dag) for dag in maanedsslutter]
print(f"Periode: {PERIODESTART:%d.%m.%Y}–{PERIODESLUTT:%d.%m.%Y} ({len(maanedsslutter)} mnd)")
print(f"Ansatte ved hver månedsslutt: {antall_hver_maaned}")
print()
print(sammenligning.round(3).to_string(index=False))

# Alle avvik skal være forklart – ellers er noe galt
uforklart = sammenligning[(sammenligning["Stemmer"] == "nei") & (sammenligning["Forklaring"] == "")]
print()
print("Alle avvik er forklart." if uforklart.empty
      else f"UFORKLARTE AVVIK: {', '.join(uforklart['Metrikk'])}")

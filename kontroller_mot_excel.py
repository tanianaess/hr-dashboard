# Kontrollskript: regner ut metrikkene for de 20 testradene i Datamodell.xlsx
# etter definisjonene i CLAUDE.md, og sammenligner med Excel-svarene i
# arket Definisjoner.
#
# Kjør slik:  python kontroller_mot_excel.py

import pandas as pd

FIL = "Datamodell.xlsx"

# Perioden vi måler – samme startdato som Excel-utkastet bruker (1.10.2025).
# Disse to linjene er som egne celler for periodestart og periodeslutt i Excel.
PERIODESTART = pd.Timestamp("2025-10-01")
PERIODESLUTT = pd.Timestamp("2026-09-30")

# Avganger som teller i turnover: stillingen må erstattes (se CLAUDE.md).
# «kontrakt utløpt» er bevisst ikke med.
TELLER_I_TURNOVER = ["frivillig", "ufrivillig", "pensjon"]


# --- 1. Les arkene -----------------------------------------------------------
# Hvert ark blir en egen tabell (DataFrame), akkurat som arkfanene i Excel.
ansatte = pd.read_excel(FIL, sheet_name="Ansatte")
fravaer = pd.read_excel(FIL, sheet_name="Fravær")
definisjoner = pd.read_excel(FIL, sheet_name="Definisjoner")


# --- 2. Hjelpefunksjon: hvor mange var ansatt på en bestemt dato? -------------
# En funksjon er en formel vi lager selv og kan bruke flere ganger.
def antall_ansatt_paa(dato):
    # Startet senest denne dagen ...
    har_startet = ansatte["ansattdato"] <= dato
    # ... og har ikke sluttet ennå (tom sluttdato, eller sluttdato er i dag
    # eller senere – sluttdato er siste arbeidsdag).
    ikke_sluttet = ansatte["sluttdato"].isna() | (ansatte["sluttdato"] >= dato)
    # "&" betyr OG, "|" betyr ELLER – som i ANTALL.HVIS.SETT.
    # .sum() teller radene der begge er sanne.
    return (har_startet & ikke_sluttet).sum()


# --- 3. Antall ansatte --------------------------------------------------------
ved_start = antall_ansatt_paa(PERIODESTART)
ved_slutt = antall_ansatt_paa(PERIODESLUTT)

# Siste dag i hver måned i perioden (31.10.2025, 30.11.2025 … 30.09.2026).
maanedsslutter = pd.date_range(PERIODESTART, PERIODESLUTT, freq="ME")
# int() gjør svaret om til et vanlig heltall, så det skrives pent ut.
antall_hver_maaned = [int(antall_ansatt_paa(dag)) for dag in maanedsslutter]
snitt_ansatte = sum(antall_hver_maaned) / len(antall_hver_maaned)

# Annualisering: gang opp til helår hvis perioden ikke er 12 måneder.
antall_maaneder = len(maanedsslutter)
til_helaar = 12 / antall_maaneder


# --- 4. Turnover --------------------------------------------------------------
# Filtrer (som autofilter) til dem som sluttet innenfor perioden.
sluttet_i_perioden = ansatte[
    (ansatte["sluttdato"] >= PERIODESTART) & (ansatte["sluttdato"] <= PERIODESLUTT)
]
# Behold bare avganger der stillingen må erstattes.
teller = sluttet_i_perioden[sluttet_i_perioden["sluttårsak"].isin(TELLER_I_TURNOVER)]

frivillige = teller[teller["sluttårsak"] == "frivillig"]
# Regel i CLAUDE.md: «uønsket» kan bare være ja når sluttårsak er frivillig.
uonskede = frivillige[frivillige["uønsket"] == "ja"]

antall_sluttet = len(teller)
antall_frivillig = len(frivillige)
antall_uonsket = len(uonskede)

# Kostnad: sum årslønn for de uønskede × 75 % – som SUMMERHVIS(...) * 0,75
kostnad_uonsket = uonskede["årslønn"].sum() * 0.75


# --- 5. Sykefravær ------------------------------------------------------------
# Bare måneder innenfor perioden. "måned" er tekst (ÅÅÅÅ-MM), så vi gjør den om
# til en dato (første dag i måneden) før vi sammenligner.
maaned_som_dato = pd.to_datetime(fravaer["måned"], format="%Y-%m")
fravaer_i_perioden = fravaer[
    (maaned_som_dato >= PERIODESTART) & (maaned_som_dato <= PERIODESLUTT)
]

# NB: Avtalte dagsverk tas fra Fravær-arket her. I den ferdige versjonen regnes
# de ut fra Ansatte, men de 20 testradene er bare et utvalg og dekker ikke hele
# teamene som Fravær-arket beskriver.
avtalte = fravaer_i_perioden["avtalte_dagsverk"].sum()
tapte_kort = fravaer_i_perioden["tapte_dagsverk_korttid"].sum()
tapte_lang = fravaer_i_perioden["tapte_dagsverk_langtid"].sum()

sykefravaer = (tapte_kort + tapte_lang) / avtalte
langtidsfravaer = tapte_lang / avtalte


# --- 6. Tid til ansettelse ----------------------------------------------------
# Etter CLAUDE.md: bare dem som ble ansatt i perioden. Excel-utkastet har
# dager_til_ansettelse i stedet for utlysningsdato og aksept_dato, så vi
# bruker den kolonnen her.
ansatt_i_perioden = ansatte[
    (ansatte["ansattdato"] >= PERIODESTART) & (ansatte["ansattdato"] <= PERIODESLUTT)
]
tid_til_ansettelse = ansatt_i_perioden["dager_til_ansettelse"].median()


# --- 7. Sammenlign med Excel --------------------------------------------------
# Python-svarene, med samme navn som i Metrikk-kolonnen i Excel.
python_svar = {
    "Sluttet totalt": antall_sluttet,
    "Sa opp selv": antall_frivillig,
    "Uønsket turnover (antall)": antall_uonsket,
    "Ansatte ved periodestart": ved_start,
    "Ansatte nå": ved_slutt,
    "Snitt ansatte": snitt_ansatte,
    "Total turnover": antall_sluttet / snitt_ansatte * til_helaar,
    "Frivillig turnover": antall_frivillig / snitt_ansatte * til_helaar,
    "Uønsket turnover": antall_uonsket / snitt_ansatte * til_helaar,
    "Kostnad uønsket turnover": kostnad_uonsket,
    "Sykefravær": sykefravaer,
    "Langtidsfravær": langtidsfravaer,
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

print(f"Periode: {PERIODESTART.date()} – {PERIODESLUTT.date()} ({antall_maaneder} mnd)")
print(f"Ansatte ved hver månedsslutt: {antall_hver_maaned}")
print()
print(sammenligning.round(3).to_string(index=False))

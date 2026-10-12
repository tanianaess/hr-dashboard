# Formler for dashbordet – som et eget beregningsark i Excel.
# Sidene i dashbordet henter tallene herfra, så hver formel finnes bare ett sted.
# Alle definisjoner følger CLAUDE.md.

from pathlib import Path

import pandas as pd

# Mappa med CSV-filene (ligger ved siden av denne fila)
DATAMAPPE = Path(__file__).parent / "data"

# Første og siste dag dataene dekker
DATA_FRA = pd.Timestamp("2024-10-01")
DATA_TIL = pd.Timestamp("2026-09-30")

# Avganger som teller i turnover: stillingen må erstattes (se CLAUDE.md)
TELLER_I_TURNOVER = ["frivillig", "ufrivillig", "pensjon"]

# Femregelen: grupper med færre enn 5 skjules
MIN_GRUPPE = 5

# Merking som vises øverst på alle sider (se «Presentasjon» i CLAUDE.md)
SYNTETISK_MERKNAD = (
    "**Syntetiske data.** Alle tall i dette dashbordet er oppdiktet og konstruert "
    "for å illustrere metodikk. De er ikke ekte funn om noe selskap."
)

TEAM = ["teknologi", "produktutvikling", "salg", "kundesuksess",
        "markedsføring", "økonomi og hr", "ledergruppen"]


# --- Lese data ----------------------------------------------------------------

def les_ansatte():
    """Leser ansatte.csv og gjør datokolonnene om til ekte datoer."""
    return pd.read_csv(
        DATAMAPPE / "ansatte.csv",
        parse_dates=["ansattdato", "sluttdato", "utlysningsdato", "aksept_dato"],
    )


# --- Datoer og perioder -------------------------------------------------------

def maanedsslutt(dato):
    """Siste dag i måneden – som MÅNEDSSLUTT(dato; 0) i Excel."""
    return dato + pd.offsets.MonthEnd(0)


def maanedsslutter(start, slutt):
    """Alle månedsslutter i perioden, f.eks. 31.10, 30.11 … 30.09."""
    return pd.date_range(start, slutt, freq="ME")


def forrige_periode(start, slutt):
    """Perioden med samme lengde rett før. 12 mnd fra okt 2025 → 12 mnd fra okt 2024."""
    antall = len(maanedsslutter(start, slutt))
    forrige_start = start - pd.DateOffset(months=antall)
    forrige_slutt = start - pd.Timedelta(days=1)
    return forrige_start, forrige_slutt


# --- Antall ansatte -----------------------------------------------------------

def antall_ansatt_paa(ansatte, dato):
    """Hvor mange var ansatt denne dagen? Startet senest i dag, og har ikke sluttet
    før i dag (sluttdato er siste arbeidsdag). Som ANTALL.HVIS.SETT med to krav."""
    har_startet = ansatte["ansattdato"] <= dato
    ikke_sluttet = ansatte["sluttdato"].isna() | (ansatte["sluttdato"] >= dato)
    return int((har_startet & ikke_sluttet).sum())


def snitt_ansatte(ansatte, start, slutt):
    """Gjennomsnitt av antall ansatte ved hver månedsslutt i perioden."""
    dager = maanedsslutter(start, slutt)
    return sum(antall_ansatt_paa(ansatte, dag) for dag in dager) / len(dager)


# --- Turnover -----------------------------------------------------------------

def sluttet_i_perioden(ansatte, start, slutt):
    """Alle som sluttet i perioden, uansett sluttårsak (som et autofilter på sluttdato)."""
    return ansatte[(ansatte["sluttdato"] >= start) & (ansatte["sluttdato"] <= slutt)]


def turnover(ansatte, start, slutt):
    """Regner ut alle turnovertall for en gruppe ansatte og en periode.
    Svaret er en «oppslagsliste» (dict): navn → verdi."""
    sluttet = sluttet_i_perioden(ansatte, start, slutt)
    teller = sluttet[sluttet["sluttårsak"].isin(TELLER_I_TURNOVER)]
    frivillig = teller[teller["sluttårsak"] == "frivillig"]
    uonsket = frivillig[frivillig["uønsket"] == "ja"]

    snitt = snitt_ansatte(ansatte, start, slutt)
    # Annualisering: gang opp til helår hvis perioden ikke er 12 måneder
    til_helaar = 12 / len(maanedsslutter(start, slutt))

    def rate(antall):
        return antall / snitt * til_helaar if snitt > 0 else None

    return {
        "snitt_ansatte": snitt,
        "avganger": len(teller),
        "frivillig": len(frivillig),
        "ufrivillig": int((teller["sluttårsak"] == "ufrivillig").sum()),
        "pensjon": int((teller["sluttårsak"] == "pensjon").sum()),
        "uønsket": len(uonsket),
        "kontrakt_utløpt": int((sluttet["sluttårsak"] == "kontrakt utløpt").sum()),
        "total_rate": rate(len(teller)),
        "frivillig_rate": rate(len(frivillig)),
        "uønsket_rate": rate(len(uonsket)),
        "lønn_uønsket": int(uonsket["årslønn"].sum()),
    }


def turnover_per_team(ansatte, start, slutt, team_liste=TEAM):
    """Én rad per team – som en pivottabell. Femregelen er bygd inn:
    - team med færre enn 5 ansatte (i snitt): alt skjules
    - fordeling på sluttårsak og uønsket: bare når teamet har minst 5 avganger
    Skjulte tall settes til None (tom celle)."""
    rader = []
    for team in team_liste:
        t = turnover(ansatte[ansatte["team"] == team], start, slutt)
        rad = {"team": team, **t}
        if t["snitt_ansatte"] < MIN_GRUPPE:
            for felt in t:
                rad[felt] = None
            rad["skjult"] = "lite team"
        elif t["avganger"] < MIN_GRUPPE:
            for felt in ["frivillig", "ufrivillig", "pensjon", "uønsket", "kontrakt_utløpt",
                         "frivillig_rate", "uønsket_rate"]:
                rad[felt] = None
            rad["skjult"] = "få avganger"
        else:
            rad["skjult"] = ""
        rad.pop("lønn_uønsket")  # Lønn vises aldri per team
        rader.append(rad)
    return pd.DataFrame(rader)


def avganger_per_maaned(ansatte, start, slutt):
    """Avganger som teller i turnover, per måned, delt i uønsket og øvrige.
    Alle måneder i perioden er med, også de uten avganger (0)."""
    sluttet = sluttet_i_perioden(ansatte, start, slutt)
    teller = sluttet[sluttet["sluttårsak"].isin(TELLER_I_TURNOVER)]
    er_uonsket = (teller["sluttårsak"] == "frivillig") & (teller["uønsket"] == "ja")
    maaned = teller["sluttdato"].dt.strftime("%Y-%m")

    alle_maaneder = [d.strftime("%Y-%m") for d in maanedsslutter(start, slutt)]
    tabell = pd.DataFrame({
        "Uønsket": er_uonsket.groupby(maaned).sum(),
        "Øvrige": (~er_uonsket).groupby(maaned).sum(),
    })
    # reindex = sørg for at alle måneder er med, tomme fylles med 0
    return tabell.reindex(alle_maaneder, fill_value=0).astype(int)


# --- Formatering (norsk tallformat) -------------------------------------------

def prosent(andel, desimaler=1):
    """0.143 → «14,3 %». Tom verdi → «–»."""
    if andel is None or pd.isna(andel):
        return "–"
    return f"{andel * 100:.{desimaler}f} %".replace(".", ",")


def prosent_med_n(teller, nevner):
    """Prosent med n, for små grupper: «12,5 % (1 av 8)»."""
    if not nevner:
        return "–"
    return f"{prosent(teller / nevner)} ({teller} av {nevner})"


def kroner(belop):
    """2700000 → «2 700 000 kr»."""
    return f"{belop:,.0f} kr".replace(",", " ")

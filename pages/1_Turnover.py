# Turnoversiden: hvor mange slutter, hvem vi ville beholdt, og hva det koster.
# Alle formler ligger i beregninger.py – her henter vi bare tallene og viser dem.

import pandas as pd
import streamlit as st

import beregninger as b

st.set_page_config(page_title="Turnover – HR-dashbord", layout="wide")


# --- Data ---------------------------------------------------------------------
# @st.cache_data: les fila bare én gang, ikke på nytt hver gang du klikker.
@st.cache_data
def hent_ansatte():
    return b.les_ansatte()


ansatte = hent_ansatte()


# --- Filtre (i sidemenyen) ------------------------------------------------------
st.sidebar.header("Filter")

# Liste med alle måneder i dataene: «2024-10», «2024-11» … «2026-09»
alle_maaneder = [d.strftime("%Y-%m") for d in b.maanedsslutter(b.DATA_FRA, b.DATA_TIL)]
fra_mnd, til_mnd = st.sidebar.select_slider(
    "Periode", options=alle_maaneder, value=("2025-10", "2026-09")
)
valgte_team = st.sidebar.multiselect("Team", b.TEAM, default=b.TEAM)

if not valgte_team:
    st.info("Velg minst ett team i filteret til venstre.")
    st.stop()  # Stopp siden her – resten gir ikke mening uten team

# Gjør «2025-10» om til 1.10.2025, og «2026-09» om til 30.09.2026
start = pd.Timestamp(f"{fra_mnd}-01")
slutt = b.maanedsslutt(pd.Timestamp(f"{til_mnd}-01"))
antall_mnd = len(b.maanedsslutter(start, slutt))

# Filtrer til valgte team – som autofilter på team-kolonnen
utvalg = ansatte[ansatte["team"].isin(valgte_team)]
hele_selskapet = len(valgte_team) == len(b.TEAM)


# --- Overskrift og merking --------------------------------------------------------
st.title("Turnover")
st.warning(b.SYNTETISK_MERKNAD, icon="⚠️")
st.caption(
    f"Periode: {start:%d.%m.%Y}–{slutt:%d.%m.%Y} ({antall_mnd} mnd). "
    f"Utvalg: {'hele selskapet' if hele_selskapet else ', '.join(valgte_team)}. "
    "Ratene er omregnet til helår når perioden ikke er 12 måneder."
)


# --- Regn ut tallene ----------------------------------------------------------------
naa = b.turnover(utvalg, start, slutt)

forrige_start, forrige_slutt = b.forrige_periode(start, slutt)
har_forrige = forrige_start >= b.DATA_FRA  # finnes det data for forrige periode?
forrige = b.turnover(utvalg, forrige_start, forrige_slutt) if har_forrige else None

# Femregelen for utvalget (se CLAUDE.md)
if naa["snitt_ansatte"] < b.MIN_GRUPPE:
    st.warning("Utvalget har færre enn 5 ansatte. Tallene skjules av personvernhensyn.")
    st.stop()

# Fordeling på frivillig/uønsket: alltid for hele selskapet, ellers bare med minst 5 avganger
vis_fordeling = hele_selskapet or naa["avganger"] >= b.MIN_GRUPPE
vis_fordeling_forrige = har_forrige and (hele_selskapet or forrige["avganger"] >= b.MIN_GRUPPE)


# --- KPI-kort -------------------------------------------------------------------------
def endring(navn, kan_vises=True):
    """Endring mot forrige periode i prosentpoeng, f.eks. «+3,1 pp»."""
    if not (har_forrige and kan_vises):
        return None
    return b.endring_pp(naa[navn], forrige[navn])


snitt = round(naa["snitt_ansatte"])
kort1, kort2, kort3 = st.columns(3)  # tre kolonner ved siden av hverandre

kort1.metric(
    "Total turnover",
    b.prosent(naa["total_rate"]),
    delta=endring("total_rate"),
    delta_color=b.pilfarge(endring("total_rate")),  # høyere turnover = dårlig = rød pil
)
kort1.caption(f"{naa['avganger']} avganger, snitt {snitt} ansatte")

if vis_fordeling:
    kort2.metric("Frivillig turnover", b.prosent(naa["frivillig_rate"]),
                 delta=endring("frivillig_rate", vis_fordeling_forrige),
                 delta_color=b.pilfarge(endring("frivillig_rate", vis_fordeling_forrige)))
    kort2.caption(f"{naa['frivillig']} sa opp selv")
    kort3.metric("Uønsket turnover", b.prosent(naa["uønsket_rate"]),
                 delta=endring("uønsket_rate", vis_fordeling_forrige),
                 delta_color=b.pilfarge(endring("uønsket_rate", vis_fordeling_forrige)))
    kort3.caption(f"{naa['uønsket']} vi ville beholdt")
else:
    kort2.metric("Frivillig turnover", "Skjult")
    kort3.metric("Uønsket turnover", "Skjult")
    kort2.caption("Færre enn 5 avganger i utvalget – fordelingen vises bare for hele selskapet.")

if har_forrige:
    st.caption(f"Pilene viser endring mot {forrige_start:%m.%Y}–{forrige_slutt:%m.%Y}, i prosentpoeng (pp).")
else:
    st.caption("Ingen sammenligning: forrige periode ligger før datastart (okt 2024).")


# --- Kostnad ved uønsket turnover -------------------------------------------------------
st.subheader("Kostnad ved uønsket turnover")

if hele_selskapet:
    # Glidebryter for antakelsen: hvor mye koster det å erstatte én person,
    # målt i prosent av årslønnen? (Bransjeanslag ligger ofte på 50–200 %.)
    kostnadsandel = st.slider(
        "Kostnad per avgang, i prosent av årslønn", min_value=50, max_value=200,
        value=75, step=5, format="%d %%",
    )
    kostnad = naa["lønn_uønsket"] * kostnadsandel / 100
    st.metric("Anslått kostnad", b.kroner(kostnad))
    st.caption(
        f"Sum årslønn for de {naa['uønsket']} uønskede avgangene × {kostnadsandel} %. "
        "Prosentsatsen er en antakelse (dekker rekruttering, opplæring og tapt "
        "produktivitet) – juster den med glidebryteren."
    )
else:
    st.info("Kostnaden vises bare for hele selskapet, fordi den bygger på lønn "
            "(lønn vises aldri per team). Velg alle team for å se den.")


# --- Graf: avganger per måned -----------------------------------------------------------
st.subheader("Avganger per måned")
per_maaned = b.avganger_per_maaned(utvalg, start, slutt)

if vis_fordeling:
    # Stablede stolper: uønsket og øvrige oppå hverandre
    st.bar_chart(per_maaned, y=["Uønsket", "Øvrige"], color=["#d1495b", "#9aa5b1"])
else:
    # Bare totalen – fordelingen er skjult for små utvalg
    st.bar_chart(per_maaned.sum(axis=1).rename("Avganger"))
st.caption("Avganger som teller i turnover (frivillig, ufrivillig, pensjon). "
           "Utløpte midlertidige kontrakter er ikke med.")


# --- Tabell per team --------------------------------------------------------------------
st.subheader("Turnover per team")

per_team = b.turnover_per_team(ansatte, start, slutt, valgte_team)
SKJULT = "skjult"


def tekst(verdi):
    """Antall som tekst – tom verdi (skjult av femregelen) blir «skjult»."""
    return SKJULT if pd.isna(verdi) else str(int(verdi))


def tabellrad(navn, t, skjult=""):
    """Gjør én rad med tall om til ferdig formatert tekst for tabellen."""
    if skjult == "lite team":
        return {"Team": navn, "Snitt ansatte": "under 5", "Turnover": SKJULT, "Avganger": SKJULT,
                "Frivillig": SKJULT, "Ufrivillig": SKJULT, "Pensjon": SKJULT,
                "Uønsket": SKJULT, "Kontrakt utløpt": SKJULT}
    snitt_rad = round(t["snitt_ansatte"])
    return {
        "Team": navn,
        "Snitt ansatte": str(snitt_rad),
        # n ved siden av prosenten, f.eks. «20,7 % (8 av 39)»
        "Turnover": f"{b.prosent(t['total_rate'])} ({int(t['avganger'])} av {snitt_rad})",
        "Avganger": tekst(t["avganger"]),
        "Frivillig": tekst(t["frivillig"]),
        "Ufrivillig": tekst(t["ufrivillig"]),
        "Pensjon": tekst(t["pensjon"]),
        "Uønsket": tekst(t["uønsket"]),
        "Kontrakt utløpt": tekst(t["kontrakt_utløpt"]),
    }


rader = [tabellrad(r["team"], r, r["skjult"]) for _, r in per_team.iterrows()]
if hele_selskapet:
    rader.append(tabellrad("Hele selskapet", naa))  # totalrad – alltid med fordeling

st.dataframe(pd.DataFrame(rader), hide_index=True, width="stretch")
st.caption(
    "Turnover = avganger / snitt antall ansatte (ved månedsslutt), omregnet til helår. "
    "«Kontrakt utløpt» teller ikke i turnover (stillingen skal ikke erstattes). "
    "**Femregelen:** team med under 5 ansatte skjules helt. Fordelingen på sluttårsak og "
    "uønsket vises bare for team med minst 5 avganger – ellers bare for hele selskapet."
)

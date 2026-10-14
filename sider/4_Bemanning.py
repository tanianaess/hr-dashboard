# Bemanningssiden: faktisk antall ansatte mot bemanningsplanen, per team og over tid.
# Alle formler ligger i beregninger.py.

import pandas as pd
import streamlit as st

import beregninger as b
from filtre import vis_filtre

st.set_page_config(page_title="Bemanning – HR-dashbord", layout="wide")


# --- Data ---------------------------------------------------------------------
@st.cache_data
def hent_data():
    return b.les_ansatte(), b.les_bemanningsplan()


ansatte, plan = hent_data()


# --- Filtre (felles for alle sider, se filtre.py) ---------------------------------
start, slutt, valgte_team, hele_selskapet = vis_filtre()
utvalg_ansatte = ansatte[ansatte["team"].isin(valgte_team)]
utvalg_plan = plan[plan["team"].isin(valgte_team)]


# --- Overskrift og merking --------------------------------------------------------
st.title("Bemanning")
st.warning(b.SYNTETISK_MERKNAD, icon="⚠️")
st.caption(
    f"Periode: {start:%d.%m.%Y}–{slutt:%d.%m.%Y}. "
    f"Utvalg: {'hele selskapet' if hele_selskapet else ', '.join(valgte_team)}. "
    "Antall personer (ikke årsverk), alle ansettelsesformer."
)


# --- Regn ut tallene ----------------------------------------------------------------
per_team = b.bemanning_per_team(ansatte, plan, start, slutt, valgte_team)
faktisk = int(per_team["faktisk"].sum())
planlagt = int(per_team["plan"].sum())
avvik = faktisk - planlagt


def med_fortegn(tall):
    """+2, −14 eller 0 – fortegn gjør retningen tydelig uten farge."""
    return f"{tall:+d}" if tall else "0"


# --- KPI-kort (nøytrale – ingen røde/grønne piler) -----------------------------------
kort1, kort2, kort3 = st.columns(3)
kort1.metric("Faktisk antall ansatte", faktisk)
kort1.caption(f"Per {slutt:%d.%m.%Y}, herav {int(per_team['midlertidige'].sum())} midlertidige")
kort2.metric("Planlagt antall", planlagt)
kort2.caption(f"Bemanningsplan for {slutt:%m.%Y}")
# Samme 5 %-regel som i tabellen: ◆ i overskriften og forklaring under
markert = b.over_avviksgrense(faktisk, planlagt)
kort3.metric("Avvik mot plan ◆" if markert else "Avvik mot plan", med_fortegn(avvik))
kort3.caption(
    f"Bemanningsgrad {b.prosent(faktisk / planlagt if planlagt else None)}"
    + (f" · ◆ mer enn {b.prosent(b.AVVIK_GRENSE, 0)} fra planen" if markert else "")
)


# --- Graf: faktisk mot plan per måned ------------------------------------------------
st.subheader("Faktisk mot plan per måned")
per_maaned = b.bemanning_per_maaned(utvalg_ansatte, utvalg_plan, start, slutt)
# «Lang» tabell: én rad per måned og serie (som å oppheve pivot i Excel)
graf_data = (per_maaned.melt(id_vars="måned", var_name="serie", value_name="antall")
             .rename(columns={"måned": "maaned"}))

st.vega_lite_chart(
    graf_data,
    {
        "height": 300,
        "mark": {"type": "line", "point": True},
        "encoding": {
            "x": {"field": "maaned", "type": "ordinal", "title": None},
            "y": {"field": "antall", "type": "quantitative", "title": "Antall ansatte",
                  "scale": {"zero": False}},
            # Nøytrale farger: plan grå og stiplet, faktisk blå
            "color": {"field": "serie", "type": "nominal", "title": None,
                      "scale": {"domain": ["Faktisk", "Plan"], "range": ["#2e86ab", "#8a8f98"]}},
            "strokeDash": {"field": "serie", "type": "nominal", "legend": None,
                           "scale": {"domain": ["Faktisk", "Plan"], "range": [[1, 0], [6, 4]]}},
            "tooltip": [{"field": "maaned", "title": "Måned"},
                        {"field": "serie", "title": "Serie"},
                        {"field": "antall", "title": "Antall"}],
        },
    },
    width="stretch",
)
st.caption("Antall ansatte ved utgangen av hver måned. Y-aksen starter ikke på null, "
           "slik at avviket blir synlig. Velg ett team i filteret for å se det teamet alene.")


# --- Tabell per team --------------------------------------------------------------------
st.subheader("Bemanning per team")

rader = []
for _, r in per_team.iterrows():
    tiltredelse = ("–" if r["tiltredelse_n"] == 0
                   else f"{b.avrund(r['tiltredelse_median'])} dager (n = {int(r['tiltredelse_n'])})")
    rader.append({
        "": "◆" if r["markert"] else "",
        "Team": r["team"],
        "Plan": int(r["plan"]),
        "Faktisk": int(r["faktisk"]),
        "Herav midlertidige": int(r["midlertidige"]),
        "Avvik": med_fortegn(int(r["avvik"])),
        "Bemanningsgrad": b.prosent(r["bemanningsgrad"]),
        "Ansettelser i perioden": int(r["ansettelser"]),
        "Avganger i perioden": int(r["avganger"]),
        "Tid til tiltredelse (median)": tiltredelse,
    })
tabell = pd.DataFrame(rader)


def marker_rad(rad):
    """Nøytral blågrå bakgrunn på team med mer enn 5 % avvik (i begge retninger)."""
    farge = "background-color: #e3e9f2" if rad[""] == "◆" else ""
    return [farge] * len(rad)


# .style.apply = betinget formatering, som i Excel
st.dataframe(tabell.style.apply(marker_rad, axis=1), hide_index=True, width="stretch")
st.caption(
    f"**◆ = avvik på mer enn {b.prosent(b.AVVIK_GRENSE, 0)} fra planen**, i begge retninger. "
    "Plan og faktisk gjelder ved periodeslutt. Faktisk teller alle ansettelsesformer – "
    "«herav midlertidige» viser hvor mange av dem som er vikarer. Avganger er alle "
    "sluttårsaker, også utløpte kontrakter. "
    "**Tid til tiltredelse** = dager fra utlysning til første arbeidsdag (inkluderer "
    "oppsigelsestid), median for ansettelser i perioden."
)
st.info(
    "**Stillinger på vei inn vises ikke.** Dataene er et øyeblikksbilde per 30.09.2026, "
    "og personer som har takket ja, men ikke startet ennå, er ikke med. Et team kan derfor "
    "ha færre ledige stillinger enn avviket tyder på.",
    icon="ℹ️",
)

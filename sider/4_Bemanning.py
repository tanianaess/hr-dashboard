# Bemanningssiden: faktisk antall ansatte mot bemanningsplanen, per team og over tid.
# Alle formler ligger i beregninger.py.

import pandas as pd
import streamlit as st

import beregninger as b
import datalasting as d
import utseende as u
from filtre import IKONER, SPORSMAL, vis_filtre

st.set_page_config(page_title="Bemanning · HR-dashbord", layout="wide")


# --- Data (felles innlesing, lest bare én gang – se datalasting.py) ----------------
ansatte, plan = d.hent_ansatte(), d.hent_bemanningsplan()


# --- Filtre (felles for alle sider, se filtre.py) ---------------------------------
start, slutt, valgte_team, hele_selskapet = vis_filtre()
utvalg_ansatte = ansatte[ansatte["team"].isin(valgte_team)]
utvalg_plan = plan[plan["team"].isin(valgte_team)]


# --- Overskrift og merking --------------------------------------------------------
u.topp("Bemanning", SPORSMAL["Bemanning"], IKONER["Bemanning"])
st.caption(
    f"Periode: {start:%d.%m.%Y}-{slutt:%d.%m.%Y}. "
    f"Utvalg: {'hele selskapet' if hele_selskapet else ', '.join(valgte_team)}. "
    "Plan og avvik i antall personer (planen er i personer). Faktisk vises også i "
    "årsverk, alle ansettelsesformer."
)


# --- Regn ut tallene ----------------------------------------------------------------
per_team = b.bemanning_per_team(ansatte, plan, start, slutt, valgte_team)
faktisk = int(per_team["faktisk"].sum())
planlagt = int(per_team["plan"].sum())
avvik = faktisk - planlagt


# --- KPI-kort (nøytrale – ingen røde/grønne piler) -----------------------------------
kort1, kort2, kort3 = st.columns(3)
kort1.metric("Faktisk antall ansatte", faktisk)
aarsverk = f"{b.avrund(per_team['faktisk_aarsverk'].sum(), 1):.1f}".replace(".", ",")  # bare tallet får komma
kort1.caption(f"Per {slutt:%d.%m.%Y}: {aarsverk} årsverk, "
              f"herav {int(per_team['midlertidige'].sum())} midlertidige ansatte")
kort2.metric("Planlagt antall", planlagt)
kort2.caption(f"Bemanningsplan for {slutt:%m.%Y}")
# Samme 5 %-regel som i tabellen: ◆ i overskriften og forklaring under
markert = b.over_avviksgrense(faktisk, planlagt)
kort3.metric("Avvik mot plan ◆" if markert else "Avvik mot plan", b.fortegn(avvik))
kort3.caption(
    f"Bemanningsgrad {b.prosent(faktisk / planlagt if planlagt else None)}."
    + (f" ◆ Mer enn {b.prosent(b.AVVIK_GRENSE, 0)} fra planen." if markert else "")
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
                      "scale": {"domain": ["Faktisk", "Plan"], "range": [u.PETROL, u.NOYTRAL]}},
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
    if r["tiltredelse_n"] == 0:
        tiltredelse = "–"
    elif pd.isna(r["tiltredelse_median"]):
        tiltredelse = b.SKJULT_UNDER_5  # femregelen: medianen bygger på for få
    else:
        tiltredelse = f"{b.avrund(r['tiltredelse_median'])} dager (n = {int(r['tiltredelse_n'])})"
    rader.append({
        "": "◆" if r["markert"] else "",
        "Team": r["team"],
        "Plan": int(r["plan"]),
        "Faktisk": int(r["faktisk"]),
        "Faktisk årsverk": f"{b.avrund(r['faktisk_aarsverk'], 1):.1f}".replace(".", ","),
        "Herav midlertidige": int(r["midlertidige"]),
        "Avvik": b.fortegn(int(r["avvik"])),
        "Bemanningsgrad": b.prosent(r["bemanningsgrad"]),
        "Ansettelser i perioden": int(r["ansettelser"]),
        "Avganger i perioden": int(r["avganger"]),
        "Tid til tiltredelse (median)": tiltredelse,
    })
tabell = pd.DataFrame(rader)


def marker_rad(rad):
    """Nøytral blågrå bakgrunn på team med mer enn 5 % avvik (i begge retninger)."""
    farge = f"background-color: {u.MARKERT_BAKGRUNN}" if rad[""] == "◆" else ""
    return [farge] * len(rad)


# .style.apply = betinget formatering, som i Excel
st.dataframe(tabell.style.apply(marker_rad, axis=1), hide_index=True, width="stretch")
st.caption(
    f"**◆ = avvik på mer enn {b.prosent(b.AVVIK_GRENSE, 0)} fra planen**, i begge retninger. "
    "Plan og faktisk gjelder ved periodeslutt. Faktisk teller alle ansettelsesformer, og "
    "«herav midlertidige» viser hvor mange av dem som er vikarer. Avganger er alle "
    "sluttårsaker, også utløpte kontrakter. "
    "**Tid til tiltredelse** = dager fra utlysning til første arbeidsdag (inkluderer "
    "oppsigelsestid), median for ansettelser i perioden. **Femregelen:** medianen skjules "
    "når den bygger på færre enn 5 ansettelser (med få personer ligger medianen nær ett "
    "enkelt forløp)."
)
st.info(
    "**Stillinger på vei inn vises ikke.** Dataene er et øyeblikksbilde per 30.09.2026, "
    "og personer som har takket ja, men ikke startet ennå, er ikke med. Et team kan derfor "
    "ha færre ledige stillinger enn avviket tyder på.",
    icon=":material/info:",
)

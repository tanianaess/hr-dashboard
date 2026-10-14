# Oversikt (forsiden): de viktigste tallene for hele selskapet med status, og
# automatiske, regelbaserte innsikter. Regler og terskler ligger i innsikter.py.

import pandas as pd
import streamlit as st

import beregninger as b
import datalasting as d
import innsikter as i
import utseende as u
from filtre import SIDER, forhandsvelg

st.set_page_config(page_title="Oversikt · HR-dashbord", layout="wide")


# --- Data ---------------------------------------------------------------------
@st.cache_data
def beregn_oversikt():
    ansatte, fravaer = d.hent_ansatte(), d.hent_fravaer()
    engasjement, plan = d.hent_engasjement(), d.hent_bemanningsplan()
    nokkeltall = i.nokkeltall(ansatte, fravaer, engasjement, plan)
    return nokkeltall, i.innsikter(ansatte, fravaer, engasjement, plan, nokkeltall)


nokkeltall, innsikt_liste = beregn_oversikt()


# --- Toppen av siden --------------------------------------------------------------
u.topp("Oversikt")
start, slutt = b.FASTE_PERIODER["Siste 12 mnd"]
st.caption(f"Hele selskapet, siste 12 måneder ({start:%d.%m.%Y}–{slutt:%d.%m.%Y}). "
           "Velg et tema i menyen til venstre for detaljer.")


# --- Nøkkeltall med status --------------------------------------------------------------
st.subheader("Nøkkeltall")


def vis_kort(k, nr):
    """Ett KPI-kort: tall, endring, statusmerke, forklaring og lenke til detaljene."""
    with st.container(border=True):
        pil = k.get("endring")
        st.metric(k["navn"], k["verdi"], delta=pil,
                  delta_color=b.pilfarge(pil, k.get("hoyere_er_bedre", False)) if pil else "off")
        u.statusmerke(k["status"][0], k["status"][1].capitalize())
        st.caption(k["ekstra"])
        if st.button("Detaljer", icon=":material/arrow_forward:", type="tertiary",
                     key=f"kort_{nr}"):
            forhandsvelg(SIDER[k["side"]])


for rad_start in range(0, len(nokkeltall), 4):  # fire kort per rad, med jevn luft
    kolonner = st.columns(4, gap="medium")
    for kolonne, (nr, k) in zip(kolonner, list(enumerate(nokkeltall))[rad_start:rad_start + 4]):
        with kolonne:
            vis_kort(k, nr)

with st.expander("Slik settes status"):
    st.dataframe(
        pd.DataFrame([{"Nøkkeltall": navn, "OK": t["tekst"][0], "Følg med": t["tekst"][1],
                       "Kritisk": t["tekst"][2], "Rask forverring gir minst «Følg med»": t["forverring_tekst"]}
                      for navn, t in i.TERSKLER.items()]),
        hide_index=True, width="stretch",
    )
    st.markdown(
        "- Tersklene er **skjønn** og ikke en standard. De bør settes av ledelsen.\n"
        "- **Sykefravær** måles mot et internt mål. Landssnittet "
        f"({b.prosent(b.SYKEFRAVAER_LANDSSNITT, 2)}, NAV 2025) vises bare som referanse.\n"
        "- **Kostnad** følger statusen til uønsket turnover.\n"
        "- **Bemanning** vises nøytralt uten pil, fordi avvik i begge retninger teller.\n"
        "- Status settes på de avrundede tallene som vises."
    )


# --- Hva ledelsen bør vite nå -------------------------------------------------------------
st.subheader("Hva ledelsen bør vite nå")
st.caption(
    "Regelbaserte innsikter (ikke AI) om de største avvikene. De bruker bare tall som også "
    "vises på de andre sidene, med de samme personvernreglene, og nevner aldri skjulte grupper."
)

if not innsikt_liste:
    st.success("Ingen store avvik akkurat nå.")

for nr, innsikt in enumerate(innsikt_liste):
    with st.container(border=True):
        funn, steg = st.columns([3, 2], gap="large")

        # Venstre: selve funnet
        with funn:
            st.markdown(f"##### {innsikt['tittel']}")
            st.markdown(innsikt["tekst"])
            if innsikt["merknad"]:
                st.caption(innsikt["merknad"])
            with st.container(horizontal=True):  # knappene på én rad, så brede som teksten
                for j, (side, team) in enumerate(innsikt["lenker"]):
                    # Teamet står i tittelen; knappen åpner siden med teamet forhåndsvalgt
                    if st.button(f"Se {side.lower()}", icon=":material/arrow_forward:",
                                 key=f"innsikt_{nr}_{j}",
                                 help=f"Åpner {side.lower()} med {team} valgt" if team else None):
                        forhandsvelg(SIDER[side], team)

        # Høyre: forslag til neste steg, tydelig skilt fra funnet
        with steg:
            with st.container(border=True):
                st.markdown(":material/lightbulb: **Mulig neste steg**")
                st.caption("Forslag, ikke en faglig anbefaling")
                st.markdown(innsikt["neste_steg"])

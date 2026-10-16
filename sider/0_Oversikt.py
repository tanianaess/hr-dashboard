# Oversikt (forsiden): de viktigste tallene for hele selskapet med status, og
# automatiske, regelbaserte innsikter. Regler og terskler ligger i innsikter.py.

import pandas as pd
import streamlit as st

import beregninger as b
import datalasting as d
import innsikter as i
import lederbrief as lb
import utseende as u
from filtre import IKONER, SIDER, forhandsvelg

st.set_page_config(page_title="Oversikt · HR-dashbord", layout="wide")

# Kort introduksjon: hvem dashbordet er for, og hva de trenger (Tanias formulering)
INTRO = (
    "**For ledergruppen i et selskap med 50-500 ansatte.** Dashbordet gir daglig leder, "
    "økonomidirektør og HR et felles bilde av de viktigste innsiktene rundt ansatte og HR "
    "før ledermøtet.\n\n"
    "- **Ledelsen:** Hvor er risikoen nå, hva koster den, og har vi folkene planen krever?\n"
    "- **HR-leder:** Hvilke team trenger oppfølging, og virker endringene i "
    "rekrutteringsprosessen?\n\n"
    "Start med statusen og innsiktene under, og gå til detaljsidene ved behov. Tallene "
    "gjelder alltid grupper, aldri enkeltpersoner, og tilgangen er begrenset til HR-ledelse "
    "og ledergruppen."
)

INNSIKT_FORKLARING = (
    "Regelbaserte innsikter om de største avvikene. De bruker bare tall som også vises "
    "under de andre temaene, med de samme personvernreglene, og nevner aldri skjulte grupper."
)
# Legges til etter Tanias tekst når lederbriefen vises (forslag til ordlyd, se CLAUDE.md)
AI_HENVISNING = "Lederbriefen lenger ned er skrevet av en AI-modell og er merket."


# --- Data ---------------------------------------------------------------------
@st.cache_data
def beregn_oversikt():
    ansatte, fravaer = d.hent_ansatte(), d.hent_fravaer()
    engasjement, plan = d.hent_engasjement(), d.hent_bemanningsplan()
    nokkeltall = i.nokkeltall(ansatte, fravaer, engasjement, plan)
    return (nokkeltall,
            i.innsikter(ansatte, fravaer, engasjement, plan, nokkeltall, samtaler=d.hent_en_til_en()),
            i.teamoversikt(ansatte, fravaer, engasjement, plan))


nokkeltall, innsikt_liste, team_rader = beregn_oversikt()

# Lederbriefen (AI): leses fra data/lederbrief.json og vises bare når den er lest og godkjent,
# og bygger på nøyaktig dagens tall (fingeravtrykket stemmer). Se «Lederbrief (AI)» i CLAUDE.md.
grunnlag_tekst = lb.grunnlag(nokkeltall, innsikt_liste)
brief = lb.les_lederbrief()
brief_status = lb.status(brief, grunnlag_tekst) if brief else None


# --- Toppen av siden --------------------------------------------------------------
u.topp("Oversikt", ikon=IKONER["Oversikt"], merknad=False)
u.neste_steg_stil()  # lys petrol bakgrunn på «Mulig neste steg» (se utseende.py)
u.lederbrief_stil()  # nøytral grå bakgrunn på lederbriefen (AI)

# Introduksjonen i et kort: hvem dashbordet er for (venstre) og spørsmålene (høyre), så
# den tar mindre plass og nøkkeltallene kommer høyere opp. Teksten (INTRO) er Tanias og
# uendret, bare delt på avsnittene. Setningen om syntetiske data og periodelinjen står
# rett under.
with st.container(border=True, key=f"{u.KORT_NOKKEL}intro"):
    hvem, sporsmal, bruk = INTRO.split("\n\n")
    venstre, hoyre = st.columns([3, 2], gap="medium")
    venstre.markdown(hvem)
    hoyre.markdown(sporsmal)
    st.caption(bruk)
u.syntetisk_merknad()
start, slutt = b.FASTE_PERIODER["Siste 12 mnd"]
st.caption(f"Tallene gjelder hele selskapet de siste 12 månedene "
           f"({start:%d.%m.%Y}-{slutt:%d.%m.%Y}). Velg et tema i menyen til venstre for detaljer. "
           f"Data per {b.DATA_TIL:%d.%m.%Y}. Oppdateres månedlig.")


# --- Nøkkeltall med status --------------------------------------------------------------
st.subheader("Nøkkeltall")
st.caption(i.felles_merknad(nokkeltall))


def vis_kort(k, nr):
    """Ett KPI-kort, lavt og tett: navnet og lenken til detaljene øverst, tallet og pilen
    på én linje, statusmerket med grensen, og én forklaring."""
    with st.container(border=True, key=f"{u.KORT_NOKKEL}nokkeltall_{nr}"):  # key: kortstil, se utseende.py
        # Navnet til venstre og pilknappen til høyre på én linje (også på mobil, der
        # kolonner ellers stables). Knappen har ikke tekst, teksten ligger i verktøytipset.
        with st.container(horizontal=True, horizontal_alignment="distribute",
                          vertical_alignment="center"):
            st.caption(k["navn"])
            if st.button("", icon=":material/arrow_forward:", type="tertiary", help="Detaljer",
                         key=f"detaljer_{nr}"):
                forhandsvelg(SIDER[k["side"]])
        pil = k.get("endring")
        # Etiketten er skjult (navnet står over), men ligger i kortet for testene
        st.metric(k["navn"], k["verdi"], delta=pil, label_visibility="collapsed",
                  delta_color=b.pilfarge(pil, k.get("hoyere_er_bedre", False),
                                         terskel=k.get("terskel")) if pil else "off")
        u.statusmerke(k["status"][0], k["status"][1].capitalize())
        st.caption(k["ekstra"])


for rad_start in range(0, len(nokkeltall), 4):  # fire kort per rad, med jevn luft
    kolonner = st.columns(4, gap="medium")
    for kolonne, (nr, k) in zip(kolonner, list(enumerate(nokkeltall))[rad_start:rad_start + 4]):
        with kolonne:
            vis_kort(k, nr)

st.caption(b.VESENTLIG_TEKST)


# --- Teamene på ett blikk ----------------------------------------------------------------
# Ett bilde av alle teamene: samme terskler som nøkkeltallene over, samme femregel som
# detaljsidene. Reglene ligger i teamoversikt() i innsikter.py, tegningen i utseende.py.
st.subheader("Teamene på ett blikk")
st.caption("Samme terskler som for hele selskapet (se «Slik settes status» under), siste 12 "
           "måneder, eNPS for siste kvartal. En grå rute er skjult fordi gruppen er under fem, "
           "og viser aldri tallet.")
u.rutenett(team_rader, i.SIGNALER)

with st.expander("Slik settes status"):
    st.dataframe(
        pd.DataFrame([{"Nøkkeltall": navn, "OK": t["tekst"][0], "Følg med": t["tekst"][1],
                       "Kritisk": t["tekst"][2], "Rask forverring gir minst «Følg med»": t["forverring_tekst"]}
                      for navn, t in i.TERSKLER.items()]),
        hide_index=True, width="stretch",
    )
    st.markdown(
        "- Tersklene er **skjønn** og ikke en standard. De bør settes av ledelsen, helst "
        "med bransjetall som referanse (det som er høyt i én bransje, kan være normalt "
        "i en annen).\n"
        "- **Sykefravær** måles mot et internt mål. Landssnittet "
        f"({b.prosent(b.SYKEFRAVAER_LANDSSNITT, 2)}, NAV 2025) vises bare som referanse, fordi det "
        "gjelder alle bransjer og er beregnet annerledes.\n"
        "- **Erstatningskostnad** følger total turnover, og **fraværskostnad** følger sykefravær.\n"
        "- **Tid til ansettelse** blir minst «Følg med» hvis et team er over grensen for kritisk.\n"
        "- **Bemanning** vises nøytralt uten pil, fordi avvik i begge retninger teller.\n"
        "- Status settes på de avrundede tallene som vises."
    )


# --- Viktigste innsikter -------------------------------------------------------------------
st.subheader("Viktigste innsikter")
st.caption(INNSIKT_FORKLARING + (f" {AI_HENVISNING}" if brief_status == "ok" else ""))

if not innsikt_liste:
    st.success("Ingen store avvik akkurat nå.")

for nr, innsikt in enumerate(innsikt_liste):
    with st.container(border=True, key=f"{u.KORT_NOKKEL}innsikt_{nr}"):
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
            # key gir boksen en egen CSS-klasse, så den får lys petrol bakgrunn
            with st.container(key=f"{u.NESTE_STEG_NOKKEL}{nr}"):
                st.markdown(":blue[:material/lightbulb: **Mulig neste steg**]")  # blå = petrol i temaet
                st.caption("Regelbasert forslag")
                st.markdown(innsikt["neste_steg"])


# --- Lederbrief (AI) ---------------------------------------------------------------------
# Skrevet av en AI-modell på forhånd (lag_lederbrief.py) ut fra nøyaktig de tallene som står
# over, og lest av et menneske før den vises. Stiller spørsmål, foreslår ikke tiltak.

def vis_lederbrief(brief):
    """Briefen i en egen boks med nøytral bakgrunn, tydelig merket som skrevet av AI."""
    felt = brief["brief"]
    with st.container(border=True, key=u.LEDERBRIEF_NOKKEL):
        st.badge("Skrevet av AI", icon=":material/smart_toy:", color="gray")
        st.caption(lb.merking(brief))
        st.markdown(felt["sammendrag"])
        for tema in felt["temaer"]:
            st.markdown(f"##### {tema['tittel']}")
            st.markdown(tema["hva_tallene_viser"])
            st.markdown("**Spørsmål til ledermøtet**\n\n"
                        + "\n".join(f"- {sporsmal}" for sporsmal in tema["sporsmal"]))
        st.markdown(f"**Følg med:** {felt['folg_med']}")
        st.caption(felt["forbehold"])
        # Åpenhet: leseren kan se nøyaktig hva modellen ble bedt om, og hva den fikk
        with st.expander("Hva AI-modellen fikk"):
            st.markdown("**Instruksen**")
            st.text(lb.INSTRUKS)
            st.markdown("**Grunnlaget** (det forsiden viser, som ren tekst)")
            st.text(brief["grunnlag"])
            if brief.get("merknad"):
                st.caption(brief["merknad"])
        _, slutt = b.FASTE_PERIODER["Siste 12 mnd"]
        # Til vedlegg i e-post: HTML (åpnes i nettleseren, kan skrives ut til PDF) eller Markdown
        with st.container(horizontal=True):
            st.download_button("Last ned som HTML", data=lb.som_html(brief),
                               file_name=f"lederbrief-{slutt:%Y-%m}.html", mime="text/html",
                               icon=":material/download:")
            st.download_button("Last ned som Markdown", data=lb.som_markdown(brief),
                               file_name=f"lederbrief-{slutt:%Y-%m}.md", mime="text/markdown",
                               icon=":material/download:")


if brief is not None:
    st.subheader("Lederbrief")
    if brief_status == "utdatert":
        st.caption("Lederbriefen er ikke oppdatert etter siste dataoppdatering, og vises derfor ikke.")
    elif brief_status == "ikke_godkjent":
        st.caption("Lederbriefen er laget, men ikke lest og godkjent ennå, og vises derfor ikke.")
    else:
        vis_lederbrief(brief)

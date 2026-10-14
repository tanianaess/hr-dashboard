# Felles filtre for alle sidene i dashbordet: periode og team (i sidemenyen).
# Hver side kaller vis_filtre() og får tilbake det brukeren har valgt.

import pandas as pd
import streamlit as st

import beregninger as b


def vis_filtre(standard_periode=("2025-10", "2026-09")):
    """Viser filtrene i sidemenyen og gir tilbake valgene:
    start (første dag), slutt (siste dag), valgte team, og om hele selskapet er valgt.
    Stopper siden hvis ingen team er valgt."""
    st.sidebar.header("Filter")

    # Liste med alle måneder i dataene: «2024-10», «2024-11» … «2026-09»
    alle_maaneder = [d.strftime("%Y-%m") for d in b.maanedsslutter(b.DATA_FRA, b.DATA_TIL)]
    fra_mnd, til_mnd = st.sidebar.select_slider(
        "Periode", options=alle_maaneder, value=standard_periode
    )
    valgte_team = st.sidebar.multiselect("Team", b.TEAM, default=b.TEAM)

    if not valgte_team:
        st.info("Velg minst ett team i filteret til venstre.")
        st.stop()  # Stopp siden her – resten gir ikke mening uten team

    # Gjør «2025-10» om til 1.10.2025, og «2026-09» om til 30.09.2026
    start = pd.Timestamp(f"{fra_mnd}-01")
    slutt = b.maanedsslutt(pd.Timestamp(f"{til_mnd}-01"))
    hele_selskapet = len(valgte_team) == len(b.TEAM)
    return start, slutt, valgte_team, hele_selskapet


def vis_filtre_sensitiv():
    """Begrenset filter for sider med sensitive tall (sykefravær, eNPS, turnoverfordeling):
    - periode: bare faste valg (siste 12 mnd, siste 24 mnd, kalenderår)
    - team: enten hele selskapet eller ett team om gangen
    Fritt flervalg og fri periode er bevisst ikke mulig – to utvalg som skiller seg
    med én liten gruppe kan trekkes fra hverandre. Gir tilbake det samme som vis_filtre()."""
    st.sidebar.header("Filter")
    periode = st.sidebar.selectbox("Periode", list(b.FASTE_PERIODER))
    team = st.sidebar.selectbox("Team", ["Hele selskapet", *b.TEAM])
    st.sidebar.caption(
        "På sider med sensitive tall kan du bare velge hele selskapet eller ett team, "
        "og faste perioder. Det gjør det vanskeligere å regne ut tall for små grupper."
    )
    start, slutt = b.FASTE_PERIODER[periode]
    if team == "Hele selskapet":
        return start, slutt, list(b.TEAM), True
    return start, slutt, [team], False

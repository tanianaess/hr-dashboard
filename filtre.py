# Felles filtre for alle sidene i dashbordet: periode og team (i sidemenyen).
# Hver side kaller vis_filtre() og får tilbake det brukeren har valgt.

import pandas as pd
import streamlit as st

import beregninger as b


# Navn på filtrene i session_state (Streamlits minne mellom sider)
NOKKEL_MAANEDER = "filter_maaneder"      # fritt filter: (fra_mnd, til_mnd)
NOKKEL_FLERVALG = "filter_team_flervalg"  # fritt filter: liste med team
NOKKEL_PERIODE = "filter_periode"         # begrenset filter: fast periode
NOKKEL_TEAM = "filter_team"               # begrenset filter: hele selskapet eller ett team
HELE_SELSKAPET = "Hele selskapet"

# Sider med begrenset filter (sensitive tall)
SENSITIVE_SIDER = {"sider/1_Turnover.py", "sider/2_Sykefravaer.py", "sider/5_Engasjement.py"}


def forhandsvelg(side, team=None):
    """Åpner en side med siste 12 mnd og ett team (eller hele selskapet) forhåndsvalgt.
    Brukes av lenkene på forsiden."""
    if side in SENSITIVE_SIDER:
        st.session_state[NOKKEL_PERIODE] = "Siste 12 mnd"
        st.session_state[NOKKEL_TEAM] = team or HELE_SELSKAPET
    else:
        start, slutt = b.FASTE_PERIODER["Siste 12 mnd"]
        st.session_state[NOKKEL_MAANEDER] = (f"{start:%Y-%m}", f"{slutt:%Y-%m}")
        st.session_state[NOKKEL_FLERVALG] = [team] if team else list(b.TEAM)
    st.switch_page(side)


def vis_filtre(standard_periode=("2025-10", "2026-09")):
    """Viser filtrene i sidemenyen og gir tilbake valgene:
    start (første dag), slutt (siste dag), valgte team, og om hele selskapet er valgt.
    Stopper siden hvis ingen team er valgt."""
    st.sidebar.header("Filter")

    # Liste med alle måneder i dataene: «2024-10», «2024-11» … «2026-09»
    alle_maaneder = [d.strftime("%Y-%m") for d in b.maanedsslutter(b.DATA_FRA, b.DATA_TIL)]
    # Startverdier legges i session_state (Streamlits minne) første gang. Da kan
    # forsiden forhåndsvelge et team før den åpner siden (se forhandsvelg()).
    st.session_state.setdefault(NOKKEL_MAANEDER, standard_periode)
    st.session_state.setdefault(NOKKEL_FLERVALG, list(b.TEAM))
    fra_mnd, til_mnd = st.sidebar.select_slider("Periode", options=alle_maaneder,
                                                key=NOKKEL_MAANEDER)
    valgte_team = st.sidebar.multiselect("Team", b.TEAM, key=NOKKEL_FLERVALG)

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
    st.session_state.setdefault(NOKKEL_PERIODE, "Siste 12 mnd")
    st.session_state.setdefault(NOKKEL_TEAM, HELE_SELSKAPET)
    periode = st.sidebar.selectbox("Periode", list(b.FASTE_PERIODER), key=NOKKEL_PERIODE)
    team = st.sidebar.selectbox("Team", [HELE_SELSKAPET, *b.TEAM], key=NOKKEL_TEAM)
    st.sidebar.caption(
        "På sider med sensitive tall kan du bare velge hele selskapet eller ett team, "
        "og faste perioder. Det gjør det vanskeligere å regne ut tall for små grupper."
    )
    start, slutt = b.FASTE_PERIODER[periode]
    if team == HELE_SELSKAPET:
        return start, slutt, list(b.TEAM), True
    return start, slutt, [team], False

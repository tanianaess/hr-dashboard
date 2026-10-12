# Startfila for dashbordet: lager menyen og inneholder forsiden.
#
# Start dashbordet med:  streamlit run app.py

import streamlit as st

from beregninger import SYNTETISK_MERKNAD

# Fanetittel og bred layout
st.set_page_config(page_title="HR-dashbord", layout="wide")


def forside():
    """Innholdet på forsiden."""
    st.title("HR-dashbord")
    st.warning(SYNTETISK_MERKNAD, icon="⚠️")

    st.markdown(
        """
        People analytics-dashbord for et fiktivt norsk tech-selskap med ca. 230
        ansatte i 7 team, okt 2024–sep 2026.

        **Sider** (velg i menyen til venstre):
        - **Turnover** – hvor mange slutter, hvem vi ville beholdt, og hva det koster
        - **Sykefravær** – korttid og langtid, mot samme periode i fjor og landssnittet

        **Personvern:** Dashbordet viser aldri enkeltpersoner. Små grupper skjules
        (femregelen), og antall (n) vises ved siden av prosenter.
        """
    )


# Menyen: navn, ikon og rekkefølge bestemmes her – ikke av filnavnene.
# En side kan være en funksjon (forside) eller en egen fil (turnover).
meny = st.navigation([
    st.Page(forside, title="Forside", icon="🏠", default=True),
    st.Page("sider/1_Turnover.py", title="Turnover", icon="📉"),
    st.Page("sider/2_Sykefravaer.py", title="Sykefravær", icon="🩺"),
])
meny.run()  # viser siden brukeren har valgt

# Startfila for dashbordet: lager menyen. Forsiden (oversikten) ligger i
# sider/0_Oversikt.py.
#
# Start dashbordet med:  streamlit run app.py

import streamlit as st

# Fanetittel og bred layout
st.set_page_config(page_title="HR-dashbord", layout="wide")

# Menyen: navn, ikon og rekkefølge bestemmes her – ikke av filnavnene.
meny = st.navigation([
    st.Page("sider/0_Oversikt.py", title="Oversikt", icon=":material/space_dashboard:", default=True),
    st.Page("sider/1_Turnover.py", title="Turnover", icon=":material/sync_alt:"),
    st.Page("sider/2_Sykefravaer.py", title="Sykefravær", icon=":material/healing:"),
    st.Page("sider/3_Rekruttering.py", title="Rekruttering", icon=":material/person_search:"),
    st.Page("sider/4_Bemanning.py", title="Bemanning", icon=":material/groups:"),
    st.Page("sider/5_Engasjement.py", title="Engasjement", icon=":material/forum:"),
])
meny.run()  # viser siden brukeren har valgt

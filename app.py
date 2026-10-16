# Startfilen for dashbordet: lager menyen. Forsiden (oversikten) ligger i
# sider/0_Oversikt.py.
#
# Start dashbordet med:  streamlit run app.py

import streamlit as st

from filtre import IKONER, SIDER

# Fanetittel og bred layout
st.set_page_config(page_title="HR-dashbord", layout="wide")

# Menyen: navn, ikon og rekkefølge bestemmes her – ikke av filnavnene.
# Filene og ikonene står i SIDER og IKONER (filtre.py), så menyen og overskriftene er like.
meny = st.navigation([
    st.Page(fil, title=navn, icon=IKONER[navn], default=(navn == "Oversikt"))
    for navn, fil in SIDER.items()
])
meny.run()  # viser siden brukeren har valgt

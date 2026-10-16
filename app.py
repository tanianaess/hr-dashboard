# Startfilen for dashbordet: lager menyen. Forsiden (oversikten) ligger i
# sider/0_Oversikt.py.
#
# Start dashbordet med:  streamlit run app.py

import streamlit as st

from filtre import IKONER, SEKSJONER, SIDER

# Fanetittel og bred layout
st.set_page_config(page_title="HR-dashbord", layout="wide")

# Ordmerket øverst i menyen (static/wordmark.svg): selskapsnavnet, som en logo i et
# vanlig produkt. Bare navnet, se «Utseende» i CLAUDE.md.
st.logo("static/wordmark.svg", size="large")

# Menyen: navn, ikon, rekkefølge og seksjoner bestemmes her – ikke av filnavnene.
# Filene, ikonene og seksjonene står i SIDER, IKONER og SEKSJONER (filtre.py), så menyen
# og overskriftene er like.
meny = st.navigation({
    seksjon: [st.Page(SIDER[navn], title=navn, icon=IKONER[navn], default=(navn == "Oversikt"))
              for navn in navn_liste]
    for seksjon, navn_liste in SEKSJONER.items()
})
meny.run()  # viser siden brukeren har valgt

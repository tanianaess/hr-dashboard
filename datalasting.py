# Felles innlesing av data for alle sidene. @st.cache_data lagrer svaret, så hver fil
# leses – og avtalte dagsverk regnes ut – bare én gang, uansett hvilken side du åpner.
# (Før hadde hver side sin egen kopi, og avtalte dagsverk ble regnet ut på nytt per side.)

import streamlit as st

import beregninger as b


@st.cache_data
def hent_ansatte():
    return b.les_ansatte()


@st.cache_data
def hent_fravaer():
    """Fravær med avtalte dagsverk og antall ansatte per team og måned (se beregninger.py)."""
    return b.fravaer_med_avtalte(hent_ansatte(), b.les_fravaer())


@st.cache_data
def hent_engasjement():
    return b.les_engasjement()


@st.cache_data
def hent_bemanningsplan():
    return b.les_bemanningsplan()


@st.cache_data
def hent_opplaering():
    return b.les_opplaering()


@st.cache_data
def hent_en_til_en():
    return b.les_en_til_en()


@st.cache_data
def hent_stillingsendringer():
    return b.les_stillingsendringer()

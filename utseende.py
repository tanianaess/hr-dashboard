# Felles utseende for alle sider: palett, toppen av siden og statusmerker.
# Temaet (bakgrunn, skrift, hovedfarge) ligger i .streamlit/config.toml.

import streamlit as st

import beregninger as b

SELSKAP = "Fjordlys Tech AS"

# Palett for grafer – samme på alle sider, i fast rekkefølge.
# Statusfargene (grønn/oransje/rød) brukes ALDRI til vanlige serier.
PETROL = "#0F4C5C"        # hovedserie
PETROL_LYS = "#5F93A1"    # serie 2
NOYTRAL = "#8A9499"       # plan, referanselinjer
NOYTRAL_LYS = "#C9D1D4"   # «andre team», bakgrunnsserier
TEKST_DEMPET = "#5B6770"  # etiketter og hjelpetekst i grafer
MARKERT_BAKGRUNN = "#E4EEF0"  # nøytral markering av rader (petrol-tone)

# Statusmerker: ord + symbol + farge (kan leses uten farger)
STATUS = {
    "OK": (":material/check_circle:", "green"),
    "Følg med": (":material/visibility:", "orange"),
    "Kritisk": (":material/error:", "red"),
}


def topp(tittel):
    """Toppen av hver side: selskapsnavn, tittel og diskret merking om syntetiske data."""
    st.caption(f"**{SELSKAP}** · fiktivt selskap · people analytics")
    st.title(tittel)
    st.badge("Syntetiske data", icon=":material/science:", color="gray")
    st.caption(b.SYNTETISK_MERKNAD.replace("**Syntetiske data.** ", ""))


def statusmerke(status, forklaring=None):
    """Liten merkelapp, f.eks. «✓ OK», med forklaring etter (f.eks. «10–15 %»)."""
    ikon, farge = STATUS[status]
    st.badge(status, icon=ikon, color=farge)
    if forklaring:
        st.caption(forklaring)

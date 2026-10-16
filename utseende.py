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


def syntetisk_merknad():
    """Setningen om at dataene er oppdiktet (står på alle sider)."""
    st.caption(b.SYNTETISK_MERKNAD.replace("**Syntetiske data.** ", ""))


def topp(tittel, sporsmal=None, ikon=None, merknad=True):
    """Toppen av hver side: selskapsnavn, tittel (med samme ikon som i menyen, i petrol),
    spørsmålet siden svarer på (hvis gitt) og diskret merking om syntetiske data.
    merknad=False: siden viser setningen om syntetiske data selv (forsiden, under introen)."""
    st.caption(f"**{SELSKAP}** · fiktivt selskap · people analytics")
    # :blue[…] er petrol i temaet (.streamlit/config.toml)
    st.title(f":blue[{ikon}] {tittel}" if ikon else tittel)
    if sporsmal:
        st.markdown(f":gray[{sporsmal}]")  # rolig grå tekst rett under tittelen
    st.badge("Syntetiske data", icon=":material/science:", color="gray")
    if merknad:
        syntetisk_merknad()


def skjult_kort(beholder, tittel, forklaring=b.SKJULT_UNDER_5.capitalize()):
    """KPI-kort for et tall som er skjult av personvernhensyn: «–» som verdi og
    forklaringen i liten tekst under. (Lang tekst som verdi får stor tallskrift og
    blir kuttet, f.eks. «skjult (unde…».)"""
    beholder.metric(tittel, "–")
    beholder.caption(forklaring)


# CSS-klassen Streamlit gir beholdere med key="neste_steg_…" (se forsiden)
NESTE_STEG_NOKKEL = "neste_steg_"


def neste_steg_stil():
    """Lys petrol bakgrunn på «Mulig neste steg»-boksene på forsiden.
    Én CSS-regel her, så fargen ikke spres rundt i sidene.
    Kontrast: tekst #1E2A30 på #E4EEF0 = 12,4 : 1 (krav: minst 4,5 : 1)."""
    st.html(
        f"<style>[class*='st-key-{NESTE_STEG_NOKKEL}'] {{"
        f"background-color: {MARKERT_BAKGRUNN}; border-radius: 0.5rem; padding: 1rem 1.25rem;"
        f"}}</style>"
    )


def statusmerke(status, forklaring=None):
    """Liten merkelapp, f.eks. «✓ OK», med forklaring etter (f.eks. «10-15 %»)."""
    ikon, farge = STATUS[status]
    st.badge(status, icon=ikon, color=farge)
    if forklaring:
        st.caption(forklaring)

# Engasjementssiden: eNPS per kvartal og team, svarandel, og koblingen mot
# langtidsfravær. Alle formler ligger i beregninger.py.

import pandas as pd
import streamlit as st

import beregninger as b
from filtre import vis_filtre

st.set_page_config(page_title="Engasjement – HR-dashbord", layout="wide")


# --- Data ---------------------------------------------------------------------
@st.cache_data
def hent_data():
    ansatte = b.les_ansatte()
    fravaer = b.fravaer_med_avtalte(ansatte, b.les_fravaer())
    return ansatte, fravaer, b.les_engasjement()


ansatte, fravaer, engasjement = hent_data()


# --- Filtre (felles for alle sider, se filtre.py) ---------------------------------
start, slutt, valgte_team, hele_selskapet = vis_filtre()
utvalg = engasjement[engasjement["team"].isin(valgte_team)]


# --- Overskrift og merking --------------------------------------------------------
st.title("Engasjement (eNPS)")
st.warning(b.SYNTETISK_MERKNAD, icon="⚠️")

kvartaler = b.kvartaler_i_perioden(start, slutt)
if not kvartaler:
    st.info("Perioden inneholder ingen hele kvartaler. Velg en lengre periode.")
    st.stop()

siste = kvartaler[-1]
st.caption(
    f"Kvartaler i perioden: {kvartaler[0]}–{siste}. "
    f"Utvalg: {'hele selskapet' if hele_selskapet else ', '.join(valgte_team)}."
)

with st.expander("Slik leses eNPS"):
    st.markdown(
        "eNPS (employee Net Promoter Score) bygger på spørsmålet «Hvor sannsynlig er det at "
        "du vil anbefale arbeidsplassen din til en venn?» (0–10).\n\n"
        "- **eNPS = andel anbefalere (9–10) minus andel kritikere (0–6)**, fra −100 til +100.\n"
        "- Positive tall betyr flere anbefalere enn kritikere.\n"
        "- I små grupper kan noen få svar flytte tallet mye – derfor vises antall svar (n) "
        "og svarandel alltid.\n"
        "- For flere team samlet vektes hvert team med antall svar."
    )


# --- Hjelpefunksjoner for visning ----------------------------------------------------
def enps_tekst(verdi):
    """13,6 → «+14», −14 → «−14», 0 → «0»."""
    if verdi is None or pd.isna(verdi):
        return "–"
    tall = b.avrund(verdi)
    return "0" if tall == 0 else f"{tall:+d}".replace("-", "−")


def endring_poeng(ny, gammel):
    """Endring i eNPS-poeng som tekst, f.eks. «+3 poeng». None hvis noe mangler."""
    if ny is None or gammel is None:
        return None
    diff = b.avrund(ny - gammel)
    return "±0 poeng" if diff == 0 else f"{diff:+d} poeng"


def hent(kvartal, data=utvalg):
    """Samlet eNPS for et kvartal (None hvis kvartalet mangler eller har under 5 svar)."""
    return b.enps_samlet(data[data["kvartal"] == kvartal])


# --- KPI-kort -------------------------------------------------------------------------
naa = hent(siste)
if naa is None:
    st.warning("Utvalget har færre enn 5 svar. eNPS skjules av personvernhensyn.")
    st.stop()

forrige_k, fjor_k = b.kvartal_minus(siste, 1), b.kvartal_minus(siste, 4)
forrige, fjor = hent(forrige_k), hent(fjor_k)
mot_fjor = endring_poeng(naa["enps"], fjor["enps"] if fjor else None)
mot_forrige = endring_poeng(naa["enps"], forrige["enps"] if forrige else None)
lav = naa["svarandel"] < b.LAV_SVARANDEL

kort1, kort2, kort3 = st.columns(3)
kort1.metric(f"eNPS {siste}", enps_tekst(naa["enps"]), delta=mot_fjor,
             delta_color=b.pilfarge(mot_fjor, hoyere_er_bedre=True))
kort1.caption(f"Pila viser endring mot samme kvartal i fjor ({fjor_k})" if fjor
              else "Ingen sammenligning med i fjor (mangler data)")
kort2.metric("Endring mot forrige kvartal", mot_forrige or "–")
kort2.caption(f"Fra {enps_tekst(forrige['enps'])} i {forrige_k}" if forrige else "Forrige kvartal mangler")
kort3.metric("Svarandel – lav" if lav else "Svarandel", b.prosent(naa["svarandel"], 0))
kort3.caption(f"{naa['svar']} av {naa['invitert']} invitert"
              + (f" · under {b.prosent(b.LAV_SVARANDEL, 0)} – tolk eNPS med forsiktighet" if lav else ""))


# --- Graf: eNPS per kvartal og team -----------------------------------------------------
st.subheader("eNPS per kvartal og team")

i_perioden = utvalg[utvalg["kvartal"].isin(kvartaler)]
synlig = i_perioden[i_perioden["antall_svar"] >= b.MIN_GRUPPE].copy()  # femregelen

# Uthev teamet med størst fall fra første til siste kvartal i perioden
endring_per_team = {}
for team, t in synlig.groupby("team"):
    t = t.set_index("kvartal")
    if kvartaler[0] in t.index and siste in t.index:
        endring_per_team[team] = t.loc[siste, "enps"] - t.loc[kvartaler[0], "enps"]
uthevet = min(endring_per_team, key=endring_per_team.get) if endring_per_team else None
if uthevet is not None and endring_per_team[uthevet] > -b.UTHEV_FALL:
    uthevet = None  # ingen team har falt nok til å utheves

synlig["linje"] = synlig["team"].where(synlig["team"] == uthevet, "andre team")
st.vega_lite_chart(
    synlig,
    {
        "height": 320,
        "layer": [
            {   # Nullinje: like mange anbefalere som kritikere
                "mark": {"type": "rule", "color": "#888", "strokeDash": [4, 4]},
                "encoding": {"y": {"datum": 0}},
            },
            {
                "mark": {"type": "line", "point": True},
                "encoding": {
                    "x": {"field": "kvartal", "type": "ordinal", "title": None,
                          "axis": {"labelAngle": 0}},
                    "y": {"field": "enps", "type": "quantitative", "title": "eNPS"},
                    "detail": {"field": "team"},  # én linje per team
                    "color": {"field": "linje", "type": "nominal", "title": None,
                              "scale": {"domain": [uthevet or "", "andre team"],
                                        "range": ["#2e86ab", "#c3c7cc"]}},
                    "tooltip": [{"field": "team", "title": "Team"},
                                {"field": "kvartal", "title": "Kvartal"},
                                {"field": "enps", "title": "eNPS"},
                                {"field": "antall_svar", "title": "Antall svar"}],
                },
            },
        ],
    },
    width="stretch",
)
st.caption(
    (f"Uthevet: **{uthevet}**, teamet med størst fall i perioden "
     f"({enps_tekst(endring_per_team[uthevet])} poeng). " if uthevet else "")
    + f"Et team uthevet bare ved fall på minst {b.UTHEV_FALL} poeng. "
    "Stiplet linje = 0 (like mange anbefalere som kritikere). "
    "Team-kvartaler med under 5 svar vises ikke (femregelen)."
)


# --- Tabell per team --------------------------------------------------------------------
st.subheader("eNPS per team")
SKJULT = "skjult"
rader = []
for team in valgte_team:
    data_team = utvalg[utvalg["team"] == team]
    e, e_forrige, e_fjor = hent(siste, data_team), hent(forrige_k, data_team), hent(fjor_k, data_team)
    if e is None:
        rader.append({"Team": team, f"eNPS {siste}": SKJULT, "Antall svar": "under 5",
                      "Svarandel": SKJULT, "Mot forrige kvartal": SKJULT, "Mot i fjor": SKJULT})
        continue
    rader.append({
        "Team": team,
        f"eNPS {siste}": enps_tekst(e["enps"]),
        "Antall svar": str(e["svar"]),
        "Svarandel": b.prosent(e["svarandel"], 0)
                     + (" (lav)" if e["svarandel"] < b.LAV_SVARANDEL else ""),
        "Mot forrige kvartal": endring_poeng(e["enps"], e_forrige["enps"] if e_forrige else None) or "–",
        "Mot i fjor": endring_poeng(e["enps"], e_fjor["enps"] if e_fjor else None) or "–",
    })
if hele_selskapet:
    rader.append({
        "Team": "Hele selskapet", f"eNPS {siste}": enps_tekst(naa["enps"]),
        "Antall svar": str(naa["svar"]), "Svarandel": b.prosent(naa["svarandel"], 0),
        "Mot forrige kvartal": mot_forrige or "–", "Mot i fjor": mot_fjor or "–",
    })
st.dataframe(pd.DataFrame(rader), hide_index=True, width="stretch")
st.caption(
    f"**Femregelen:** team med under 5 svar skjules (gjelder også kvartalene det sammenlignes "
    f"med). **Lav svarandel** = under {b.prosent(b.LAV_SVARANDEL, 0)} av de inviterte – da kan "
    "eNPS gi et skjevt bilde. Hele selskapet er vektet med antall svar, inkludert team som "
    "er skjult."
)


# --- Kobling: eNPS og langtidsfravær ------------------------------------------------------
st.subheader("Engasjement og langtidsfravær")
st.warning(b.KOBLING_MERKNAD, icon="⚠️")

snitt_ansatte = b.snitt_ansatte(ansatte[ansatte["team"].isin(valgte_team)], start, slutt)
if snitt_ansatte < b.MIN_GRUPPE:
    st.info("Utvalget har færre enn 5 ansatte. Fraværet skjules av personvernhensyn.")
else:
    per_kvartal = b.enps_per_kvartal(utvalg, kvartaler).set_index("kvartal")
    langtid = b.langtid_per_kvartal(fravaer[fravaer["team"].isin(valgte_team)], kvartaler)
    kobling = per_kvartal[["enps"]].join(langtid * 100).reset_index()
    kobling["enps"] = kobling["enps"].map(b.avrund)
    kobling["langtid_rate"] = kobling["langtid_rate"].map(lambda x: b.avrund(x, 1))

    venstre, hoyre = st.columns(2)  # to grafer side om side, hver med egen akse
    for kolonne, felt, tittel, farge in [
        (venstre, "enps", "eNPS", "#2e86ab"),
        (hoyre, "langtid_rate", "Langtidsfravær (%)", "#d1495b"),
    ]:
        kolonne.markdown(f"**{tittel}**")
        kolonne.vega_lite_chart(
            kobling,
            {
                "height": 220,
                "mark": {"type": "line", "point": True, "color": farge},
                "encoding": {
                    "x": {"field": "kvartal", "type": "ordinal", "title": None,
                          "axis": {"labelAngle": 0}},
                    # Aksen tar med null, så små endringer ikke ser dramatiske ut
                    "y": {"field": felt, "type": "quantitative", "title": None,
                          "scale": {"zero": True}},
                    "tooltip": [{"field": "kvartal"}, {"field": felt, "title": tittel}],
                },
            },
            width="stretch",
        )
    st.caption(
        "Samme utvalg og kvartaler i begge grafene. To grafer i stedet for én med to akser, "
        "så det ikke ser ut som om linjene «følger» hverandre bare på grunn av skaleringen. "
        "Velg ett team i filteret for å se det teamet alene."
    )

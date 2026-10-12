# Rekrutteringssiden: hvor mange vi ansetter, hvor lang tid det tar, og hvordan
# rekrutteringsmetoden henger sammen med kvaliteten på ansettelsene.
# Alle formler ligger i beregninger.py.

import pandas as pd
import streamlit as st

import beregninger as b
from filtre import vis_filtre

st.set_page_config(page_title="Rekruttering – HR-dashbord", layout="wide")


# --- Data ---------------------------------------------------------------------
@st.cache_data
def hent_ansatte():
    return b.les_ansatte()


ansatte = hent_ansatte()


# --- Filtre (felles for alle sider, se filtre.py) ---------------------------------
start, slutt, valgte_team, hele_selskapet = vis_filtre()
utvalg = ansatte[ansatte["team"].isin(valgte_team)]


# --- Overskrift og merking --------------------------------------------------------
st.title("Rekruttering")
st.warning(b.SYNTETISK_MERKNAD, icon="⚠️")
st.caption(
    f"Periode: {start:%d.%m.%Y}–{slutt:%d.%m.%Y}. "
    f"Utvalg: {'hele selskapet' if hele_selskapet else ', '.join(valgte_team)}. "
    f"Rekrutteringsdata er registrert fra {b.REKRUTTERING_FRA:%m.%Y}."
)


# --- KPI-kort: ansettelser i perioden -------------------------------------------------
naa = b.rekruttering(utvalg, start, slutt)
fjor_start, fjor_slutt = b.samme_periode_i_fjor(start, slutt)
har_fjor = fjor_start >= b.REKRUTTERING_FRA
fjor = b.rekruttering(utvalg, fjor_start, fjor_slutt) if har_fjor else None

if naa["antall"] == 0:
    st.info("Ingen ansettelser med registrerte rekrutteringsdata i perioden for dette utvalget.")
    st.stop()


def endring_dager():
    """Endring i median tid til ansettelse, f.eks. «−6 dager»."""
    if not (har_fjor and fjor["antall"]):
        return None
    dager = round(naa["median_dager"] - fjor["median_dager"])
    return "±0 dager" if dager == 0 else f"{dager:+d} dager"


endring_andel = (b.endring_pp(naa["andel_strukturert"], fjor["andel_strukturert"])
                 if har_fjor and fjor["antall"] else None)
endring_antall = f"{naa['antall'] - fjor['antall']:+d}" if har_fjor else None

kort1, kort2, kort3 = st.columns(3)
kort1.metric("Ansettelser", naa["antall"], delta=endring_antall, delta_color="off")
kort1.caption("Alle ansettelsesformer, med registrerte rekrutteringsdata")
kort2.metric("Median tid til ansettelse", f"{naa['median_dager']:.0f} dager",
             delta=endring_dager(), delta_color=b.pilfarge(endring_dager()))
kort2.caption("Fra utlysning til akseptert tilbud")
kort3.metric("Andel strukturert rekruttering", b.prosent(naa["andel_strukturert"], 0),
             delta=endring_andel, delta_color=b.pilfarge(endring_andel, hoyere_er_bedre=True))
kort3.caption(f"{naa['strukturert']} av {naa['antall']} ansettelser")

if har_fjor:
    st.caption(f"Pilene viser endring mot samme periode i fjor ({fjor_start:%m.%Y}–{fjor_slutt:%m.%Y}).")
else:
    st.caption("Ingen sammenligning: samme periode i fjor ligger før rekrutteringsdata ble registrert.")


# --- Kvalitet på ansettelser ------------------------------------------------------------
st.subheader("Kvalitet på ansettelser")
st.warning(b.KVALITET_MERKNAD, icon="⚠️")

kvalitet = b.kvalitet_per_metode(utvalg, slutt)
kohorter = b.kvalitet_kohorter(utvalg, slutt)


def andel_tekst(antall, n):
    """«14,3 % (1 av 7)», «skjult (under 5)» (femregelen), eller «for tidlig å måle»
    når ingen i kohorten har vært ansatt lenge nok ennå."""
    if n == 0:
        return "for tidlig å måle"
    if antall is None or pd.isna(antall):
        return "skjult (under 5)"
    return b.prosent_med_n(int(antall), n)


st.dataframe(
    pd.DataFrame([{
        "Rekrutteringsmetode": r["metode"].capitalize(),
        "Tidlig turnover (slutter innen 12 mnd)": andel_tekst(r["tidlig_antall"], r["tidlig_n"]),
        "Prøvetid bestått": andel_tekst(r["provetid_bestatt"], r["provetid_n"]),
    } for _, r in kvalitet.iterrows()]),
    hide_index=True, width="stretch",
)
st.caption(
    f"**Kohort** = gruppen som følges over tid. Kvalitetstallene bygger på faste ansatte "
    f"med registrerte rekrutteringsdata som har vært ansatt lenge nok til at utfallet kan "
    f"observeres. Kohortene styres av periodeslutt, ikke periodestart:\n"
    f"- **Tidlig turnover:** ansatt {b.REKRUTTERING_FRA:%d.%m.%Y}–{kohorter['tidlig_til']:%d.%m.%Y} "
    f"(minst 12 mnd før periodeslutt). Teller avganger der stillingen må erstattes.\n"
    f"- **Prøvetid:** ansatt {b.REKRUTTERING_FRA:%d.%m.%Y}–{kohorter['provetid_til']:%d.%m.%Y} "
    f"(minst 6 mnd før periodeslutt).\n\n"
    f"**Femregelen:** grupper med færre enn 5 i kohorten skjules."
)


# --- Graf 1: andel strukturerte per kvartal, med n ---------------------------------------
st.subheader("Andel strukturert rekruttering per kvartal")
per_kvartal = b.strukturert_per_kvartal(utvalg, start, slutt)
per_kvartal["prosent"] = per_kvartal["andel"] * 100
per_kvartal["etikett"] = "n = " + per_kvartal["antall"].astype(str)

st.vega_lite_chart(
    per_kvartal,
    {
        "height": 300,
        "encoding": {
            "x": {"field": "kvartal", "type": "ordinal", "title": None, "axis": {"labelAngle": 0}},
            "y": {"field": "prosent", "type": "quantitative", "title": "Andel strukturert (%)",
                  "scale": {"domain": [0, 100]}},
        },
        "layer": [
            {"mark": {"type": "bar", "color": "#2e86ab"},
             "encoding": {"tooltip": [
                 {"field": "kvartal", "title": "Kvartal"},
                 {"field": "prosent", "title": "Andel (%)", "format": ".0f"},
                 {"field": "strukturert", "title": "Strukturert"},
                 {"field": "antall", "title": "Ansettelser"}]}},
            # Antall ansettelser (n) over hver stolpe
            {"mark": {"type": "text", "dy": -8, "color": "#444"},
             "encoding": {"text": {"field": "etikett"}}},
        ],
    },
    width="stretch",
)
st.caption("n = antall ansettelser i kvartalet (alle ansettelsesformer). Med få ansettelser "
           "per kvartal kan én ansettelse flytte andelen mye.")


# --- Graf 2: median tid til ansettelse per team, med n -----------------------------------
st.subheader("Median tid til ansettelse per team")
per_team = b.tid_til_ansettelse_per_team(utvalg, start, slutt, valgte_team)
per_team = per_team[per_team["antall"] > 0].copy()  # bare team med ansettelser
per_team["etikett"] = (per_team["median_dager"].round().astype(int).astype(str)
                       + " d (n = " + per_team["antall"].astype(str) + ")")

st.vega_lite_chart(
    per_team,
    {
        "height": 40 * len(per_team) + 20,
        "encoding": {
            "y": {"field": "team", "type": "nominal", "title": None, "sort": "-x"},
            "x": {"field": "median_dager", "type": "quantitative", "title": "Median dager"},
        },
        "layer": [
            {"mark": {"type": "bar", "color": "#2e86ab"}},
            {"mark": {"type": "text", "align": "left", "dx": 4, "color": "#444"},
             "encoding": {"text": {"field": "etikett"}}},
        ],
    },
    width="stretch",
)
st.caption("Fra utlysning til akseptert tilbud, for ansettelser i perioden. "
           "n = antall ansettelser. Team uten ansettelser i perioden vises ikke.")

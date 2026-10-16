# Sykefraværssiden: totalt, korttid og langtid, sammenlignet med samme periode i
# fjor og med landssnittet. Alle formler ligger i beregninger.py.

import pandas as pd
import streamlit as st

import beregninger as b
import datalasting as d
import utseende as u
from filtre import IKONER, SPORSMAL, vis_filtre_sensitiv

st.set_page_config(page_title="Sykefravær · HR-dashbord", layout="wide")


# --- Data (felles innlesing, lest bare én gang – se datalasting.py) ----------------
# Avtalte dagsverk regnes ut fra ansatte én gang og deles av alle sidene.
ansatte, fravaer = d.hent_ansatte(), d.hent_fravaer()


# --- Filtre: begrenset, fordi siden har sensitive tall (se filtre.py) -------------
start, slutt, valgte_team, hele_selskapet = vis_filtre_sensitiv()

# Filtrer begge tabellene til valgte team
utvalg_ansatte = ansatte[ansatte["team"].isin(valgte_team)]
utvalg_fravaer = fravaer[fravaer["team"].isin(valgte_team)]


# --- Overskrift og merking --------------------------------------------------------
u.topp("Sykefravær", SPORSMAL["Sykefravær"], IKONER["Sykefravær"])
st.caption(
    f"Periode: {start:%d.%m.%Y}-{slutt:%d.%m.%Y}. "
    f"Utvalg: {'hele selskapet' if hele_selskapet else ', '.join(valgte_team)}."
)

# Femregelen: utvalg med færre enn 5 ansatte skjules
snitt = b.snitt_ansatte(utvalg_ansatte, start, slutt)
if snitt < b.MIN_GRUPPE:
    st.info("Utvalget har færre enn 5 ansatte. Sykefraværet skjules av personvernhensyn.", icon=":material/lock:")
    st.stop()

# Sekundær prikking: små team holdes utenfor totalen – se beregninger.py
fjor_start, fjor_slutt = b.samme_periode_i_fjor(start, slutt)
har_fjor = fjor_start >= b.DATA_FRA
utenfor = b.utenfor_sykefravaer(ansatte, valgte_team)
if utenfor:
    utvalg_ansatte = utvalg_ansatte[~utvalg_ansatte["team"].isin(utenfor)]
    utvalg_fravaer = utvalg_fravaer[~utvalg_fravaer["team"].isin(utenfor)]
    snitt = b.snitt_ansatte(utvalg_ansatte, start, slutt)
    st.caption(f"Totalene gjelder **{b.med_unntak('utvalget', utenfor)}**. "
               "Små team holdes utenfor, så de ikke kan regnes ut (sekundær prikking).")


# --- Regn ut tallene ----------------------------------------------------------------
naa = b.sykefravaer(utvalg_fravaer, start, slutt)
fjor = b.sykefravaer(utvalg_fravaer, fjor_start, fjor_slutt) if har_fjor else None


def endring(navn):
    """Endring mot samme periode i fjor, i prosentpoeng."""
    if not har_fjor:
        return None
    return b.endring_pp(naa[navn], fjor[navn])


# --- KPI-kort -------------------------------------------------------------------------
kort1, kort2, kort3, kort4 = st.columns(4)
kort1.metric("Sykefravær totalt", b.prosent(naa["total_rate"], 2),
             delta=endring("total_rate"), delta_color=b.pilfarge(endring("total_rate"), terskel=b.VESENTLIG_ENDRING_SYKEFRAVAER_PP))
kort1.caption(f"Snitt {b.avrund(snitt)} ansatte")
kort2.metric("Korttid (1-16 dager)", b.prosent(naa["korttid_rate"], 2),
             delta=endring("korttid_rate"), delta_color=b.pilfarge(endring("korttid_rate"), terskel=b.VESENTLIG_ENDRING_SYKEFRAVAER_PP))
kort3.metric("Langtid (over 16 dager)", b.prosent(naa["langtid_rate"], 2),
             delta=endring("langtid_rate"), delta_color=b.pilfarge(endring("langtid_rate"), terskel=b.VESENTLIG_ENDRING_SYKEFRAVAER_PP))
# Status styres av det interne målet. Landssnittet er bare en referanse (se infoboksen).
kort4.metric("Internt mål", b.prosent(b.SYKEFRAVAER_MAL, 0))
# Markdown-lenke: [tekst](adresse)
kort4.caption(f"Referanse: alle bransjer {b.prosent(b.SYKEFRAVAER_LANDSSNITT, 2)} "
              f"([{b.SYKEFRAVAER_KILDE}]({b.SYKEFRAVAER_KILDE_URL})), ikke direkte sammenlignbart")

if har_fjor:
    st.caption(f"Pilene viser endring mot samme periode i fjor "
               f"({fjor_start:%m.%Y}-{fjor_slutt:%m.%Y}), i prosentpoeng (pp).")
else:
    st.caption("Ingen sammenligning: samme periode i fjor ligger før datastart (okt 2024).")

if har_fjor:
    st.caption(b.VESENTLIG_TEKST)
st.info(b.SYKEFRAVAER_REFERANSE_MERKNAD, icon=":material/info:")

# --- Kostnad i arbeidsgiverperioden (bygger på lønn: bare hele selskapet, siste 12 mnd) ---
st.subheader("Kostnad i arbeidsgiverperioden")
if not hele_selskapet:
    st.info("Kostnaden vises bare for hele selskapet, fordi den bygger på lønn "
            "(lønn vises aldri per team).", icon=":material/lock:")
elif not b.er_siste_12(start, slutt):
    st.info("Kostnaden vises bare for siste 12 mnd, fordi den bygger på lønn.",
            icon=":material/lock:")
else:
    kostnad = b.fravaerskostnad(utvalg_ansatte, utvalg_fravaer, start, slutt)
    kostnad_fjor = b.fravaerskostnad(utvalg_ansatte, utvalg_fravaer, fjor_start, fjor_slutt) if har_fjor else None
    pil = b.endring_millioner(kostnad, kostnad_fjor) if kostnad_fjor else None
    k1, _ = st.columns(2)
    k1.metric("Minst", b.millioner(kostnad), delta=pil, delta_color=b.pilfarge(pil))
    k1.caption(
        "Arbeidsgiver betaler de første 16 dagene av hvert sykefravær. Kostnaden er tapte "
        "dagsverk korttid × gjennomsnittlig dagslønn per årsverk"
        + (f" ({b.med_unntak('hele selskapet', utenfor)})" if utenfor else "")
        + ", avrundet til nærmeste 0,1 mill. kr. Det er et minimum: de første 16 dagene av "
        "langtidsfravær, arbeidsgiveravgift og feriepenger er ikke med."
    )


# --- Graf: sykefravær per måned, med landssnitt -----------------------------------------
st.subheader("Sykefravær per måned")

# Trendgrafen viser alltid hele dataperioden (én fast visning, uansett periodevalg).
# Femregelen gjelder per måned – se sykefravaer_per_maaned() i beregninger.py.
per_maaned = b.sykefravaer_per_maaned(utvalg_fravaer, *b.TRENDPERIODE)
if per_maaned.empty:
    st.info("Utvalget har færre enn 5 ansatte i alle månedene. Grafen skjules av "
            "personvernhensyn.", icon=":material/lock:")
else:
    # Gjør tabellen «lang»: én rad per måned og fraværstype (som å «oppheve pivot» i Excel)
    graf_data = (per_maaned.reset_index()
                 .melt(id_vars="måned", var_name="type", value_name="prosent")
                 .rename(columns={"måned": "maaned"}))
    # Ferdig formatert tekst til verktøytipset: komma og Excel-avrunding (avrund),
    # ikke desimalpunktum og JavaScript-avrunding
    graf_data["prosent_tekst"] = graf_data["prosent"].map(lambda x: b.prosent(x / 100, 1))
    landssnitt = b.SYKEFRAVAER_LANDSSNITT * 100

    st.vega_lite_chart(
        graf_data,
        {
            "height": 320,
            "layer": [
                {   # Stablede stolper: langtid nederst, korttid oppå
                    "mark": "bar",
                    "encoding": {
                        "x": {"field": "maaned", "type": "ordinal", "title": None},
                        "y": {"field": "prosent", "type": "quantitative", "stack": True,
                              "title": "Sykefravær (%)"},
                        "color": {"field": "type", "type": "nominal", "title": None,
                                  "scale": {"domain": ["Langtid", "Korttid"],
                                            "range": [u.PETROL, u.PETROL_LYS]}},
                        "order": {"field": "type", "sort": "descending"},
                        "tooltip": [{"field": "maaned", "title": "Måned"},
                                    {"field": "type", "title": "Type"},
                                    {"field": "prosent_tekst", "title": "Sykefravær"}],
                    },
                },
                {   # Stiplet linje for landssnittet
                    "mark": {"type": "rule", "strokeDash": [6, 4], "color": u.TEKST_DEMPET},
                    "encoding": {"y": {"datum": landssnitt}},
                },
                {   # Tekst ved linjen
                    "mark": {"type": "text", "align": "left", "dx": 4, "dy": -8, "color": u.TEKST_DEMPET},
                    "encoding": {"y": {"datum": landssnitt}, "x": {"value": 0},
                                 "text": {"value": f"Alle bransjer {b.prosent(b.SYKEFRAVAER_LANDSSNITT, 2)} (referanse)"}},
                },
            ],
        },
        width="stretch",
    )
    st.caption(
        f"Hele dataperioden ({b.TRENDPERIODE[0]:%m.%Y}-{b.TRENDPERIODE[1]:%m.%Y}), uansett "
        "periodevalg. **Femregelen per måned:** måneder der utvalget har færre enn 5 ansatte, "
        "vises ikke, og små team holdes utenfor måneden når de til sammen er under 5."
    )


# --- Tabell per team --------------------------------------------------------------------
st.subheader("Sykefravær per team")

per_team = b.sykefravaer_per_team(ansatte, fravaer, start, slutt, valgte_team)
SKJULT = b.SKJULT
rader = []
for _, r in per_team.iterrows():
    if r["skjult"]:
        rader.append({"Team": r["team"], "Snitt ansatte": "under 5", "Totalt": SKJULT,
                      "Korttid": SKJULT, "Langtid": SKJULT, "Endring mot i fjor": SKJULT})
        continue
    endring_tekst = "–" if pd.isna(r["endring_pp"]) else b.minustegn(b.endring_pp(r["endring_pp"] / 100, 0))
    rader.append({
        "Team": r["team"],
        "Snitt ansatte": str(b.avrund(r["snitt_ansatte"])),  # n ved siden av prosentene
        "Totalt": b.prosent(r["total_rate"], 2),
        "Korttid": b.prosent(r["korttid_rate"], 2),
        "Langtid": b.prosent(r["langtid_rate"], 2),
        "Endring mot i fjor": endring_tekst,
    })
if hele_selskapet:
    rader.append({
        "Team": b.med_unntak("Hele selskapet", utenfor), "Snitt ansatte": str(b.avrund(snitt)),
        "Totalt": b.prosent(naa["total_rate"], 2), "Korttid": b.prosent(naa["korttid_rate"], 2),
        "Langtid": b.prosent(naa["langtid_rate"], 2),
        "Endring mot i fjor": b.minustegn(endring("total_rate")) or "–",
    })

st.dataframe(pd.DataFrame(rader), hide_index=True, width="stretch")
st.caption(
    "Sykefravær = tapte dagsverk / avtalte dagsverk. Avtalte dagsverk = hverdager "
    "(mandag-fredag) × stillingsprosent, uten fradrag for ferie og helligdager. "
    "**Femregelen:** team med under 5 ansatte skjules."
)

# Rekrutteringssiden: hvor mange vi ansetter, hvor lang tid det tar, og hvordan
# rekrutteringsmetoden henger sammen med kvaliteten på ansettelsene.
# Alle formler ligger i beregninger.py.

import pandas as pd
import streamlit as st

import beregninger as b
import datalasting as d
import utseende as u
from filtre import IKONER, SPORSMAL, vis_filtre_sensitiv

st.set_page_config(page_title="Rekruttering · HR-dashbord", layout="wide")


# --- Data (felles innlesing, lest bare én gang – se datalasting.py) ----------------
ansatte = d.hent_ansatte()


# --- Filtre: begrenset, fordi siden har sensitive tall (se filtre.py) -------------
# Kvaliteten på ansettelser (tidlig turnover, prøvetid) handler om få personer per
# gruppe, så fritt filter kunne trekke utvalg fra hverandre.
start, slutt, valgte_team, hele_selskapet = vis_filtre_sensitiv()
utvalg = ansatte[ansatte["team"].isin(valgte_team)]


# --- Overskrift og merking --------------------------------------------------------
u.topp("Rekruttering", SPORSMAL["Rekruttering"], IKONER["Rekruttering"])
st.caption(
    f"Periode: {start:%d.%m.%Y}-{slutt:%d.%m.%Y}. "
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


# Femregelen: med under 5 ansettelser er median og andel strukturert skjult (None)
SKJULT_UNDER_5 = b.SKJULT_UNDER_5


def endring_dager():
    """Endring i median tid til ansettelse, f.eks. «-6 dager»."""
    if not har_fjor or naa["median_dager"] is None or fjor["median_dager"] is None:
        return None
    return b.endring_antall(naa["median_dager"] - fjor["median_dager"], "dager", "dag")


endring_andel = (b.endring_pp(naa["andel_strukturert"], fjor["andel_strukturert"])
                 if har_fjor and None not in (naa["andel_strukturert"], fjor["andel_strukturert"])
                 else None)
diff_antall = naa["antall"] - fjor["antall"] if har_fjor else None
endring_antall = None if diff_antall is None else ("±0" if diff_antall == 0 else f"{diff_antall:+d}")

kort1, kort2, kort3 = st.columns(3)
kort1.metric("Ansettelser", naa["antall"], delta=endring_antall, delta_color="off")
kort1.caption("Alle ansettelsesformer, med registrerte rekrutteringsdata")
if naa["median_dager"] is None:
    forklaring = "Skjult: færre enn 5 ansettelser i utvalget (femregelen)."
    u.skjult_kort(kort2, "Median tid til ansettelse", forklaring)
    u.skjult_kort(kort3, "Andel strukturert rekruttering", forklaring)
else:
    kort2.metric("Median tid til ansettelse", f"{b.avrund(naa['median_dager'])} dager",
                 delta=endring_dager(), delta_color=b.pilfarge(endring_dager()))
    kort2.caption("Fra utlysning til akseptert tilbud")
    # Grå pil når en av periodene bygger på under 20 ansettelser (for lite til å si noe)
    nok = har_fjor and min(naa["antall"], fjor["antall"]) >= b.MIN_N_ENDRING
    kort3.metric("Andel strukturert rekruttering", b.prosent(naa["andel_strukturert"], 0),
                 delta=endring_andel,
                 delta_color=b.pilfarge(endring_andel, hoyere_er_bedre=True, vesentlig=nok))
    kort3.caption(f"{naa['strukturert']} av {naa['antall']} ansettelser")

if har_fjor:
    st.caption(f"Pilene viser endring mot samme periode i fjor ({fjor_start:%m.%Y}-{fjor_slutt:%m.%Y}).")
else:
    st.caption("Ingen sammenligning: samme periode i fjor ligger før rekrutteringsdata ble registrert.")


# --- Kvalitet på ansettelser ------------------------------------------------------------
st.subheader("Kvalitet på ansettelser")
st.info(b.KVALITET_MERKNAD, icon=":material/info:")

# Med sekundær prikking: i totalen («hele selskapet») skjules en celle hvis små,
# skjulte team ellers kunne regnes ut som total minus de synlige (se beregninger.py)
kvalitet = b.kvalitet_per_nivaa_prikket(ansatte, slutt, valgte_team)
kohorter = b.kvalitet_kohorter(utvalg, slutt)


def andel_tekst(antall, n, prikket=False):
    """«14,3 % (1 av 7)», «skjult (under 5)» (femregelen), «skjult (sekundær prikking)»,
    eller «for tidlig å måle» når ingen i kohorten har vært ansatt lenge nok ennå."""
    if n == 0:
        return "for tidlig å måle"
    if prikket:
        return b.SKJULT_PRIKKET
    if antall is None or pd.isna(antall):
        return SKJULT_UNDER_5
    return b.prosent_med_n(int(antall), n)


st.dataframe(
    pd.DataFrame([{
        "Rekruttering": r["gruppe"].capitalize(),
        "Tidlig turnover (slutter innen 12 mnd)": andel_tekst(r["tidlig_antall"], r["tidlig_n"],
                                                              r["tidlig_prikket"]),
        "Prøvetid bestått": andel_tekst(r["provetid_bestatt"], r["provetid_n"],
                                        r["provetid_prikket"]),
    } for _, r in kvalitet.iterrows()]),
    hide_index=True, width="stretch",
)
st.caption(
    f"**Kohort** = gruppen som følges over tid. Kvalitetstallene bygger på faste ansatte "
    f"med registrerte rekrutteringsdata som har vært ansatt lenge nok til at utfallet kan "
    f"observeres. Kohortene styres av periodeslutt, ikke periodestart:\n"
    f"- **Tidlig turnover:** ansatt {b.REKRUTTERING_FRA:%d.%m.%Y}-{kohorter['tidlig_til']:%d.%m.%Y} "
    f"(minst 12 mnd før periodeslutt). Teller avganger der stillingen må erstattes.\n"
    f"- **Prøvetid:** ansatt {b.REKRUTTERING_FRA:%d.%m.%Y}-{kohorter['provetid_til']:%d.%m.%Y} "
    f"(minst 6 mnd før periodeslutt).\n\n"
    f"**Tre nivåer:** (1) ustrukturert, (2) strukturert intervju alene og (3) strukturert "
    f"intervju + minst én tilleggsmetode (case study, personlighetstest eller evnetest).\n\n"
    f"**Femregelen:** grupper med færre enn 5 i kohorten skjules. For hele selskapet "
    f"skjules også celler der små team ellers kunne regnes ut (sekundær prikking)."
)

st.info(
    "**Hvorfor vi ikke kan avgjøre hvilken metode som virker best:** Et selskap på "
    "denne størrelsen ansetter for få personer til å evaluere rekrutteringsmetoder "
    "statistisk på egne data alene, særlig de nyeste metodene, som ennå ikke har en "
    "kohort å måle. Valg av metoder bør derfor bygge på forskning (se under), og egne "
    "data brukes til å følge med, ikke til å bevise.",
    icon=":material/info:",
)


# --- Bruk av tilleggsmetoder (bare antall, aldri resultater) -----------------------------
st.subheader("Bruk av tilleggsmetoder")
bruk = b.bruk_av_tilleggsmetoder(utvalg, start, slutt)
kolonner = st.columns(len(bruk))
for kolonne, (navn, antall) in zip(kolonner, bruk.items()):
    if antall is None:
        u.skjult_kort(kolonne, navn.capitalize())  # «–» og «Skjult (under 5)» under
    else:
        kolonne.metric(navn.capitalize(), antall)
st.caption(
    "Antall ansettelser i perioden der metoden ble brukt (en ansettelse kan ha flere). "
    "Tilleggsmetoder ble tatt i bruk for strukturerte ansettelser utlyst fra 2026. "
    "Bare antall vises, aldri resultater. **Femregelen:** under 5 skjules, også for hele "
    "selskapet (ellers kan «1 personlighetstest» peke mot én kandidat)."
)


# --- Forskningsboks ------------------------------------------------------------------
def to_desimaler(verdi, fortegn=False):
    """0.42 → «0,42» (eller «−0,09» med fortegn). Tom verdi → «–»."""
    if verdi is None:
        return "–"
    tekst = f"{b.avrund(verdi, 2):{'+' if fortegn else ''}.2f}".replace(".", ",")
    return tekst.replace("-", "−")  # ekte minustegn


with st.container(border=True):  # ramme rundt boksen
    st.subheader("Hva sier forskningen?")
    st.markdown(f"Kilde: [{b.FORSKNING_KILDE}]({b.FORSKNING_KILDE_URL})")
    st.dataframe(
        pd.DataFrame([{
            "Metode i dashbordet": metode,
            "Kategori i forskningen": kategori,
            "Sackett mfl. (2022)": to_desimaler(ny),
            "Schmidt og Hunter (1998)": to_desimaler(gammel),
            "Endring": to_desimaler(None if gammel is None else ny - gammel, fortegn=True),
        } for metode, kategori, ny, gammel in b.FORSKNING_VALIDITET]),
        hide_index=True, width="stretch",
    )
    st.markdown(
        "**Validitet** er sammenhengen mellom metoden og senere jobbprestasjon, fra 0 (ingen) "
        "til 1 (perfekt). Tallene er gjennomsnitt fra mange studier (metaanalyse).\n\n"
        "- **Forskningen har endret seg:** Sackett mfl. (2022) korrigerer for det de mener var "
        "overkorrigering i tidligere metaanalyser, og estimatene ble lavere, mest for evnetest "
        "og arbeidsprøve. Strukturert intervju ligger nå øverst.\n"
        "- **Noen forskere mener de nye estimatene er for lave**, fordi korreksjonene kan ha "
        "gått for langt den andre veien.\n"
        "- **Case study** finnes ikke som egen kategori i forskningen. Nærmeste kategori er "
        "**arbeidsprøve (work sample)**.\n"
        "- **Personlighetstest** måler alle fem Big Five-trekk. Hvilke trekk som er relevante, "
        "**avhenger av stillingen**. Et trekk med lav gjennomsnittlig validitet kan være "
        "viktig i en bestemt rolle.\n\n"
        f"Tidligere anslag: {b.TIDLIGERE_KILDE}."
    )


# --- Personvern ved testbruk ---------------------------------------------------------
st.info(
    "**Personvern ved testbruk:** Resultater fra personlighets- og evnetester er "
    "personopplysninger. Datasettet lagrer bare *om* en metode ble brukt, aldri "
    "resultater, heller ikke per Big Five-trekk. Kandidater skal på forhånd informeres om "
    "hvilke tester som brukes og hvorfor, resultatene skal bare brukes i den aktuelle "
    "rekrutteringen, og de skal ikke lagres lenger enn nødvendig.",
    icon=":material/lock:",
)


# --- Graf 1: andel strukturerte per kvartal, med n ---------------------------------------
st.subheader("Andel strukturert rekruttering per kvartal")
per_kvartal = b.strukturert_per_kvartal(utvalg, start, slutt)  # bare kvartaler med minst 5
if per_kvartal.empty:
    st.info("Ingen kvartaler med minst 5 ansettelser i utvalget. Grafen skjules (femregelen).",
            icon=":material/lock:")
per_kvartal["prosent"] = per_kvartal["andel"] * 100
per_kvartal["andel_tekst"] = per_kvartal["andel"].map(lambda x: b.prosent(x, 0))  # verktøytips
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
            {"mark": {"type": "bar", "color": u.PETROL},
             "encoding": {"tooltip": [
                 {"field": "kvartal", "title": "Kvartal"},
                 {"field": "andel_tekst", "title": "Andel strukturert"},
                 {"field": "strukturert", "title": "Strukturert"},
                 {"field": "antall", "title": "Ansettelser"}]}},
            # Antall ansettelser (n) over hver stolpe
            {"mark": {"type": "text", "dy": -8, "color": u.TEKST_DEMPET},
             "encoding": {"text": {"field": "etikett"}}},
        ],
    },
    width="stretch",
)
st.caption("n = antall ansettelser i kvartalet (alle ansettelsesformer). Med få ansettelser "
           "per kvartal kan én ansettelse flytte andelen mye. **Femregelen:** kvartaler med "
           "under 5 ansettelser vises ikke.")


# --- Graf 2: median tid til ansettelse per team, med n -----------------------------------
st.subheader("Median tid til ansettelse per team")
per_team = b.tid_til_ansettelse_per_team(utvalg, start, slutt, valgte_team)
# Bare team med minst 5 ansettelser – ellers er medianen skjult (femregelen)
per_team = per_team[per_team["median_dager"].notna()].copy()
per_team["etikett"] = (per_team["median_dager"].map(b.avrund).astype(str)
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
            {"mark": {"type": "bar", "color": u.PETROL}},
            {"mark": {"type": "text", "align": "left", "dx": 4, "color": u.TEKST_DEMPET},
             "encoding": {"text": {"field": "etikett"}}},
        ],
    },
    width="stretch",
)
st.caption("Fra utlysning til akseptert tilbud, for ansettelser i perioden. "
           "n = antall ansettelser. **Femregelen:** team med under 5 ansettelser i perioden "
           "vises ikke.")

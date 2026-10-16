# Engasjementssiden: eNPS per kvartal og team, svarandel, og koblingen mot
# langtidsfravær. Alle formler ligger i beregninger.py.

import pandas as pd
import streamlit as st

import beregninger as b
import datalasting as d
import utseende as u
from filtre import IKONER, SPORSMAL, vis_filtre_sensitiv

st.set_page_config(page_title="Engasjement · HR-dashbord", layout="wide")


# --- Data (felles innlesing, lest bare én gang – se datalasting.py) ----------------
ansatte, fravaer, engasjement = d.hent_ansatte(), d.hent_fravaer(), d.hent_engasjement()


# --- Filtre: begrenset, fordi siden har sensitive tall (se filtre.py) -------------
start, slutt, valgte_team, hele_selskapet = vis_filtre_sensitiv()
utvalg = engasjement[engasjement["team"].isin(valgte_team)]


# --- Overskrift og merking --------------------------------------------------------
u.topp("Engasjement (eNPS)", SPORSMAL["Engasjement"], IKONER["Engasjement"])

kvartaler = b.kvartaler_i_perioden(start, slutt)
if not kvartaler:
    st.info("Perioden inneholder ingen hele kvartaler. Velg en lengre periode.")
    st.stop()

siste = kvartaler[-1]
forrige_k, fjor_k = b.kvartal_minus(siste, 1), b.kvartal_minus(siste, 4)

# Sekundær prikking: små team holdes utenfor totalene – se beregninger.py
utenfor = b.utenfor_enps(engasjement, valgte_team)
utvalg_total = utvalg[~utvalg["team"].isin(utenfor)]  # brukes til alle totaler
st.caption(
    f"Kvartaler i perioden: {kvartaler[0]}-{siste}. "
    f"Utvalg: {'hele selskapet' if hele_selskapet else ', '.join(valgte_team)}."
)

with st.expander("Slik leses eNPS"):
    st.markdown(
        "eNPS (employee Net Promoter Score) bygger på spørsmålet «Hvor sannsynlig er det at "
        "du vil anbefale arbeidsplassen din til en venn?» (0-10).\n\n"
        "- **eNPS = andel anbefalere (9-10) minus andel kritikere (0-6)**, fra −100 til +100.\n"
        "- Positive tall betyr flere anbefalere enn kritikere.\n"
        "- I små grupper kan noen få svar flytte tallet mye. Derfor vises antall svar (n) "
        "og svarandel alltid.\n"
        "- For flere team samlet vektes hvert team med antall svar.\n"
        "- **Lav svarandel** kan gi et skjevt bilde: de som er mest misfornøyde, svarer "
        "ofte ikke (frafallsskjevhet)."
    )


# --- Hjelpefunksjoner for visning ----------------------------------------------------
enps_tekst = b.enps_tekst  # felles i beregninger.py


def endring_poeng(ny, gammel):
    """Endring i eNPS-poeng som tekst, f.eks. «+3 poeng». None hvis noe mangler."""
    if ny is None or gammel is None:
        return None
    return b.endring_antall(ny - gammel, "poeng")


def hent(kvartal, data=utvalg_total):
    """Samlet eNPS for et kvartal (None hvis kvartalet mangler eller har under 5 svar)."""
    return b.enps_samlet(data[data["kvartal"] == kvartal])


# --- KPI-kort -------------------------------------------------------------------------
naa = hent(siste)
if naa is None:
    st.info("Utvalget har færre enn 5 svar. eNPS skjules av personvernhensyn.", icon=":material/lock:")
    st.stop()

forrige, fjor = hent(forrige_k), hent(fjor_k)
mot_fjor = endring_poeng(naa["enps"], fjor["enps"] if fjor else None)
mot_forrige = endring_poeng(naa["enps"], forrige["enps"] if forrige else None)
lav = naa["svarandel"] < b.LAV_SVARANDEL
if utenfor:
    st.caption(f"Totalene gjelder **{b.med_unntak('utvalget', utenfor)}**. Små team holdes "
               "utenfor, så de ikke kan regnes ut (sekundær prikking).")

kort1, kort2, kort3 = st.columns(3)
# Grå pil når et av kvartalene bygger på under 20 svar (for lite til å si noe)
nok = fjor is not None and min(naa["svar"], fjor["svar"]) >= b.MIN_N_ENDRING
kort1.metric(f"eNPS {siste}", enps_tekst(naa["enps"]), delta=mot_fjor,
             delta_color=b.pilfarge(mot_fjor, hoyere_er_bedre=True, vesentlig=nok))
kort1.caption(f"Pilen viser endring mot samme kvartal i fjor ({fjor_k})" if fjor
              else "Ingen sammenligning med i fjor (mangler data)")
kort2.metric("Endring mot forrige kvartal", b.minustegn(mot_forrige) or "–")
kort2.caption(f"Fra {enps_tekst(forrige['enps'])} i {forrige_k}" if forrige else "Forrige kvartal mangler")
kort3.metric("Lav svarandel" if lav else "Svarandel", b.prosent(naa["svarandel"], 0))
kort3.caption(f"{naa['svar']} av {naa['invitert']} invitert."
              + (f" Under {b.prosent(b.LAV_SVARANDEL, 0)}, så tolk eNPS med forsiktighet." if lav else ""))


# --- Graf: eNPS per kvartal og team -----------------------------------------------------
st.subheader("eNPS per kvartal og team")

# Trendgrafene viser alltid hele dataperioden (én fast visning, uansett periodevalg).
# Femregelen gjelder per punkt: hvert team-kvartal med under 5 svar vises ikke.
trend_kvartaler = b.kvartaler_i_perioden(*b.TRENDPERIODE)
i_trend = utvalg[utvalg["kvartal"].isin(trend_kvartaler)]
synlig = i_trend[i_trend["antall_svar"] >= b.MIN_GRUPPE].copy()  # femregelen per punkt

# Uthev teamet med størst fall fra første til siste kvartal i grafen
endring_per_team = {}
for team, t in synlig.groupby("team"):
    t = t.set_index("kvartal")
    if trend_kvartaler[0] in t.index and trend_kvartaler[-1] in t.index:
        endring_per_team[team] = t.loc[trend_kvartaler[-1], "enps"] - t.loc[trend_kvartaler[0], "enps"]
uthevet = min(endring_per_team, key=endring_per_team.get) if endring_per_team else None
if uthevet is not None and endring_per_team[uthevet] > -b.UTHEV_FALL:
    uthevet = None  # ingen team har falt nok til å utheves

synlig["linje"] = synlig["team"].where(synlig["team"] == uthevet, "andre team")
synlig["enps_tekst"] = synlig["enps"].map(b.enps_tekst)  # verktøytips: Excel-avrunding
st.vega_lite_chart(
    synlig,
    {
        "height": 320,
        "layer": [
            {   # Nullinje: like mange anbefalere som kritikere
                "mark": {"type": "rule", "color": u.NOYTRAL, "strokeDash": [4, 4]},
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
                                        "range": [u.PETROL, u.NOYTRAL_LYS]}},
                    "tooltip": [{"field": "team", "title": "Team"},
                                {"field": "kvartal", "title": "Kvartal"},
                                {"field": "enps_tekst", "title": "eNPS"},
                                {"field": "antall_svar", "title": "Antall svar"}],
                },
            },
        ],
    },
    width="stretch",
)
st.caption(
    f"Hele dataperioden ({trend_kvartaler[0]}-{trend_kvartaler[-1]}), uansett periodevalg. "
    + (f"Uthevet: **{uthevet}**, teamet med størst fall fra første til siste kvartal "
       f"({enps_tekst(endring_per_team[uthevet])} poeng). " if uthevet else "")
    + f"Et team uthevet bare ved fall på minst {b.UTHEV_FALL} poeng. "
    "Stiplet linje = 0 (like mange anbefalere som kritikere). "
    "**Femregelen per punkt:** team-kvartaler med under 5 svar vises ikke."
)


# --- Tabell per team --------------------------------------------------------------------
st.subheader("eNPS per team")
SKJULT = b.SKJULT
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
        "Mot forrige kvartal": b.minustegn(endring_poeng(e["enps"], e_forrige["enps"] if e_forrige else None)) or "–",
        "Mot i fjor": b.minustegn(endring_poeng(e["enps"], e_fjor["enps"] if e_fjor else None)) or "–",
    })
if hele_selskapet:
    rader.append({
        "Team": b.med_unntak("Hele selskapet", utenfor), f"eNPS {siste}": enps_tekst(naa["enps"]),
        "Antall svar": str(naa["svar"]), "Svarandel": b.prosent(naa["svarandel"], 0),
        "Mot forrige kvartal": b.minustegn(mot_forrige) or "–", "Mot i fjor": b.minustegn(mot_fjor) or "–",
    })
st.dataframe(pd.DataFrame(rader), hide_index=True, width="stretch")
st.caption(
    f"**Femregelen:** team med under 5 svar skjules (gjelder også kvartalene det sammenlignes "
    f"med). **Lav svarandel** = under {b.prosent(b.LAV_SVARANDEL, 0)} av de inviterte. Da kan "
    "eNPS gi et skjevt bilde. Hele selskapet er vektet med antall svar. Små team holdes "
    "utenfor totalen, så de ikke kan regnes ut (sekundær prikking)."
)


lave = [r["Team"] for r in rader if r["Svarandel"].endswith("(lav)")]
if lav or lave:
    st.info(
        "**Lav svarandel"
        + (f" ({', '.join(lave)})" if lave else "")
        + ":** når mange ikke svarer, kan eNPS gi et for positivt bilde. De som er mest "
        "misfornøyde, svarer ofte ikke (frafallsskjevhet), så det reelle engasjementet "
        "kan være lavere enn tallet viser.",
        icon=":material/info:",
    )


# --- Kobling: eNPS og langtidsfravær ------------------------------------------------------
st.subheader("Engasjement og langtidsfravær")
st.info(b.KOBLING_MERKNAD, icon=":material/info:")

# Samme team holdes utenfor begge grafene, så de viser samme utvalg
utenfor_kobling = sorted(set(utenfor) | set(b.utenfor_sykefravaer(ansatte, valgte_team)))
kobling_team = [t for t in valgte_team if t not in utenfor_kobling]
snitt_ansatte = b.snitt_ansatte(ansatte[ansatte["team"].isin(kobling_team)], start, slutt)
if snitt_ansatte < b.MIN_GRUPPE:
    st.info("Utvalget har færre enn 5 ansatte. Fraværet skjules av personvernhensyn.")
else:
    if utenfor_kobling:
        st.caption(f"Begge grafene gjelder **{b.med_unntak('utvalget', utenfor_kobling)}** "
                   "(sekundær prikking).")
    # Hele dataperioden, med femregelen per kvartal (se beregninger.py).
    # «inner» = bare kvartaler der begge tallene kan vises, så grafene viser det samme.
    per_kvartal = b.enps_per_kvartal(utvalg[utvalg["team"].isin(kobling_team)],
                                     trend_kvartaler).set_index("kvartal")
    langtid = b.langtid_per_kvartal(fravaer[fravaer["team"].isin(kobling_team)], trend_kvartaler)
    kobling = per_kvartal[["enps"]].join(langtid * 100, how="inner").reset_index()
    # Verktøytips med ferdig formatert tekst (komma, Excel-avrunding)
    kobling["enps_tekst"] = kobling["enps"].map(b.enps_tekst)
    kobling["langtid_rate_tekst"] = kobling["langtid_rate"].map(lambda x: b.prosent(x / 100, 1))

    venstre, hoyre = st.columns(2)  # to grafer side om side, hver med egen akse
    for kolonne, felt, tittel, farge in [
        (venstre, "enps", "eNPS", u.PETROL),
        (hoyre, "langtid_rate", "Langtidsfravær (%)", u.PETROL),
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
                    "tooltip": [{"field": "kvartal", "title": "Kvartal"},
                                {"field": f"{felt}_tekst", "title": tittel}],
                },
            },
            width="stretch",
        )
    st.caption(
        f"Hele dataperioden ({trend_kvartaler[0]}-{trend_kvartaler[-1]}). Kvartaler med under "
        "5 svar eller under 5 ansatte vises ikke (femregelen per punkt). "
        "Samme utvalg og kvartaler i begge grafene. To grafer i stedet for én med to akser, "
        "så det ikke ser ut som om linjene «følger» hverandre bare på grunn av skaleringen. "
        "Velg ett team i filteret for å se det teamet alene."
    )

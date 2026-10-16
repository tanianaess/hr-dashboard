# Utviklingssiden: opplæring, 1:1 med lederen og intern mobilitet, og hvordan det
# henger sammen med turnover. Alle formler ligger i beregninger.py.

import pandas as pd
import streamlit as st

import beregninger as b
import datalasting as d
import utseende as u
from filtre import IKONER, SPORSMAL, vis_filtre_sensitiv

st.set_page_config(page_title="Utvikling · HR-dashbord", layout="wide")


# --- Data (felles innlesing, lest bare én gang – se datalasting.py) ----------------
ansatte = d.hent_ansatte()
aktiviteter, samtaler, endringer = d.hent_opplaering(), d.hent_en_til_en(), d.hent_stillingsendringer()


# --- Filtre: begrenset, fordi forfremmelser er sensitive (se filtre.py) -------------
start, slutt, valgte_team, hele_selskapet = vis_filtre_sensitiv()
utvalg = ansatte[ansatte["team"].isin(valgte_team)]


# --- Overskrift og merking --------------------------------------------------------
u.topp("Utvikling", SPORSMAL["Utvikling"], IKONER["Utvikling"])
st.caption(
    f"Periode: {start:%d.%m.%Y}-{slutt:%d.%m.%Y}. "
    f"Utvalg: {'hele selskapet' if hele_selskapet else ', '.join(valgte_team)}."
)
st.info(b.KOMPETANSE_MERKNAD, icon=":material/info:")

# Sekundær prikking (se beregninger.py):
# - opplæring og 1:1: små team (ledergruppen) holdes utenfor totalen
# - forfremmelser: team med under 5 interne endringer holdes utenfor hvis de til sammen er under 5
utenfor = b.utenfor_sykefravaer(ansatte, valgte_team)
utvalg_total = utvalg[~utvalg["team"].isin(utenfor)]
utenfor_f = b.utenfor_forfremmelser(ansatte, endringer, valgte_team)

forrige_start, forrige_slutt = b.forrige_periode(start, slutt)
har_forrige = forrige_start >= b.DATA_FRA

o = b.opplaering(utvalg_total, aktiviteter, start, slutt)
if o is None:
    st.info("Utvalget har færre enn 5 ansatte. Tallene skjules av personvernhensyn.",
            icon=":material/lock:")
    st.stop()
o_forrige = b.opplaering(utvalg_total, aktiviteter, forrige_start, forrige_slutt) if har_forrige else None
s = b.en_til_en(utvalg_total, samtaler, start, slutt)
s_forrige = b.en_til_en(utvalg_total, samtaler, forrige_start, forrige_slutt) if har_forrige else None
m = b.intern_mobilitet(utvalg, endringer, start, slutt)
m_forrige = b.intern_mobilitet(utvalg, endringer, forrige_start, forrige_slutt) if har_forrige else None
m_f = b.intern_mobilitet(utvalg[~utvalg["team"].isin(utenfor_f)], endringer, start, slutt)

if utenfor:
    st.caption(f"Opplæring og 1:1 gjelder **{b.med_unntak('utvalget', utenfor)}**. Små team holdes "
               "utenfor, så de ikke kan regnes ut (sekundær prikking).")


def pp(navn, ny, gammel):
    """Endring i prosentpoeng mot forrige periode, eller None."""
    if ny is None or gammel is None or ny.get(navn) is None or gammel.get(navn) is None:
        return None
    return b.endring_pp(ny[navn], gammel[navn])


# --- Opplæring og oppfølging ------------------------------------------------------------
st.subheader("Opplæring og oppfølging")
k1, k2, k3, k4 = st.columns(4)
def endring_timer(ny, gammel):
    """Endring i timer med én desimal, f.eks. «-0,7 timer» (bindestrek: retning på pilen)."""
    diff = b.avrund(ny - gammel, 1)
    return "±0,0 timer" if diff == 0 else f"{diff:+.1f} timer".replace(".", ",")


pil = endring_timer(o["timer_per_ansatt"], o_forrige["timer_per_ansatt"]) if o_forrige else None
k1.metric("Opplæring per ansatt", f"{b.avrund(o['timer_per_ansatt'], 1):.1f} timer".replace(".", ","),
          delta=pil, delta_color=b.pilfarge(pil, hoyere_er_bedre=True))
k1.caption(f"{o['aktiviteter']} aktiviteter (kurs, sertifiseringer, konferanser, intern opplæring)")
if hele_selskapet:
    # Arbeidstiden er den største kostnaden. Den bygger på lønn, så den tas bare med
    # for hele selskapet (lønn vises aldri per team).
    tid = b.opplaering_tidskostnad(utvalg_total, aktiviteter, start, slutt) / o["snitt_ansatte"]
    k2.metric("Kostnad per ansatt", b.kroner(o["kostnad_per_ansatt"] + tid))
    k2.caption(f"Herav {b.kroner(o['kostnad_per_ansatt'])} direkte (kursavgift, reise) og "
               f"{b.kroner(tid)} i arbeidstid (timer × timelønn)")
else:
    k2.metric("Direkte kostnad per ansatt", b.kroner(o["kostnad_per_ansatt"]))
    k2.caption("Kursavgift og reise. Arbeidstiden vises bare for hele selskapet, "
               "fordi den bygger på lønn.")
pil = pp("andel_deltatt", o, o_forrige)
k3.metric("Deltatt i opplæring", b.prosent(o["andel_deltatt"], 0), delta=pil,
          delta_color=b.pilfarge(pil, hoyere_er_bedre=True))
k3.caption(f"{o['deltatt']} av {o['personer']} ansatte i perioden hadde minst én aktivitet: "
           "kurs, sertifisering, konferanse, intern opplæring eller mentorordning")
if s is None:
    u.skjult_kort(k4, "Jevnlige 1:1 med leder")
else:
    pil = pp("andel_jevnlige", s, s_forrige)
    k4.metric("Jevnlige 1:1 med leder", b.prosent(s["andel_jevnlige"], 0), delta=pil,
              delta_color=b.pilfarge(pil, hoyere_er_bedre=True))
    snitt_1til1 = f"{b.avrund(s['per_ansatt_per_maaned'], 1):.1f}".replace(".", ",")
    k4.caption(f"{s['jevnlige']} av {s['n']} hadde 1:1 i minst 10 av 12 måneder. "
               f"I snitt {snitt_1til1} samtaler per ansatt per måned.")
if har_forrige:
    st.caption(f"Pilene viser endring mot {forrige_start:%m.%Y}-{forrige_slutt:%m.%Y}. "
               + b.VESENTLIG_TEKST)


# --- Intern mobilitet ---------------------------------------------------------------------
st.subheader("Intern mobilitet")
k1, k2, k3, k4 = st.columns(4)
if m["besettelsesgrad"] is None:
    u.skjult_kort(k1, "Besatt internt")
else:
    pil = pp("besettelsesgrad", m, m_forrige) if m_forrige and m_forrige["besettelsesgrad"] is not None else None
    # Grå pil når en av periodene bygger på under 20 besatte stillinger (for lite til å si noe)
    nok = m_forrige is not None and min(m["besatte"], m_forrige["besatte"]) >= b.MIN_N_ENDRING
    k1.metric("Besatt internt", b.prosent(m["besettelsesgrad"], 0), delta=pil,
              delta_color=b.pilfarge(pil, hoyere_er_bedre=True, vesentlig=nok))
    k1.caption(f"{m['interne']} av {m['besatte']} stillinger besatt med en som allerede jobbet her")

# Samme endepunkt internt og eksternt: første dag i ny rolle (eksternt inkluderer oppsigelsestid)
ekstern_dager = b.tid_til_tiltredelse(utvalg, start, slutt)
if m["median_dager_intern"] is None:
    u.skjult_kort(k2, "Tid til besatt, internt")
else:
    k2.metric("Tid til besatt, internt", f"{b.avrund(m['median_dager_intern'])} dager")
    k2.caption("Median dager fra utlysning til første dag i ny rolle")
if ekstern_dager is None:
    u.skjult_kort(k3, "Tid til besatt, eksternt")
else:
    k3.metric("Tid til besatt, eksternt", f"{b.avrund(ekstern_dager)} dager")
    k3.caption("Median dager fra utlysning til første arbeidsdag (inkluderer oppsigelsestid)")

if m_f["forfremmelser"] is None:
    u.skjult_kort(k4, "Forfremmelser", "Skjult: færre enn 5 interne endringer i utvalget.")
else:
    k4.metric("Forfremmelser", m_f["forfremmelser"])
    k4.caption(f"{b.prosent(m_f['forfremmelsesrate'])} av snitt {b.avrund(m_f['snitt_ansatte'])} ansatte"
               + (f" · uten {', '.join(utenfor_f)}" if utenfor_f else "")
               + f" · {m_f['overganger']} interne overganger")
st.caption(
    "Interne besettelser er forfremmelser og overganger til en ny rolle i samme team. "
    "Tiden måles likt internt og eksternt, til første dag i ny rolle. Internt går "
    "raskere, blant annet fordi det ikke er oppsigelsestid. "
    "**Forfremmelser er sensitive** (ledelsens vurdering av enkeltpersoner) og vises bare "
    "med minst 5 interne endringer i utvalget."
)


# --- Tabell per team --------------------------------------------------------------------------
st.subheader("Per team")
per_team = b.kompetanse_per_team(ansatte, aktiviteter, samtaler, endringer, start, slutt, valgte_team)


def tall(verdi, format_):
    """Skjult tall (None) blir «skjult», ellers formatert tekst."""
    return b.SKJULT if verdi is None or pd.isna(verdi) else format_(verdi)


rader = []
for _, r in per_team.iterrows():
    rader.append({
        "Team": r["team"],
        "Snitt ansatte": tall(r["snitt_ansatte"], lambda v: str(b.avrund(v))) if pd.notna(r["snitt_ansatte"]) else "under 5",
        "Opplæring per ansatt": tall(r["timer_per_ansatt"], lambda v: f"{b.avrund(v, 1):.1f} t".replace(".", ",")),
        "Kostnad per ansatt": tall(r["kostnad_per_ansatt"], b.kroner),
        "Deltatt i opplæring": tall(r["andel_deltatt"], lambda v: b.prosent(v, 0)),
        "Jevnlige 1:1": (b.SKJULT if pd.isna(r["andel_jevnlige"])
                         else b.prosent_med_n(int(r["jevnlige"]), int(r["n_1til1"]))),
        "Besatt internt": (b.SKJULT_UNDER_5 if pd.isna(r["besettelsesgrad"])
                           else f"{b.prosent(r['besettelsesgrad'], 0)} ({r['interne']} av {r['besatte']})"),
        "Forfremmelser": tall(r["forfremmelser"], lambda v: str(int(v))),
    })
st.dataframe(pd.DataFrame(rader), hide_index=True, width="stretch")
st.caption(
    "**Femregelen:** team med under 5 ansatte skjules. Jevnlige 1:1 gjelder dem som var ansatt "
    "hele perioden, og skjules under 5. Besatt internt vises med minst 5 besatte stillinger. "
    "Forfremmelser vises bare med minst 5 interne endringer i teamet."
)
st.info(b.EN_TIL_EN_MERKNAD, icon=":material/info:")


# --- Kobling: oppfølging og turnover ---------------------------------------------------------------
st.subheader("Oppfølging, turnover og engasjement")
st.info(b.OPPFOLGING_MERKNAD, icon=":material/info:")
turnover = b.turnover_per_team(ansatte, start, slutt, valgte_team).set_index("team")
engasjement = d.hent_engasjement()

punkter = []
for _, r in per_team.iterrows():
    if pd.isna(r["andel_jevnlige"]):
        continue  # 1:1 skjult (femregelen)
    frivillig = turnover.loc[r["team"], "frivillig_rate"]
    enps = b.enps_periode(engasjement[engasjement["team"] == r["team"]], start, slutt)
    punkter.append({
        "team": r["team"],
        "jevnlige": r["andel_jevnlige"] * 100,
        "jevnlige_tekst": b.prosent(r["andel_jevnlige"], 0),
        # Frivillig turnover er None for team med under 5 avganger (fordelingen er sensitiv)
        "frivillig": None if frivillig is None or pd.isna(frivillig) else frivillig * 100,
        "frivillig_tekst": None if frivillig is None or pd.isna(frivillig) else b.prosent(frivillig),
        "enps": enps,
        "enps_tekst": None if enps is None else b.enps_tekst(enps),
    })
punkter = pd.DataFrame(punkter)


def punktgraf(beholder, y_felt, y_tittel, nullinje=False):
    """Ett punkt per team: jevnlige 1:1 (x) mot et annet tall (y). Bare synlige punkter."""
    data = punkter.dropna(subset=[y_felt]) if len(punkter) else punkter
    if len(data) < 2:
        beholder.info("For få team med synlige tall. Velg hele selskapet.", icon=":material/lock:")
        return
    lag = [{"mark": {"type": "point", "filled": True, "size": 120, "color": u.PETROL}},
           # Navnet til høyre for punktet, eller til venstre nær høyre kant (så det ikke kuttes)
           {"transform": [{"filter": "datum.jevnlige <= 75"}],
            "mark": {"type": "text", "align": "left", "dx": 9, "color": u.TEKST_DEMPET},
            "encoding": {"text": {"field": "team"}}},
           {"transform": [{"filter": "datum.jevnlige > 75"}],
            "mark": {"type": "text", "align": "right", "dx": -9, "color": u.TEKST_DEMPET},
            "encoding": {"text": {"field": "team"}}}]
    if nullinje:  # eNPS: like mange anbefalere som kritikere
        lag.insert(0, {"mark": {"type": "rule", "color": u.NOYTRAL, "strokeDash": [4, 4]},
                       "encoding": {"y": {"datum": 0}}})
    beholder.markdown(f"**{y_tittel}**")
    beholder.vega_lite_chart(
        data,
        {
            "height": 280,
            "encoding": {
                "x": {"field": "jevnlige", "type": "quantitative", "title": "Jevnlige 1:1 med leder (%)",
                      "scale": {"domain": [0, 100]}},
                "y": {"field": y_felt, "type": "quantitative", "title": None, "scale": {"zero": True}},
                "tooltip": [{"field": "team", "title": "Team"},
                            {"field": "jevnlige_tekst", "title": "Jevnlige 1:1"},
                            {"field": f"{y_felt}_tekst", "title": y_tittel}],
            },
            "layer": lag,
        },
        width="stretch",
    )


venstre, hoyre = st.columns(2, gap="large")
punktgraf(venstre, "frivillig", "Frivillig turnover")
punktgraf(hoyre, "enps", "eNPS", nullinje=True)
st.caption(
    "Hvert punkt er et team. eNPS er snittet for kvartalene i perioden, vektet med antall svar. "
    "Bare team der tallene kan vises etter femregelen, er med: frivillig turnover krever minst "
    "5 avganger, og eNPS minst 5 svar i hvert kvartal. Team som avviker fra mønsteret, er like "
    "viktige å se på. Se Engasjement for utviklingen kvartal for kvartal."
)


# --- Hva vi ikke måler ---------------------------------------------------------------------------
st.info(
    "**Hva siden bevisst ikke måler:** formelle medarbeidersamtaler to ganger i året (de "
    "måler om en rutine er fulgt, ikke om noen utvikler seg) og kompetansegap per person "
    "(krever vurderinger av enkeltpersoner, er sensitivt og sjelden presist i små selskaper).",
    icon=":material/info:",
)

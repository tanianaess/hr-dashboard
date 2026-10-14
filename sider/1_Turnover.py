# Turnoversiden: hvor mange slutter, hvem vi ville beholdt, og hva det koster.
# Alle formler ligger i beregninger.py – her henter vi bare tallene og viser dem.

import pandas as pd
import streamlit as st

import beregninger as b
import utseende as u
from filtre import vis_filtre_sensitiv

st.set_page_config(page_title="Turnover · HR-dashbord", layout="wide")


# --- Data ---------------------------------------------------------------------
# @st.cache_data: les fila bare én gang, ikke på nytt hver gang du klikker.
@st.cache_data
def hent_ansatte():
    return b.les_ansatte()


ansatte = hent_ansatte()


# --- Filtre: begrenset, fordi siden har sensitive tall (se filtre.py) -------------
start, slutt, valgte_team, hele_selskapet = vis_filtre_sensitiv()
antall_mnd = len(b.maanedsslutter(start, slutt))

# Filtrer til valgte team – som autofilter på team-kolonnen
utvalg = ansatte[ansatte["team"].isin(valgte_team)]


# --- Overskrift og merking --------------------------------------------------------
u.topp("Turnover")
st.caption(
    f"Periode: {start:%d.%m.%Y}–{slutt:%d.%m.%Y} ({antall_mnd} mnd). "
    f"Utvalg: {'hele selskapet' if hele_selskapet else ', '.join(valgte_team)}. "
    "Ratene er omregnet til helår når perioden ikke er 12 måneder."
)


# --- Regn ut tallene ----------------------------------------------------------------
naa = b.turnover(utvalg, start, slutt)

forrige_start, forrige_slutt = b.forrige_periode(start, slutt)
har_forrige = forrige_start >= b.DATA_FRA  # finnes det data for forrige periode?
forrige = b.turnover(utvalg, forrige_start, forrige_slutt) if har_forrige else None

# Femregelen for utvalget (se CLAUDE.md)
if naa["snitt_ansatte"] < b.MIN_GRUPPE:
    # Antall avganger er ikke sensitivt og vises alltid – ratene og fordelingen skjules
    kort1, kort2 = st.columns(2)
    kort1.metric("Avganger", naa["avganger"])
    kort1.caption("Avganger som teller i turnover (frivillig, ufrivillig, pensjon)")
    kort2.metric("Kontrakt utløpt", naa["kontrakt_utløpt"])
    st.info("Utvalget har færre enn 5 ansatte. Turnoverratene og fordelingen på sluttårsak "
            "skjules av personvernhensyn.", icon=":material/lock:")
    st.stop()

# Sekundær prikking for FORDELINGEN (uønsket og sluttårsak) – se beregninger.py.
# Total turnover og antall avganger tar med alle.
utenfor = b.utenfor_turnoverfordeling(ansatte, valgte_team)
utvalg_fordeling = utvalg[~utvalg["team"].isin(utenfor)]
fordeling = b.turnover(utvalg_fordeling, start, slutt)
fordeling_forrige = (b.turnover(utvalg_fordeling, forrige_start, forrige_slutt)
                     if har_forrige else None)

# Fordelingen vises bare når den bygger på minst 5 avganger
vis_fordeling = fordeling["avganger"] >= b.MIN_GRUPPE
vis_fordeling_forrige = har_forrige and fordeling_forrige["avganger"] >= b.MIN_GRUPPE
if utenfor and vis_fordeling:
    st.caption(f"Fordelingen på frivillig og uønsket gjelder **{b.med_unntak('utvalget', utenfor)}** "
               ". Små grupper holdes utenfor, så de ikke kan regnes ut (sekundær prikking).")


# --- KPI-kort -------------------------------------------------------------------------
def endring(navn, kan_vises=True, ny=None, gammel=None):
    """Endring mot forrige periode i prosentpoeng, f.eks. «+3,1 pp».
    Standard er totaltallene; for fordelingen sendes de prikkede tallene inn."""
    if not (har_forrige and kan_vises):
        return None
    ny, gammel = ny or naa, gammel or forrige
    return b.endring_pp(ny[navn], gammel[navn])


snitt = b.avrund(naa["snitt_ansatte"])
kort1, kort2, kort3 = st.columns(3)  # tre kolonner ved siden av hverandre

kort1.metric(
    "Total turnover",
    b.prosent(naa["total_rate"]),
    delta=endring("total_rate"),
    delta_color=b.pilfarge(endring("total_rate")),  # høyere turnover = dårlig = rød pil
)
kort1.caption(f"{naa['avganger']} avganger, snitt {snitt} ansatte")

if vis_fordeling:
    for kort, navn, tittel, tekst in [
        (kort2, "frivillig", "Frivillig turnover", "sa opp selv"),
        (kort3, "uønsket", "Uønsket turnover", "vi ville beholdt"),
    ]:
        pil = endring(f"{navn}_rate", vis_fordeling_forrige, fordeling, fordeling_forrige)
        kort.metric(tittel, b.prosent(fordeling[f"{navn}_rate"]), delta=pil,
                    delta_color=b.pilfarge(pil))
        kort.caption(f"{fordeling[navn]} {tekst}" + (f" (uten {', '.join(utenfor)})" if utenfor else ""))
else:
    kort2.metric("Frivillig turnover", "Skjult")
    kort3.metric("Uønsket turnover", "Skjult")
    kort2.caption("Færre enn 5 avganger i utvalget, så fordelingen vises bare for hele selskapet.")

if har_forrige:
    st.caption(f"Pilene viser endring mot {forrige_start:%m.%Y}–{forrige_slutt:%m.%Y}, i prosentpoeng (pp).")
else:
    st.caption("Ingen sammenligning: forrige periode ligger før datastart (okt 2024).")


# --- Kostnad ved uønsket turnover -------------------------------------------------------
st.subheader("Kostnad ved uønsket turnover")

# Kostnaden bygger på lønn, så den vises bare i ÉN fast visning: hele selskapet,
# siste 12 mnd. Flere visninger (andre perioder eller team) kunne trekkes fra
# hverandre og gi lønnen til noen få personer.
if not hele_selskapet:
    st.info("Kostnaden vises bare for hele selskapet, fordi den bygger på lønn "
            "(lønn vises aldri per team).", icon=":material/lock:")
elif not b.er_siste_12(start, slutt):
    st.info("Kostnaden vises bare for siste 12 mnd. Den bygger på lønn, og to perioder "
            "kunne sammenlignes for å regne ut lønnen til noen få personer.",
            icon=":material/lock:")
elif not vis_fordeling or fordeling["uønsket"] < b.MIN_GRUPPE:
    st.info("Færre enn 5 uønskede avganger. Kostnaden skjules, fordi den ellers viser "
            "lønnen til noen få personer.", icon=":material/lock:")
else:
    # Glidebryter for antakelsen: hvor mye koster det å erstatte én person,
    # målt i prosent av årslønnen? (Bransjeanslag ligger ofte på 50–200 %.)
    kostnadsandel = st.slider(
        "Kostnad per avgang, i prosent av årslønn", min_value=50, max_value=200,
        value=b.avrund(b.KOSTNADSANDEL_STANDARD * 100), step=5, format="%d %%",
    )
    kostnad = fordeling["lønn_uønsket"] * kostnadsandel / 100
    # Sammenligning med forrige 12 mnd (den andre faste perioden), bare med minst 5
    kan_sammenligne = vis_fordeling_forrige and fordeling_forrige["uønsket"] >= b.MIN_GRUPPE
    pil = (b.endring_millioner(kostnad, fordeling_forrige["lønn_uønsket"] * kostnadsandel / 100)
           if kan_sammenligne else None)
    # Rundes grovt (0,1 mill.) med vilje, så lønnssummen ikke kan leses ut nøyaktig
    st.metric("Anslått kostnad", b.millioner(kostnad), delta=pil, delta_color=b.pilfarge(pil))
    st.caption(
        f"Sum årslønn for de {fordeling['uønsket']} uønskede avgangene × {kostnadsandel} %"
        + (f" ({b.med_unntak('hele selskapet', utenfor)})" if utenfor else "") + ", "
        "avrundet til nærmeste 0,1 mill. kr. "
        + ("Pila viser endring mot forrige 12 mnd. " if kan_sammenligne else "")
        + "Prosentsatsen er en antakelse (dekker "
        "rekruttering, opplæring og tapt produktivitet). Juster den med glidebryteren."
    )


# --- Graf: avganger per måned -----------------------------------------------------------
st.subheader("Avganger per måned")
# Bare totalen: én måned er ofte én person, så fordelingen på uønsket og sluttårsak
# vises aldri per måned. Totalt antall avganger er ikke sensitivt, så alle er med.
per_maaned = b.avganger_per_maaned(utvalg, start, slutt)
st.bar_chart(per_maaned, y="Avganger", color=u.PETROL)
st.caption("Avganger som teller i turnover (frivillig, ufrivillig, pensjon). "
           "Utløpte midlertidige kontrakter er ikke med. Fordelingen på uønsket og "
           "sluttårsak vises ikke per måned, fordi én måned ofte er én person.")


# --- Tabell per team --------------------------------------------------------------------
st.subheader("Turnover per team")

per_team = b.turnover_per_team(ansatte, start, slutt, valgte_team)
SKJULT = "skjult"


def tekst(verdi):
    """Antall som tekst – tom verdi (skjult av femregelen) blir «skjult»."""
    return SKJULT if pd.isna(verdi) else str(int(verdi))


def tabellrad(navn, t, skjult=""):
    """Gjør én rad med tall om til ferdig formatert tekst for tabellen."""
    if skjult == "lite team":
        # Antall avganger og utløpte kontrakter er ikke sensitivt og vises alltid
        return {"Team": navn, "Snitt ansatte": "under 5", "Turnover": SKJULT,
                "Avganger": tekst(t["avganger"]),
                "Frivillig": SKJULT, "Ufrivillig": SKJULT, "Pensjon": SKJULT,
                "Uønsket": SKJULT, "Kontrakt utløpt": tekst(t["kontrakt_utløpt"])}
    snitt_rad = b.avrund(t["snitt_ansatte"])
    return {
        "Team": navn,
        "Snitt ansatte": str(snitt_rad),
        # n ved siden av prosenten, f.eks. «20,7 % (8 av 39)»
        "Turnover": f"{b.prosent(t['total_rate'])} ({int(t['avganger'])} av {snitt_rad})",
        "Avganger": tekst(t["avganger"]),
        "Frivillig": tekst(t["frivillig"]),
        "Ufrivillig": tekst(t["ufrivillig"]),
        "Pensjon": tekst(t["pensjon"]),
        "Uønsket": tekst(t["uønsket"]),
        "Kontrakt utløpt": tekst(t["kontrakt_utløpt"]),
    }


rader = [tabellrad(r["team"], r, r["skjult"]) for _, r in per_team.iterrows()]
if hele_selskapet:
    # Totalrad: avganger og turnover for alle, fordelingen etter sekundær prikking
    total = {**naa, **{k: fordeling[k] for k in
                       ["frivillig", "ufrivillig", "pensjon", "uønsket", "kontrakt_utløpt"]}}
    navn = "Hele selskapet" + (f" (fordeling uten {', '.join(utenfor)})" if utenfor else "")
    rader.append(tabellrad(navn, total))

st.dataframe(pd.DataFrame(rader), hide_index=True, width="stretch")
st.caption(
    "Turnover = avganger / snitt antall ansatte (ved månedsslutt), omregnet til helår. "
    "«Kontrakt utløpt» teller ikke i turnover (stillingen skal ikke erstattes). "
    "**Femregelen:** antall avganger og utløpte kontrakter vises alltid (at noen slutter, er "
    "ikke sensitivt). For team med under 5 ansatte skjules turnoverraten. Fordelingen på "
    "sluttårsak og uønsket vises bare for team med minst 5 avganger, ellers bare for hele "
    "selskapet."
)

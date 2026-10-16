# Turnoversiden: hvor mange slutter, hvem vi ville beholdt, og hva det koster.
# Alle formler ligger i beregninger.py – her henter vi bare tallene og viser dem.

import pandas as pd
import streamlit as st

import beregninger as b
import datalasting as d
import utseende as u
from filtre import HELE_SELSKAPET, IKONER, SPORSMAL, vis_filtre_sensitiv

st.set_page_config(page_title="Turnover · HR-dashbord", layout="wide")


# --- Data (felles innlesing, lest bare én gang – se datalasting.py) ----------------
ansatte = d.hent_ansatte()


# --- Filtre: begrenset, fordi siden har sensitive tall (se filtre.py) -------------
start, slutt, valgte_team, hele_selskapet = vis_filtre_sensitiv()
antall_mnd = len(b.maanedsslutter(start, slutt))

# Filtrer til valgte team – som autofilter på team-kolonnen
utvalg = ansatte[ansatte["team"].isin(valgte_team)]


# --- Overskrift og merking --------------------------------------------------------
u.topp("Turnover", SPORSMAL["Turnover"], IKONER["Turnover"])
st.caption(
    f"Periode: {start:%d.%m.%Y}-{slutt:%d.%m.%Y} ({antall_mnd} mnd). "
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
    st.caption(f"Fordelingen på frivillig og uønsket gjelder **{b.med_unntak('utvalget', utenfor)}**. "
               "Små grupper holdes utenfor, så de ikke kan regnes ut (sekundær prikking).")


# --- KPI-kort -------------------------------------------------------------------------
def endring(navn, kan_vises=True, ny=None, gammel=None):
    """Endring mot forrige periode i prosentpoeng, f.eks. «+3,1 pp».
    Standard er totaltallene; for fordelingen sendes de prikkede tallene inn."""
    if not (har_forrige and kan_vises):
        return None
    ny, gammel = ny or naa, gammel or forrige
    return b.endring_pp(ny[navn], gammel[navn])


def nok_n(ny, gammel):
    """Grå pil når en av periodene bygger på under 20 ansatte (for lite til å si noe)."""
    return gammel is not None and min(ny["snitt_ansatte"], gammel["snitt_ansatte"]) >= b.MIN_N_ENDRING


snitt = b.avrund(naa["snitt_ansatte"])
kort1, kort2, kort3 = st.columns(3)  # tre kolonner ved siden av hverandre

kort1.metric(
    "Total turnover",
    b.prosent(naa["total_rate"]),
    delta=endring("total_rate"),
    # høyere turnover = dårlig = rød pil; grå når en av periodene har under 20 ansatte
    delta_color=b.pilfarge(endring("total_rate"), vesentlig=nok_n(naa, forrige)),
)
kort1.caption(f"{naa['avganger']} avganger, snitt {snitt} ansatte")

if vis_fordeling:
    for kort, navn, tittel, tekst in [
        (kort2, "frivillig", "Frivillig turnover", "sa opp selv"),
        (kort3, "uønsket", "Uønsket turnover", "vi ville beholdt"),
    ]:
        pil = endring(f"{navn}_rate", vis_fordeling_forrige, fordeling, fordeling_forrige)
        kort.metric(tittel, b.prosent(fordeling[f"{navn}_rate"]), delta=pil,
                    delta_color=b.pilfarge(pil, vesentlig=nok_n(fordeling, fordeling_forrige)))
        kort.caption(f"{fordeling[navn]} {tekst}" + (f" (uten {', '.join(utenfor)})" if utenfor else ""))
else:
    forklaring = "Skjult: færre enn 5 avganger i utvalget, så fordelingen vises bare for hele selskapet."
    u.skjult_kort(kort2, "Frivillig turnover", forklaring)
    u.skjult_kort(kort3, "Uønsket turnover", forklaring)

if har_forrige:
    st.caption(f"Pilene viser endring mot {forrige_start:%m.%Y}-{forrige_slutt:%m.%Y}, i prosentpoeng (pp).")
else:
    st.caption("Ingen sammenligning: forrige periode ligger før datastart (okt 2024).")


# --- Kostnad ved turnover ---------------------------------------------------------------
st.subheader("Kostnad ved turnover")

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
elif naa["avganger"] < b.MIN_GRUPPE:
    st.info("Færre enn 5 avganger. Kostnaden skjules, fordi den ellers viser "
            "lønnen til noen få personer.", icon=":material/lock:")
else:
    # Glidebryter for antakelsen: hvor mye koster det å erstatte én person,
    # målt i prosent av årslønnen? (Bransjeanslag ligger ofte på 50-200 %.)
    kostnadsandel = st.slider(
        "Kostnad per avgang, i prosent av årslønn", min_value=50, max_value=200,
        value=b.avrund(b.KOSTNADSANDEL_STANDARD * 100), step=5, format="%d %%",
    )
    andel = kostnadsandel / 100
    k1, k2 = st.columns(2)

    # 1) Alle avganger der stillingen må erstattes (ikke sensitivt å telle, men lønn er
    #    med, så samme faste visning og grove avrunding)
    total = naa["lønn_avganger"] * andel
    pil = (b.endring_millioner(total, forrige["lønn_avganger"] * andel)
           if har_forrige and forrige["avganger"] >= b.MIN_GRUPPE else None)
    k1.metric("Erstatningskostnad, alle avganger", b.millioner(total), delta=pil,
              delta_color=b.pilfarge(pil))
    k1.caption(f"{naa['avganger']} avganger der stillingen må erstattes (frivillig, ufrivillig "
               "og pensjon). Det koster å erstatte en person, også når man er glad for at hen sluttet.")

    # 2) Herav uønsket – fordelingen er sensitiv (minst 5, sekundær prikking)
    if vis_fordeling and fordeling["uønsket"] >= b.MIN_GRUPPE:
        uonsket = fordeling["lønn_uønsket"] * andel
        kan_sammenligne = vis_fordeling_forrige and fordeling_forrige["uønsket"] >= b.MIN_GRUPPE
        pil = (b.endring_millioner(uonsket, fordeling_forrige["lønn_uønsket"] * andel)
               if kan_sammenligne else None)
        k2.metric("Herav uønskede avganger", b.millioner(uonsket), delta=pil,
                  delta_color=b.pilfarge(pil))
        k2.caption(f"{fordeling['uønsket']} avganger vi ville beholdt"
                   + (f" ({b.med_unntak('hele selskapet', utenfor)})" if utenfor else "")
                   + ". «Uønsket» er ledelsens vurdering, ikke et fast tall.")
    else:
        u.skjult_kort(k2, "Herav uønskede avganger", "Skjult: færre enn 5 uønskede avganger.")
    st.caption(
        f"Sum årslønn × {kostnadsandel} %, avrundet til nærmeste 0,1 mill. kr. "
        + ("Pilene viser endring mot forrige 12 mnd. " if har_forrige else "")
        + "Prosentsatsen er en antakelse (dekker rekruttering, opplæring og tapt "
        "produktivitet). Juster den med glidebryteren. " + b.VESENTLIG_TEKST
    )

    # --- Regnestykke: hva er det verdt å redusere frivillig turnover? ---------------------
    # Ren aritmetikk, ingen prognose: færre avganger × selskapets gjennomsnittlige
    # erstatningskostnad per avgang (sum årslønn × prosentsatsen over, delt på antall
    # avganger). Lønn per team brukes aldri. Team kan velges bare der fordelingen allerede
    # vises i tabellen under (minst 5 avganger), så regnestykket viser ingen nye tall om
    # små grupper. Vises bare i samme faste visning som kostnaden (hele selskapet, siste 12 mnd).
    if vis_fordeling:
        st.markdown("##### Hva er det verdt å redusere frivillig turnover?")
        per_avgang = naa["lønn_avganger"] / naa["avganger"] * andel
        synlige = b.turnover_per_team(ansatte, start, slutt)
        synlige = synlige[synlige["frivillig_rate"].notna()].set_index("team")
        hvem = st.selectbox("Regn for", [HELE_SELSKAPET, *synlige.index], key="regnestykke_team")
        if hvem == HELE_SELSKAPET:
            rate, snitt_r, antall_f = fordeling["frivillig_rate"], fordeling["snitt_ansatte"], fordeling["frivillig"]
            navn = b.med_unntak("hele selskapet", utenfor)
        else:
            rad = synlige.loc[hvem]
            rate, snitt_r, antall_f, navn = rad["frivillig_rate"], rad["snitt_ansatte"], int(rad["frivillig"]), hvem
        naa_hel = b.avrund(rate * 100)  # dagens nivå i hele prosent
        if naa_hel < 1:
            st.caption(f"Frivillig turnover for {navn} er allerede {b.prosent(rate)}.")
        else:
            # Standardmål: selskapets nivå for et team, 2 pp lavere for hele selskapet
            selskap_hel = b.avrund(fordeling["frivillig_rate"] * 100)
            standard = max(0, naa_hel - 2) if hvem == HELE_SELSKAPET else min(naa_hel, selskap_hel)
            maal = st.slider("Mål for frivillig turnover", 0, naa_hel, standard, format="%d %%")
            faerre = (rate - maal / 100) * snitt_r  # avganger per år
            st.markdown(
                f"Frivillig turnover for **{navn}** er {b.prosent(rate)} ({antall_f} av snitt "
                f"{b.avrund(snitt_r)} ansatte). Ned til {maal} % betyr ca. **{b.avrund(faerre)} "
                f"færre avganger per år**. Med en gjennomsnittlig erstatningskostnad på "
                f"{b.millioner(per_avgang)} per avgang er det ca. **{b.millioner(faerre * per_avgang)} "
                f"per år**."
            )
        st.caption(
            "Regnestykke, ikke prognose: det sier hva færre avganger ville spart med selskapets "
            "gjennomsnittlige erstatningskostnad per avgang, ikke hva et tiltak koster eller "
            "oppnår. Lønn per team brukes ikke. Team kan velges der fordelingen vises i tabellen under."
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
SKJULT = b.SKJULT


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
    # Totalrad: avganger, turnover og kontrakt utløpt for alle (ikke sensitivt),
    # fordelingen på sluttårsak og uønsket etter sekundær prikking
    total = {**naa, **{k: fordeling[k] for k in ["frivillig", "ufrivillig", "pensjon", "uønsket"]}}
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

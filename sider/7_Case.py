# Eksempelside: fra funn til tiltak. Viser hvordan dashbordet kan brukes i praksis, med
# salg som eksempel. Analysen og tiltakene er Tanias vurderinger – tallene hentes fra
# beregninger.py (siste 12 mnd, salg mot hele selskapet), så ingen tall står fast i teksten.

import streamlit as st

import beregninger as b
import datalasting as d
import innsikter as i
import utseende as u
from filtre import CASE_SIDE, IKONER, SPORSMAL

st.set_page_config(page_title="Eksempel · HR-dashbord", layout="wide")

TEAM = i.CASE_TEAM  # «salg»


# --- Data (felles innlesing, lest bare én gang – se datalasting.py) ----------------
ansatte, engasjement = d.hent_ansatte(), d.hent_engasjement()
aktiviteter, samtaler, endringer = d.hent_opplaering(), d.hent_en_til_en(), d.hent_stillingsendringer()

# Én fast visning: siste 12 mnd. Ingen filter på siden.
start, slutt = b.FASTE_PERIODER["Siste 12 mnd"]


# --- Tallene for salg (femregelen er bygd inn: skjulte tall er None) ------------------
# Samme funksjoner som tabellene per team på Turnover og Utvikling
t_salg = b.turnover_per_team(ansatte, start, slutt, [TEAM]).iloc[0]
k_salg = b.kompetanse_per_team(ansatte, aktiviteter, samtaler, endringer, start, slutt, [TEAM]).iloc[0]
enps_salg = b.enps_periode(engasjement[engasjement["team"] == TEAM], start, slutt)


# --- Tallene for hele selskapet (sekundær prikking som på de andre sidene) ------------
utenfor_t = b.utenfor_turnoverfordeling(ansatte, b.TEAM)  # frivillig og uønsket
t_selskap = b.turnover(ansatte[~ansatte["team"].isin(utenfor_t)], start, slutt)
utenfor_s = b.utenfor_sykefravaer(ansatte, b.TEAM)  # opplæring og 1:1 (små team utenfor)
a_s = ansatte[~ansatte["team"].isin(utenfor_s)]
o_selskap = b.opplaering(a_s, aktiviteter, start, slutt)
s_selskap = b.en_til_en(a_s, samtaler, start, slutt)
m_selskap = b.intern_mobilitet(ansatte, endringer, start, slutt)  # ikke sensitivt: alle med
utenfor_e = b.utenfor_enps(engasjement, b.TEAM)
e_selskap = engasjement[~engasjement["team"].isin(utenfor_e)
                        & engasjement["kvartal"].isin(b.kvartaler_i_perioden(start, slutt))]
enps_selskap = b.enps_samlet(e_selskap)["enps"]


# --- Hjelpefunksjoner for visning -------------------------------------------------------
def skjult(verdi):
    """Sant når tallet er skjult av femregelen (None eller tom celle)."""
    return verdi is None or verdi != verdi  # verdi != verdi er sant bare for NaN


def timer(verdi):
    """22,9 timer med komma (som på Utvikling)."""
    return b.SKJULT_UNDER_5 if skjult(verdi) else f"{b.avrund(verdi, 1):.1f}".replace(".", ",")


# --- Toppen av siden ----------------------------------------------------------------------
u.topp(CASE_SIDE, SPORSMAL[CASE_SIDE], IKONER[CASE_SIDE])
st.info("Eksempel på hvordan jeg ville brukt dashbordet i praksis. Analysen og tiltakene er "
        "mine vurderinger, ikke noe verktøyet konkluderer med.", icon=":material/info:")

# Kort fortalt: hele eksempelet i tre linjer. «Dobbelt så høy» regnes ut (forhold_tekst).
if skjult(t_salg["frivillig_rate"]):
    funn = f"{TEAM} har minst opplæring og oppfølging i selskapet"
else:
    funn = (f"{TEAM} har {i.forhold_tekst(t_salg['frivillig_rate'], t_selskap['frivillig_rate'])} "
            "frivillig turnover som selskapet, og minst opplæring og oppfølging")
with st.container(border=True):
    st.markdown(
        ":blue[**Kort fortalt**]\n\n"
        f"- **Funn:** {funn}.\n"
        "- **Mulig årsak:** lederne rekker ikke å følge opp (sjekkes før tiltak).\n"
        "- **Tiltak:** styrke ledelsen i salg og måle effekten over 12 måneder."
    )
st.caption(f"Tallene gjelder siste 12 måneder ({start:%d.%m.%Y}-{slutt:%d.%m.%Y}), {TEAM} "
           "sammenlignet med hele selskapet, med de samme beregningene og personvernreglene "
           "som resten av dashbordet.")


# --- 1. Funn: fire nøkkeltallskort ---------------------------------------------------------
st.subheader("1. Funn")
st.markdown(f"**{TEAM.capitalize()} mot hele selskapet**")

enps_salg_tekst = None if enps_salg is None else b.enps_tekst(enps_salg)
kort = [
    # (tittel, verdi for salg eller None hvis skjult, hele selskapet, ekstra tekst)
    ("Frivillig turnover", None if skjult(t_salg["frivillig_rate"]) else b.prosent(t_salg["frivillig_rate"]),
     b.prosent(t_selskap["frivillig_rate"]), ""),
    ("Jevnlige 1:1 med leder",
     None if skjult(k_salg["andel_jevnlige"]) else b.prosent(k_salg["andel_jevnlige"], 0),
     b.prosent(s_selskap["andel_jevnlige"], 0),
     "" if skjult(k_salg["andel_jevnlige"]) else
     f" {int(k_salg['jevnlige'])} av {int(k_salg['n_1til1'])} i {TEAM} hadde 1:1 i minst 10 av 12 måneder."),
    ("Opplæring, timer per ansatt",
     None if skjult(k_salg["timer_per_ansatt"]) else timer(k_salg["timer_per_ansatt"]),
     timer(o_selskap["timer_per_ansatt"]), ""),
    ("eNPS", enps_salg_tekst, b.enps_tekst(enps_selskap), ""),
]
for kolonne, (tittel, verdi, selskap, ekstra) in zip(st.columns(4, gap="medium"), kort):
    with kolonne.container(border=True):
        if verdi is None:
            u.skjult_kort(st, tittel)  # femregelen: ikke regnet ut på annen måte
        else:
            st.metric(tittel, verdi)
            st.caption(f"Hele selskapet: {selskap}.{ekstra}")
# Hvem som er holdt utenfor totalene, sagt én gang i liten tekst under kortene
st.caption(i.felles_merknad([
    dict(kortnavn="frivillig og uønsket turnover", utenfor=utenfor_t),
    dict(kortnavn="opplæring", utenfor=utenfor_s),
    dict(kortnavn="1:1", utenfor=utenfor_s),
    dict(kortnavn="eNPS", utenfor=utenfor_e),
]) + " eNPS er snittet for kvartalene i perioden, vektet med antall svar.")

# Uønsket turnover og intern besettelse på én linje under kortene
if skjult(t_salg["uønsket_rate"]):
    uonsket = f"Uønsket turnover i {TEAM} er {b.SKJULT_UNDER_5} (færre enn 5 avganger)."
else:
    uonsket = (f"Uønsket turnover {b.prosent(t_salg['uønsket_rate'])} "
               f"({int(t_salg['uønsket'])} av {int(t_salg['avganger'])} avganger) mot "
               f"{b.prosent(t_selskap['uønsket_rate'])}.")
if skjult(k_salg["besettelsesgrad"]):
    intern = f"Besatt internt {b.SKJULT_UNDER_5}."
else:
    intern = (f"Besatt internt {k_salg['interne']} av {k_salg['besatte']} "
              f"({b.prosent(k_salg['besettelsesgrad'], 0)}) mot "
              f"{b.prosent(m_selskap['besettelsesgrad'], 0)}, få ansettelser.")
st.markdown(f"{uonsket} {intern}")


# --- 2. Diagnose og tiltak: én kolonne per mulig forklaring -------------------------------
st.subheader("2. Diagnose og tiltak")
st.caption("Tallene sier hva, ikke hvorfor. Tre mulige forklaringer, som kan gjelde samtidig.")

FORKLARINGER = [
    ("For mange direkte rapporter per leder.",
     "Tell direkte rapporter per leder i HR-systemet (finnes ikke i dashbordet).",
     "Én ny lederrolle, helst intern, valgt ut fra lederpotensial og ikke salgstall. "
     "Billigere alternativ: teamlederrolle uten fullt personalansvar."),
    ("Salgslederne har egne salgsmål, så 1:1 og utvikling taper når det er travelt.",
     "Lederavtaler og bonusmodell.",
     "Knytt en del av lederens mål til oppfølging og utvikling av teamet."),
    ("Lederne har ikke fått lederutvikling.",
     "Samtaler med lederne.",
     "Lederutvikling: hvordan se og bruke styrkene til hver enkelt, og hvordan holde gode 1:1."),
]
for kolonne, (aarsak, sjekk, tiltak) in zip(st.columns(3, gap="medium"), FORKLARINGER):
    with kolonne.container(border=True):
        st.markdown(f":blue[**Mulig årsak**]\n\n{aarsak}\n\n"
                    f":blue[**Slik sjekkes det**]\n\n{sjekk}\n\n"
                    f":blue[**Tiltak**]\n\n{tiltak}")

st.markdown("**Uansett:** felles struktur for månedlige 1:1 og utviklingsplan for hver selger.")
st.caption("Sammenheng er ikke bevis for årsak, derfor sluttsamtaler og pulsundersøkelse før "
           "tiltak velges.")


# --- 3. Involvering ------------------------------------------------------------------------
st.subheader("3. Involvering")
st.markdown("Toppleder og økonomiansvarlig (budsjett), salgsdirektør og salgsledere (eier "
            "endringen, HR støtter), tillitsvalgte (organiseringen drøftes med dem før "
            "beslutning) og selgerne (pulsundersøkelse før og etter).")


# --- 4. Måling -----------------------------------------------------------------------------
st.subheader("4. Måling")
mal_1til1 = b.prosent(i.CASE_MAL_1TIL1, 0)
fra_1til1 = (f"Mot {mal_1til1}" if skjult(k_salg["andel_jevnlige"])
             else f"Fra {b.prosent(k_salg['andel_jevnlige'], 0)} til {mal_1til1}")
st.markdown(
    "| Når | Hva | Mål |\n"
    "|---|---|---|\n"
    f"| 3 mnd | Andel jevnlige 1:1 og om lederutviklingen er i gang | {fra_1til1} |\n"
    "| 6 mnd | eNPS og pulsspørsmålet «min leder følger meg opp» | eNPS minst på selskapets nivå |\n"
    "| 12 mnd | Frivillig turnover og andel besatt internt | Frivillig turnover ned mot selskapets nivå |"
)
st.caption("Andelen 1:1 brukes til å følge tiltaket, ikke til å vurdere den enkelte leder.")

# Om dashbordet: hvorfor det er bygget slik, hva som bevisst er utelatt, hvordan det er
# bygget sammen med AI, og hva som måtte vært på plass med ekte data. Siden gjør valgene
# synlige for den som åpner lenken, ikke bare for den som leser README.
# Teksten under «Slik har jeg tenkt» og «Med ekte data» er Tanias egne formuleringer fra
# README («Mine valg» og «Slik kan dette tas i bruk hos dere»). Endres de ett sted, bør de
# endres begge steder.

import streamlit as st

import utseende as u
from filtre import IKONER, SPORSMAL

st.set_page_config(page_title="Om dashbordet · HR-dashbord", layout="wide")

u.topp("Om dashbordet", SPORSMAL["Om dashbordet"], IKONER["Om dashbordet"])

st.markdown(
    "Dashbordet er bygget som et porteføljeprosjekt: et eksempel på hvordan jeg ville jobbet "
    "med HR-data sammen med en ledergruppe i et selskap med 50-500 ansatte. Bakgrunnen min er "
    "organisasjonspsykologi, og det preger valgene."
)


# --- Slik har jeg tenkt (Tanias formuleringer fra README) ----------------------------------
st.subheader("Slik har jeg tenkt")
st.markdown(
    "- **Få nøkkeltall som ledelsen faktisk bruker.** Turnover, sykefravær, rekruttering, "
    "bemanning og engasjement svarer på tre spørsmål: Hvor er risikoen, hva koster den, og har "
    "vi folkene vi trenger? Definisjonene følger ISO 30414:2025, så tallene kan forklares og "
    "sammenlignes over tid.\n"
    "- **Kostnad i kroner.** Turnover og sykefravær vises også i kroner, fordi det er språket "
    "en økonomidirektør handler på. Antakelsene står åpent og kan justeres.\n"
    "- **Små endringer er ikke alarmer.** Pilene får bare farge når endringen er stor nok til "
    "å bety noe, og når tallet bygger på nok personer. Ellers er de grå.\n"
    "- **Personvern styrer designet.** Grupper under fem vises ikke, og sensitive tall vises "
    "bare i faste perioder, så ingen kan regne ut små grupper ved å sammenligne utvalg. "
    "Reglene reduserer risikoen, men hindrer den ikke. Derfor er tilgangsstyring like viktig "
    "som teknikken.\n"
    "- **Regelbaserte innsikter.** Forsiden peker på de største avvikene etter faste regler. "
    "Hver innsikt kan etterprøves, og skjulte grupper nevnes aldri.\n"
    "- **Forskning før egne data.** Et selskap med 230 ansatte ansetter for få til å avgjøre "
    "hvilken rekrutteringsmetode som virker best. Dashbordet viser derfor hva forskningen sier "
    "(Sackett mfl., 2022), og bruker egne data til å følge med.\n"
    "- **Det jeg bevisst lot være:** lønn per team, testresultater og kompetansevurderinger "
    "av enkeltpersoner. Det er sensitivt, og nytten står ikke i forhold til risikoen. Jeg "
    "måler heller ikke formelle medarbeidersamtaler to ganger i året. De sier om en rutine er "
    "fulgt, ikke om noen utvikler seg. Jevnlige 1:1 med lederen sier mer."
)


# --- Bygget sammen med AI ------------------------------------------------------------------
st.subheader("Slik er det bygget, sammen med AI")
st.markdown(
    "Jeg skrev reglene selv, i vanlig norsk: definisjonene av hvert nøkkeltall, "
    "personvernreglene og hvordan tallene skal vises. Den kravspesifikasjonen ligger åpent i "
    "repoet (`CLAUDE.md`). En AI-assistent (Claude Code) skrev koden etter reglene, og "
    "automatiske tester kontrollerer at formlene, personvernreglene og tekstreglene holdes, "
    "hver gang noe endres. Jeg kan forklare hver beregning.\n\n"
    "Lederbriefen på forsiden viser hvordan jeg ville brukt AI med persondata: modellen får "
    "bare ferdig prikkede tall som allerede står på forsiden, teksten leses og godkjennes av "
    "et menneske før den vises, den er tydelig merket, og den stiller spørsmål til ledermøtet "
    "i stedet for å foreslå tiltak. Tiltakene forblir regelbaserte, så de kan etterprøves."
)


# --- Med ekte data -------------------------------------------------------------------------
st.subheader("Med ekte data ville jeg")
st.markdown(
    "- først avklart definisjoner og datakvalitet med HR og økonomi, og latt ledergruppen "
    "sette tersklene for status\n"
    "- gitt tilgang bare til HR-ledelse og ledergruppen, lagret dataene i Norge eller EU, og "
    "hatt databehandleravtale med leverandøren\n"
    "- vurdert om det trengs en personvernkonsekvensvurdering (DPIA) før oppstart\n"
    "- ikke sendt tall til en ekstern AI-tjeneste før det var vurdert og dokumentert, selv om "
    "aggregerte, prikkede tall i utgangspunktet ikke er personopplysninger"
)

st.info(
    "**Hva reglene ikke gjør:** Faste perioder, femregelen og sekundær prikking reduserer "
    "risikoen for at tall om små grupper kan utledes, men de hindrer den ikke. Ingen tekniske "
    "regler kan helt hindre det i et interaktivt verktøy. Den som kjenner organisasjonen, kan "
    "dessuten koble tallene med egen kunnskap. Den viktigste beskyttelsen er derfor "
    "tilgangsstyring.",
    icon=":material/info:",
)

st.caption(
    "Koden, alle definisjonene og datamodellen ligger åpent på GitHub: "
    "[tanianaess/hr-dashboard](https://github.com/tanianaess/hr-dashboard). "
    "Bygget med Python, pandas og Streamlit."
)

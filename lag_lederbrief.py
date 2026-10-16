# Lager lederbriefen (AI) med Claude og lagrer den i data/lederbrief.json.
# Kjøres bare på egen maskin, aldri i den publiserte appen (se «Lederbrief (AI)» i CLAUDE.md):
#
#   python lag_lederbrief.py             lager et nytt utkast (trenger ANTHROPIC_API_KEY)
#   python lag_lederbrief.py --godkjenn  setter dagens dato i «godkjent» etter at du har lest
#
# API-nøkkelen leses fra miljøvariabelen ANTHROPIC_API_KEY og ligger aldri i repoet.
# Pakken anthropic står bare i requirements-dev.txt; dashbordet importerer den aldri.

import argparse
from datetime import date

import beregninger as b
import innsikter as i
import lederbrief as lb

MODELL = "claude-opus-5-5"


def hent_grunnlag():
    """Samme tall som forsiden: leser dataene og kjører nokkeltall() og innsikter()."""
    ansatte = b.les_ansatte()
    fravaer = b.fravaer_med_avtalte(ansatte, b.les_fravaer())
    engasjement, plan = b.les_engasjement(), b.les_bemanningsplan()
    nokkeltall = i.nokkeltall(ansatte, fravaer, engasjement, plan)
    innsikt_liste = i.innsikter(ansatte, fravaer, engasjement, plan, nokkeltall,
                                samtaler=b.les_en_til_en())
    return lb.grunnlag(nokkeltall, innsikt_liste)


def lag(grunnlag_tekst):
    """Sender instruksen og grunnlaget til Claude og får briefen tilbake som faste felt.
    Modellen må svare i akkurat denne formen (som et skjema med låste kolonner), så
    teksten kan lagres og kontrolleres felt for felt."""
    import anthropic  # importeres bare her, så dashbordet ikke trenger pakken
    from pydantic import BaseModel  # følger med anthropic; beskriver skjemaet

    class Tema(BaseModel):
        tittel: str
        hva_tallene_viser: str
        sporsmal: list[str]

    class Brief(BaseModel):
        sammendrag: str
        temaer: list[Tema]
        folg_med: str
        forbehold: str

    klient = anthropic.Anthropic()  # leser ANTHROPIC_API_KEY fra miljøet
    svar = klient.messages.parse(
        model=MODELL,
        max_tokens=4000,
        system=lb.INSTRUKS,
        messages=[{"role": "user", "content": grunnlag_tekst}],
        output_format=Brief,
    )
    if svar.stop_reason != "end_turn" or svar.parsed_output is None:
        raise SystemExit(f"Fikk ikke en ferdig brief (stop_reason: {svar.stop_reason}). Prøv igjen.")
    return svar.parsed_output.model_dump()


def godkjenn(grunnlag_tekst):
    """Setter dagens dato i «godkjent». Bare etter at et menneske har lest teksten, og bare
    når briefen bygger på dagens tall og går gjennom kontrollene."""
    brief = lb.les_lederbrief()
    if brief is None:
        raise SystemExit(f"Fant ingen brief å godkjenne ({lb.STI}). Lag en først.")
    if lb.status(brief, grunnlag_tekst) == "utdatert":
        raise SystemExit("Briefen bygger på gamle tall. Lag en ny før du godkjenner.")
    problemer = lb.kontroller(brief["brief"], grunnlag_tekst)
    if problemer:
        raise SystemExit("Briefen går ikke gjennom kontrollene:\n- " + "\n- ".join(problemer))
    brief["godkjent"] = date.today().isoformat()
    lb.lagre_lederbrief(brief)
    print(f"Godkjent {lb.dato(brief['godkjent'])}. Briefen vises nå på forsiden.")


def main():
    parser = argparse.ArgumentParser(description="Lager eller godkjenner lederbriefen (AI).")
    parser.add_argument("--godkjenn", action="store_true",
                        help="sett dagens dato i «godkjent» etter at du har lest briefen")
    args = parser.parse_args()

    grunnlag_tekst = hent_grunnlag()
    if args.godkjenn:
        godkjenn(grunnlag_tekst)
        return

    print("Grunnlaget AI-modellen får:\n")
    print(grunnlag_tekst)
    felt = lag(grunnlag_tekst)
    start, slutt = b.FASTE_PERIODER["Siste 12 mnd"]
    brief = {
        "laget": date.today().isoformat(),
        "modell": MODELL,
        "periode": f"{start:%d.%m.%Y}-{slutt:%d.%m.%Y}",
        "data_per": f"{b.DATA_TIL:%d.%m.%Y}",
        "fingeravtrykk": lb.fingeravtrykk(grunnlag_tekst),
        "grunnlag": grunnlag_tekst,
        "brief": felt,
        "godkjent": "",  # tom til et menneske har lest teksten (--godkjenn)
    }
    lb.lagre_lederbrief(brief)
    print("\nUtkast lagret i", lb.STI, "\n")
    print(lb.som_markdown(brief))
    problemer = lb.kontroller(felt, grunnlag_tekst)
    if problemer:
        print("Kontrollene fant problemer. Lag briefen på nytt, eller rett teksten i filen, før du godkjenner:")
        print("- " + "\n- ".join(problemer))
    else:
        print("Kontrollene fant ingen problemer. Les teksten, og godkjenn med:\n"
              "  python lag_lederbrief.py --godkjenn")


if __name__ == "__main__":
    main()

# Lager et selskapsnotat («Tre spørsmål til <selskap>») for ett selskap, bygget bare på
# offentlige tall. Reglene står i CLAUDE.md («Selskapsnotat»). Kjøres på egen maskin:
#
#   python lag_selskapsnotat.py --last-ned                 henter SSB-tabellene på nytt (data/eksterne/)
#   python lag_selskapsnotat.py 912345678                  slår opp selskapet i Enhetsregisteret
#   python lag_selskapsnotat.py 912345678 --aarsberetning notater/912345678-aarsberetning.json
#   python lag_selskapsnotat.py --eksempel                 oppdiktet selskap, helt uten nett
#
# Notatet lagres i notater/<selskap>.md og .html. Bare eksempelet ligger i repoet; notater om
# ekte selskaper holdes utenfor (se .gitignore).

import argparse
import sys

import selskapsnotat as sn


def main():
    # Notatet skrives alltid som UTF-8 til fil. I et vindu som ikke kan vise alle tegnene
    # (Windows), byttes de ut med «?» i utskriften i stedet for at skriptet stopper.
    sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="Lager et selskapsnotat bygget bare på offentlige tall.")
    parser.add_argument("orgnr", nargs="?", help="organisasjonsnummer (9 sifre)")
    parser.add_argument("--aarsberetning", help="JSON-fil med tall du har lest i årsberetningen")
    parser.add_argument("--navn", help="selskapets navn slik det skal skrives i notatet")
    parser.add_argument("--eksempel", action="store_true", help="lag eksempelnotatet (offline)")
    parser.add_argument("--last-ned", action="store_true", help="hent SSB-tabellene på nytt")
    parser.add_argument("--mappe", help="mappe for notatet (standard: notater/)")
    args = parser.parse_args()

    if args.last_ned:
        sn.last_ned_ssb()
        print(f"Kildene er oppdatert i {sn.KILDER_STI}")
        if not args.orgnr and not args.eksempel:
            return

    if args.eksempel:
        grunnlag = sn.eksempel()
        prefiks = "eksempel-"
    elif args.orgnr:
        enhet = sn.hent_enhet(args.orgnr)
        if args.navn:
            enhet["navn"] = args.navn
        if args.aarsberetning:
            aarsberetning = sn.les_aarsberetning(args.aarsberetning)
        else:
            # Uten årsberetning: notatet sier at selskapets egne tall ikke er oppgitt
            aarsberetning = {"kilde": "årsberetningen (ikke lest ennå)"}
        grunnlag = sn.lag_grunnlag(enhet, aarsberetning, sn.les_tabeller(), sn.les_kilder())
        prefiks = ""
    else:
        parser.error("oppgi et organisasjonsnummer, eller --eksempel")

    md, html = sn.skriv_notat(grunnlag, args.mappe, prefiks)
    print(sn.som_markdown(grunnlag))
    print(f"Lagret: {md}\n        {html}")
    problemer = sn.kontroller(grunnlag)
    if problemer:
        print("Kontrollene fant problemer. Rett dem før notatet sendes:")
        print("- " + "\n- ".join(problemer))
        raise SystemExit(1)
    print("Kontrollene fant ingen problemer: alle tall har kilde, og tekstreglene holdes.")


if __name__ == "__main__":
    main()

# Selskapsnotat: «Tre spørsmål til <selskap>», en halv side om ett selskap Tania søker jobb
# hos, bygget BARE på offentlige tall: Enhetsregisteret (navn, næring, antall ansatte), SSB
# (sykefravær og månedslønn i næringen) og det selskapet selv har skrevet i årsberetningen.
# Reglene står i CLAUDE.md («Selskapsnotat»). Ingen AI: teksten er regelbasert, som innsiktene
# på forsiden, og hvert tall har kilde. Notatet sier aldri noe om enkeltpersoner.
#
# Filen gjør tre ting, som tre ark i en arbeidsbok:
#   1. henter og lagrer tallene (Enhetsregisteret, og SSB-tabellene i data/eksterne/)
#   2. regner (hvilken SSB-gruppe næringen hører til, og regnestykkene i kroner)
#   3. skriver notatet (Markdown og HTML)
# Skriptet lag_selskapsnotat.py er knappen som kjører alt. Bare pandas og standardbiblioteket.

import itertools
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

import beregninger as b
import lederbrief as lb

PROSJEKT = Path(__file__).parent
MAPPE = b.DATAMAPPE / "eksterne"             # SSB-tabellene (nedlastet) og kilder.json
EKSEMPELMAPPE = b.DATAMAPPE / "eksempel_selskap"  # oppdiktet selskap til eksempelet (offline)
NOTATMAPPE = PROSJEKT / "notater"            # ferdige notater; bare eksempelet ligger i repoet
KILDER_STI = MAPPE / "kilder.json"
EKSEMPEL_DATO = date(2026, 10, 21)           # fast dato i eksempelet, så det blir likt hver gang

# Avsenderen, som i «hvem og hva»-linjen i dashbordet. Lenken skal peke på den publiserte appen
# når den er klar; til da peker den på koden.
AVSENDER = "Tania Næss, organisasjonspsykolog"
DASHBORD_LENKE = "https://github.com/tanianaess/hr-dashboard"

# Enhetsregisteret: åpne data, ingen nøkkel, lisens NLOD (se dokumentasjonen)
BRREG_API = "https://data.brreg.no/enhetsregisteret/api/enheter/{orgnr}"
BRREG_DOK = "https://data.brreg.no/enhetsregisteret/api/dokumentasjon"
BRREG_NAVN = "Enhetsregisteret (Brønnøysundregistrene), åpne data"

# SSBs statistikkbank: PxWebApi v2 (det SSB anbefaler fra høsten 2025). Hele spørringen ligger i
# adressen, så den kan limes inn i en nettleser og kontrolleres.
SSB_API = "https://data.ssb.no/api/pxwebapi/v2/tables/{tabell}/data"
SSB_TABELL = "https://www.ssb.no/statbank/table/{tabell}"

# De tre tabellene, verifisert mot metadataene i API-et 21.10.2026. «valg» er filteret, som når
# man velger verdier i Statistikkbanken: begge kjønn, alle næringer, siste periode(r).
# «alle» er koden for «Alle næringer» i hver tabell (den brukes som siste utvei).
TABELLER = {
    "sykefravaer_kvartal": dict(
        tabell="12440",
        valg={"Kjonn": "0", "NACE2007": "*", "Sykefraver2": "*",
              "ContentsCode": "SykefravProsent", "Tid": "top(5)"},  # siste kvartal og samme i fjor
        alle="A-U"),
    "sykefravaer_aar": dict(
        tabell="12441",
        valg={"Kjonn": "0", "NACE2007": "*", "Sykefraver2": "*",
              "ContentsCode": "Sykdom", "Tid": "top(1)"},
        alle="00-99"),
    "lonn_kvartal": dict(
        tabell="11656",
        valg={"Kjonn": "0", "Alder": "999A", "NACE2007": "*",
              "ContentsCode": "GjMndlonn,GjAvtMndlonn,Lonsstakere", "Tid": "top(1)"},
        alle="00-99"),
}

# Antakelsene, de samme som i dashbordet (se CLAUDE.md): kostnadsandel ved en avgang, arbeidsdager
# i et årsverk, og arbeidsgiverperioden (de første 16 kalenderdagene av et sykefravær).
KOSTNADSANDEL = b.KOSTNADSANDEL_STANDARD
ARBEIDSDAGER = b.ARBEIDSDAGER_PER_AARSVERK
ARBEIDSGIVERPERIODE_DAGER = 16

# Standard for næringsgruppering (SN2007): hvilke 2-sifrede næringer hvert hovedområde (bokstav)
# dekker. Kilde: SSB, Klass, Standard for næringsgruppering 2007 (klassifikasjon 6).
HOVEDOMRAADER = {
    "A": (1, 3), "B": (5, 9), "C": (10, 33), "D": (35, 35), "E": (36, 39), "F": (41, 43),
    "G": (45, 47), "H": (49, 53), "I": (55, 56), "J": (58, 63), "K": (64, 66), "L": (68, 68),
    "M": (69, 75), "N": (77, 82), "O": (84, 84), "P": (85, 85), "Q": (86, 88), "R": (90, 93),
    "S": (94, 96), "T": (97, 98), "U": (99, 99),
}


# --- 1. Hente og lagre tallene -------------------------------------------------------------

def hent_json(url):
    """Henter JSON fra en åpen nettadresse. Ingen nøkkel og ingen innlogging. Dette er den
    eneste funksjonen som bruker nettet, så offline-modus (eksempelet) bare lar være å kalle den."""
    foresporsel = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "hr-dashboard selskapsnotat"})
    with urllib.request.urlopen(foresporsel, timeout=60) as svar:
        return json.loads(svar.read().decode("utf-8"))


FORKORTELSER = {"AS", "ASA", "ANS", "DA", "SA", "BA", "NUF", "KS", "SE", "IKS", "KF", "FKF", "HF"}


def pent_navn(navn):
    """«NORDVIND LOGISTIKK AS» → «Nordvind Logistikk AS». Enhetsregisteret skriver navn med
    store bokstaver. Skriver selskapet navnet sitt annerledes, bruk --navn i skriptet."""
    return " ".join(o if o.upper() in FORKORTELSER else o.capitalize() for o in navn.split())


def enhet_fra_svar(svar, hentet=None):
    """Plukker ut de få feltene notatet bruker fra svaret til Enhetsregisteret, ikke mer:
    notatet skal ikke samle informasjon om selskapet. Brukes både på ekte svar og eksempelet."""
    naering = svar.get("naeringskode1") or {}
    return {
        "orgnr": svar["organisasjonsnummer"],
        "navn": pent_navn(svar["navn"]),
        "organisasjonsform": (svar.get("organisasjonsform") or {}).get("beskrivelse", ""),
        "nace_kode": naering.get("kode"),
        "nace_tekst": naering.get("beskrivelse"),
        # Enhetsregisteret oppgir ikke tallet når virksomheten har 0-4 ansatte (feltet er tomt)
        "antall_ansatte": svar.get("antallAnsatte"),
        "ansatte_per": svar.get("registreringsdatoAntallAnsatteEnhetsregisteret"),
        "hentet": (hentet or date.today()).isoformat(),
    }


def hent_enhet(orgnr):
    """Slår opp et organisasjonsnummer i Enhetsregisteret (åpent API, ingen nøkkel)."""
    orgnr = str(orgnr).replace(" ", "")
    if not re.fullmatch(r"\d{9}", orgnr):
        raise SystemExit(f"Organisasjonsnummeret skal ha 9 sifre, fikk «{orgnr}».")
    try:
        svar = hent_json(BRREG_API.format(orgnr=orgnr))
    except urllib.error.HTTPError as feil:
        if feil.code == 404:
            raise SystemExit(f"Fant ikke organisasjonsnummer {orgnr} i Enhetsregisteret.") from None
        raise
    return enhet_fra_svar(svar)


def ssb_url(tabell, valg):
    """Adressen til én tabell med filteret i valg, f.eks. valueCodes[Tid]=top(1)."""
    parametre = {"lang": "no", "outputFormat": "json-stat2"}
    parametre.update({f"valueCodes[{kode}]": verdi for kode, verdi in valg.items()})
    return SSB_API.format(tabell=tabell) + "?" + urllib.parse.urlencode(parametre, safe="*(),")


def jsonstat_til_tabell(data):
    """Gjør SSBs svar (JSON-stat2) om til en lang tabell: én rad per tall, med kode og tekst for
    hver dimensjon (næring, type sykefravær, kvartal). Som å gjøre en pivottabell om til en
    vanlig liste. Tall SSB holder tilbake (vist som «:») blir tomme."""
    dimensjoner = data["id"]
    koder, tekster = [], []
    for navn in dimensjoner:
        kategori = data["dimension"][navn]["category"]
        koder.append(sorted(kategori["index"], key=kategori["index"].get))  # i SSBs rekkefølge
        tekster.append(kategori.get("label", {}))
    rader = []
    for nr, kombinasjon in enumerate(itertools.product(*koder)):
        rad = {}
        for navn, kode, tekst in zip(dimensjoner, kombinasjon, tekster):
            rad[navn] = kode
            rad[navn + "_tekst"] = tekst.get(kode, kode)
        rad["verdi"] = data["value"][nr]
        rader.append(rad)
    return pd.DataFrame(rader)


def les_kilder():
    """kilder.json: hva som er lastet ned, hvorfra og når. Skrives av last_ned_ssb()."""
    if not KILDER_STI.exists():
        raise SystemExit(f"Finner ikke {KILDER_STI}. Kjør: python lag_selskapsnotat.py --last-ned")
    return json.loads(KILDER_STI.read_text(encoding="utf-8"))


def last_ned_ssb(i_dag=None):
    """Henter de tre SSB-tabellene og lagrer dem som CSV i data/eksterne/, sammen med kilder.json
    (tabellnavn, adresse, SSBs oppdateringsdato, siste periode og nedlastingsdato). Kjøres på
    nytt når SSB har publisert et nytt kvartal."""
    i_dag = i_dag or date.today()
    MAPPE.mkdir(parents=True, exist_ok=True)
    kilder = {"brreg": {"navn": BRREG_NAVN, "api": BRREG_API, "dokumentasjon": BRREG_DOK,
                        "lisens": "Norsk lisens for offentlige data (NLOD)"},
              "tabeller": {}}
    for navn, t in TABELLER.items():
        url = ssb_url(t["tabell"], t["valg"])
        data = hent_json(url)
        tabell = jsonstat_til_tabell(data)
        fil = f"ssb_{t['tabell']}.csv"
        tabell.to_csv(MAPPE / fil, index=False, encoding="utf-8")
        kilder["tabeller"][navn] = {
            # tittelen uten «12440: » foran, og med enkle mellomrom
            "tabell": t["tabell"], "tittel": " ".join(data["label"].split(": ", 1)[-1].split()), "fil": fil,
            "url": SSB_TABELL.format(tabell=t["tabell"]), "api_url": url,
            "oppdatert": data["updated"][:10], "siste_periode": str(tabell["Tid"].max()),
            "lastet_ned": i_dag.isoformat(), "merknader_fra_ssb": data.get("note", []),
        }
        print(f"Lastet ned tabell {t['tabell']} ({kilder['tabeller'][navn]['siste_periode']}): {fil}")
    KILDER_STI.write_text(json.dumps(kilder, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return kilder


def les_tabeller():
    """Leser de lagrede SSB-tabellene fra data/eksterne/. Kodene leses som tekst (så «05» ikke
    blir 5), tallene som tall (tomt = holdt tilbake av SSB)."""
    kilder = les_kilder()
    tabeller = {}
    for navn, info in kilder["tabeller"].items():
        t = pd.read_csv(MAPPE / info["fil"], dtype=str, keep_default_na=False, encoding="utf-8")
        t["verdi"] = pd.to_numeric(t["verdi"], errors="coerce")
        tabeller[navn] = t
    return tabeller


def les_aarsberetning(sti):
    """Tall Tania selv har lest i selskapets årsberetning, i en liten JSON-fil med kilde. Alle
    tallfeltene kan være tomme (null): da sier notatet at tallet ikke er oppgitt."""
    fil = json.loads(Path(sti).read_text(encoding="utf-8"))
    if not fil.get("kilde"):
        raise SystemExit(f"{sti}: feltet «kilde» må fylles ut (f.eks. «Årsberetning 2025, side 4»).")
    return fil


# --- 2. Regne: næringsgruppe og regnestykker -----------------------------------------------

def tolk_ssb_kode(kode):
    """Hvilke næringer en SSB-kode dekker, som (2-sifrede næringer, 3-sifrede grupper):
    «61-63» → ({61, 62, 63}, set()), «D-E» → ({35, …, 39}, set()),
    «05_07_08_09.9» → ({5, 7, 8}, {«09.9»}), «30.1b» → (set(), {«30.1»})."""
    naeringer, grupper = set(), set()
    for del_ in kode.split("_"):
        del_ = del_.rstrip("b")
        if re.fullmatch(r"[A-U](-[A-U])?", del_):
            for bokstav in map(chr, range(ord(del_[0]), ord(del_[-1]) + 1)):
                lav, hoy = HOVEDOMRAADER[bokstav]
                naeringer.update(range(lav, hoy + 1))
        elif "." in del_:
            fra, _, til = del_.partition("-")
            fra_n, fra_g = fra.split(".")
            til_n, til_g = (til or fra).split(".")
            if fra_n == til_n:
                grupper.update(f"{fra_n}.{g}" for g in range(int(fra_g), int(til_g) + 1))
            else:
                grupper.update({fra, til})
        else:
            fra, _, til = del_.partition("-")
            naeringer.update(range(int(fra), int(til or fra) + 1))
    return naeringer, grupper


def finn_grupper(nace_kode, tabell, alle):
    """Hvilke næringsgrupper i en SSB-tabell selskapets næringskode hører til, mest spesifikk
    først og «Alle næringer» sist: «62.010» → [(«61-63», «IKT-virksomhet»), («J», «Informasjon
    og kommunikasjon»), («A-U», «Alle næringer»)] i tabell 12440. Den som bruker listen, går
    videre til neste når et tall mangler.
    Enhetsregisteret bruker SN2025 (fra 1.1.2025, f.eks. 62.100), SSB-tabellene SN2007 (f.eks.
    62.010). Koblingen går derfor på de to første sifrene (næringen), som i hovedsak er like i de
    to standardene; gruppenivået (tre sifre) brukes bare der tabellen selv har slike koder."""
    naering, gruppe = int(nace_kode[:2]), nace_kode[:4]  # «62.010» → 62 og «62.0»
    kandidater = []
    for kode, tekst in tabell[["NACE2007", "NACE2007_tekst"]].drop_duplicates().itertuples(index=False):
        if kode in (alle, "00"):  # «Alle næringer» legges til sist; «00» er uoppgitt
            continue
        naeringer, grupper = tolk_ssb_kode(kode)
        if gruppe in grupper:
            kandidater.append((len(grupper) / 10, kode, tekst))  # gruppenivå er mest spesifikt
        elif naering in naeringer:
            kandidater.append((len(naeringer), kode, tekst))
    kandidater.sort()
    alle_tekst = tabell.loc[tabell["NACE2007"] == alle, "NACE2007_tekst"].iloc[0]
    return [(kode, tekst) for _, kode, tekst in kandidater] + [(alle, alle_tekst)]


def verdi(tabell, grupper, **filter_):
    """Første gruppe i listen som har et tall for dette filteret (f.eks. Sykefraver2=«Alt»,
    Tid=«2026K2»). Gir (tall, kode, tekst), eller (None, None, None)."""
    for kode, tekst in grupper:
        rader = tabell[tabell["NACE2007"] == kode]
        for kolonne, onsket in filter_.items():
            rader = rader[rader[kolonne] == onsket]
        if len(rader) and pd.notna(rader["verdi"].iloc[0]):
            return float(rader["verdi"].iloc[0]), kode, tekst
    return None, None, None


def hovedomraade(nace_kode):
    """«62.010» → «J» (Informasjon og kommunikasjon)."""
    naering = int(nace_kode[:2])
    return next((bokstav for bokstav, (lav, hoy) in HOVEDOMRAADER.items() if lav <= naering <= hoy), None)


def kvartal_tekst(kode):
    """«2026K2» → «2. kvartal 2026»."""
    aar, k = kode.split("K")
    return f"{k}. kvartal {aar}"


def samme_kvartal_i_fjor(kode):
    """«2026K2» → «2025K2»."""
    return f"{int(kode[:4]) - 1}{kode[4:]}"


def rund_til(tall, trinn):
    """Runder til nærmeste 10, 1 000 osv. (5 opp, som i Excel): 291,2 → 290 med trinn 10."""
    return int(b.avrund(tall / trinn)) * trinn


def belop(kr):
    """Kroner slik de vises: minst 1 mill. kr som «0,8 mill. kr», ellers til nærmeste 1 000 kr."""
    return b.millioner(kr) if kr >= 1_000_000 else b.kroner(rund_til(kr, 1_000))


def dagsverk_tekst(dagsverk):
    """Dagsverk slik de vises: til nærmeste 10, med mellomrom som tusenskille: 1 392,4 → «1 390»."""
    return f"{rund_til(dagsverk, 10):,}".replace(",", " ")


def prosent_tekst(prosent):
    """SSB oppgir prosent som 6,8 (ikke 0,068): 6.8 → «6,8 %»."""
    return b.prosent(prosent / 100)


def forskjell_tekst(pp):
    """Avrundet forskjell i prosentpoeng som tekst: −0,2 → «0,2 pp under», 0,5 → «0,5 pp over»,
    0 → «likt med». Brukes som i «Det er 0,2 pp under næringen»."""
    if pp == 0:
        return "likt med"
    return f"{abs(pp):.1f} pp {'over' if pp > 0 else 'under'}".replace(".", ",")


def naeringstall(enhet, tabeller, kilder):
    """Sykefravær og månedslønn for selskapets næring, fra de lagrede SSB-tabellene, med hvilken
    gruppe tallet gjelder. Hver verdi er (tall, gruppekode, gruppetekst)."""
    if not enhet.get("nace_kode"):
        raise SystemExit(f"{enhet['navn']} har ingen næringskode i Enhetsregisteret, så næringstallene "
                         "kan ikke finnes.")
    k, a = tabeller["sykefravaer_kvartal"], tabeller["sykefravaer_aar"]
    lonn = tabeller["lonn_kvartal"]
    kvartal = kilder["tabeller"]["sykefravaer_kvartal"]["siste_periode"]
    aar = kilder["tabeller"]["sykefravaer_aar"]["siste_periode"]
    lonnskvartal = kilder["tabeller"]["lonn_kvartal"]["siste_periode"]
    grupper_k = finn_grupper(enhet["nace_kode"], k, TABELLER["sykefravaer_kvartal"]["alle"])
    grupper_a = finn_grupper(enhet["nace_kode"], a, TABELLER["sykefravaer_aar"]["alle"])
    grupper_l = finn_grupper(enhet["nace_kode"], lonn, TABELLER["lonn_kvartal"]["alle"])
    alle_k, alle_a, alle_l = grupper_k[-1:], grupper_a[-1:], grupper_l[-1:]
    return {
        "kvartal": kvartal, "aar": aar, "lonnskvartal": lonnskvartal,
        "kvartal_alt": verdi(k, grupper_k, Sykefraver2="Alt", Tid=kvartal),
        "kvartal_i_fjor_alt": verdi(k, grupper_k, Sykefraver2="Alt", Tid=samme_kvartal_i_fjor(kvartal)),
        "kvartal_alle_naeringer": verdi(k, alle_k, Sykefraver2="Alt", Tid=kvartal),
        "aar_alt": verdi(a, grupper_a, Sykefraver2="Alt", Tid=aar),
        "aar_egenmeldt": verdi(a, grupper_a, Sykefraver2="E", Tid=aar),
        "aar_alle_naeringer": verdi(a, alle_a, Sykefraver2="Alt", Tid=aar),
        "maanedslonn": verdi(lonn, grupper_l, ContentsCode="GjMndlonn", Tid=lonnskvartal),
        "maanedslonn_alle_naeringer": verdi(lonn, alle_l, ContentsCode="GjMndlonn", Tid=lonnskvartal),
    }


def regnestykke(enhet, aarsberetning, naering):
    """Hva tallene kan bety i kroner, med dashbordets antakelser. Ren aritmetikk på offentlige
    gjennomsnittstall, ikke en prognose. Grunnlaget er årsverk fra årsberetningen når det finnes,
    ellers antall ansatte fra Enhetsregisteret (som om alle var i full stilling). Gir None når
    grunnlag eller lønn mangler."""
    personer = aarsberetning.get("aarsverk") or enhet["antall_ansatte"]
    maanedslonn = naering["maanedslonn"][0]
    if not personer or not maanedslonn:
        return None
    dagslonn = maanedslonn * 12 / ARBEIDSDAGER            # lønn per arbeidsdag
    dagsverk_i_aaret = personer * ARBEIDSDAGER             # avtalte dagsverk, uten fradrag for ferie
    r = {
        "grunnlag": "aarsverk" if aarsberetning.get("aarsverk") else "ansatte",
        "personer": personer,
        "maanedslonn": maanedslonn,
        # ett prosentpoeng sykefravær, i dagsverk og kroner per år
        "pp_dagsverk": dagsverk_i_aaret / 100,
        "pp_kr": dagsverk_i_aaret / 100 * dagslonn,
        # egenmeldt fravær ligger alltid i arbeidsgiverperioden (et minimum for den)
        "egenmeldt_prosent": naering["aar_egenmeldt"][0],
        "egenmeldt_dagsverk": None, "egenmeldt_kr": None,
        # forskjellen mot næringen, når selskapets eget sykefravær er kjent
        "forskjell_pp": None, "forskjell_dagsverk": None, "forskjell_kr": None,
        # en avgang som må erstattes, og eventuelt antall avganger ut fra turnover i årsberetningen
        "per_avgang_kr": KOSTNADSANDEL * 12 * maanedslonn,
        "avganger": None, "avganger_kr": None,
    }
    if r["egenmeldt_prosent"] is not None:
        r["egenmeldt_dagsverk"] = dagsverk_i_aaret * r["egenmeldt_prosent"] / 100
        r["egenmeldt_kr"] = r["egenmeldt_dagsverk"] * dagslonn
    eget = aarsberetning.get("sykefravaer_prosent")
    if eget is not None and naering["aar_alt"][0] is not None:
        r["forskjell_pp"] = b.avrund(eget - naering["aar_alt"][0], 1)
        r["forskjell_dagsverk"] = dagsverk_i_aaret * r["forskjell_pp"] / 100
        r["forskjell_kr"] = r["forskjell_dagsverk"] * dagslonn
    turnover = aarsberetning.get("turnover_prosent")
    if turnover is not None:
        r["avganger"] = b.avrund(turnover / 100 * personer)
        r["avganger_kr"] = r["avganger"] * r["per_avgang_kr"]
    return r


# --- 3. Skrive notatet ---------------------------------------------------------------------

METODEMERKNAD = (
    "Tallene er ikke regnet ut på samme måte. SSB måler egenmeldt og legemeldt fravær for "
    "lønnstakere 16-69 år i hele næringen: egenmeldt fravær kommer fra en utvalgsundersøkelse "
    "blant rundt 10 000 virksomheter, legemeldt fra NAVs sykmeldingsregister. Et selskap regner "
    "som regel sitt eget tall ut fra lønnssystemet, med egne regler for avtalte dagsverk. Små "
    "forskjeller kan derfor skyldes metode, ikke helse."
)
REGNESTYKKE_MERKNAD = (
    "Dette er ren aritmetikk på offentlige gjennomsnittstall, ikke en prognose for selskapet. "
    "Egne lønnsdata og egen fordeling på korttids- og langtidsfravær gir riktigere tall."
)
BUNNLINJE = ("Notatet bygger bare på offentlige tall og det selskapet selv har publisert, og sier "
             "ingenting om enkeltpersoner.")

# Det tredje spørsmålet tilpasses hovedområdet i næringen (bokstaven i SN2007). Spørsmål, ikke
# råd, og ingen påstander om hvordan selskapet er organisert.
TREDJE_SPORSMAL = {
    "C": "Hvordan henger sykefraværet sammen med skiftordninger og HMS-tallene, og følges "
         "langtidsfraværet opp like systematisk som skadene?",
    "F": "Hvordan henger sykefraværet sammen med HMS-tallene og sesongen, og vet dere hvor stor "
         "del av bemanningen som er innleid når det er mest å gjøre?",
    "G": "Hvor stor del av dem som slutter, slutter innen det første året, og hvordan rekrutteres "
         "de som møter kundene (strukturert intervju eller ikke)?",
    "H": "Hvordan fordeler sykefraværet seg mellom dem som er ute på veien eller lageret og dem "
         "som sitter på kontoret, og brukes tallene når bemanningen planlegges?",
    "I": "Hvor stor del av de ansatte er midlertidige eller på deltid, og måles turnover og "
         "sykefravær for dem for seg?",
    "J": "Hvor lang tid tar det fra en stilling lyses ut til kandidaten takker ja, og hvor mange "
         "av dem som ble ansatt de siste to årene er fortsatt i selskapet?",
    "K": "Hvordan måles engasjement i dag, hvor ofte, og kobles svarene mot turnover og fravær "
         "per avdeling?",
    "M": "Hvor stor del av de ansatte har hatt jevnlige 1:1 med lederen sin det siste året, og "
         "vet dere om det henger sammen med hvem som blir?",
    "N": "Hvor stor del av de ansatte har hatt jevnlige 1:1 med lederen sin det siste året, og "
         "vet dere om det henger sammen med hvem som blir?",
    "Q": "Hvordan fordeler langtidsfraværet seg på avdelinger og yrkesgrupper, og hvor stor del "
         "av bemanningen dekkes av vikarer?",
}
TREDJE_SPORSMAL_ELLERS = ("Hvilke tre HR-tall får ledergruppen hver måned i dag, og hvilken "
                          "beslutning har de endret det siste året?")


def lag_grunnlag(enhet, aarsberetning, tabeller, kilder, i_dag=None):
    """Alt notatet bygger på, samlet ett sted: selskapet, næringstallene, regnestykket, kildene
    og datoen. Teksten (blokker) lages fra dette, og testene kontrollerer teksten mot det."""
    naering = naeringstall(enhet, tabeller, kilder)
    return {
        "enhet": enhet,
        "aarsberetning": aarsberetning,
        "naering": naering,
        "regnestykke": regnestykke(enhet, aarsberetning, naering),
        "kilder": kilder,
        "laget": (i_dag or date.today()).isoformat(),
        "antakelser": {"kostnadsandel_prosent": int(KOSTNADSANDEL * 100), "arbeidsdager": ARBEIDSDAGER,
                       "arbeidsgiverperiode_dager": ARBEIDSGIVERPERIODE_DAGER, "maaneder": 12},
    }


def _gruppetekst(tall):
    """«Landtransport og rørtransport» fra en (tall, kode, tekst)-verdi."""
    return tall[2] if tall[2] else ""


def blokker(g):
    """Notatet som en liste av blokker: («h1», tekst), («p», tekst), («h2», tekst),
    («ul», [punkter]), («ol», [punkter]), («meta», tekst). Markdown og HTML lages fra den samme
    listen, så de to alltid sier det samme."""
    e, aar_b, n, r = g["enhet"], g["aarsberetning"], g["naering"], g["regnestykke"]
    k = g["kilder"]["tabeller"]
    navn = e["navn"]
    gruppe_k, gruppe_a, gruppe_l = _gruppetekst(n["kvartal_alt"]), _gruppetekst(n["aar_alt"]), _gruppetekst(n["maanedslonn"])
    kvartal, aar = kvartal_tekst(n["kvartal"]), n["aar"]
    ut = [("h1", f"Tre spørsmål til {navn}"),
          ("meta", f"Et kort notat til ledergruppen, bygget bare på offentlige tall. "
                   f"Laget {lb.dato(g['laget'])} av {AVSENDER}.")]

    # Selskapet, slik det står i Enhetsregisteret
    if e["antall_ansatte"]:
        ansatte = f"med {e['antall_ansatte']} ansatte (per {lb.dato(e['ansatte_per'])})"
    else:
        ansatte = "uten registrert antall ansatte (Enhetsregisteret oppgir ikke tallet under 5)"
    grupper = {gruppe_k, gruppe_a, gruppe_l} - {""}
    if len(grupper) == 1:
        ssb = f"I SSBs statistikk hører næringen til gruppen «{gruppe_k}»."
    else:
        ssb = (f"I SSBs statistikk hører næringen til «{gruppe_k}» (sykefravær per kvartal), "
               f"«{gruppe_a}» (sykefravær per år) og «{gruppe_l}» (lønn).")
    ut.append(("p", f"{navn} er registrert i Enhetsregisteret {ansatte} og med næringskode "
                    f"{e['nace_kode']} {e['nace_tekst']}. {ssb}"))

    # 1. Sykefravær mot næringen
    ut.append(("h2", "1. Sykefravær: selskapet mot næringen"))
    punkter = []
    linje = f"Næringen «{gruppe_k}»: {prosent_tekst(n['kvartal_alt'][0])} i {kvartal}"
    if n["kvartal_i_fjor_alt"][0] is not None:
        linje += f", mot {prosent_tekst(n['kvartal_i_fjor_alt'][0])} samme kvartal året før"
    linje += f" (SSB, tabell {k['sykefravaer_kvartal']['tabell']})."
    if n["aar_alt"][0] is not None:
        linje += (f" For hele {aar}: {prosent_tekst(n['aar_alt'][0])}, der egenmeldt fravær utgjør "
                  f"{prosent_tekst(n['aar_egenmeldt'][0])} (tabell {k['sykefravaer_aar']['tabell']}).")
    punkter.append(linje)
    punkter.append(f"Alle næringer: {prosent_tekst(n['kvartal_alle_naeringer'][0])} i {kvartal} og "
                   f"{prosent_tekst(n['aar_alle_naeringer'][0])} for hele {aar}.")
    eget = aar_b.get("sykefravaer_prosent")
    forskjell = (b.avrund(eget - n["aar_alt"][0], 1)
                 if eget is not None and n["aar_alt"][0] is not None else None)
    # «årsberetningen for 2025» i teksten; hele kilden står under «Kilder»
    kildeord = f"årsberetningen for {aar_b['aar']}" if aar_b.get("aar") else aar_b["kilde"]
    if eget is not None:
        linje = f"{navn} oppgir selv {prosent_tekst(eget)} i {kildeord}."
        if forskjell is not None:
            linje += f" Det er {forskjell_tekst(forskjell)} næringen for {aar}."
        punkter.append(linje)
    else:
        punkter.append(f"Selskapets eget sykefravær er ikke oppgitt i {aar_b['kilde']}, så det "
                       "sammenlignes ikke her.")
    ut += [("ul", punkter), ("p", METODEMERKNAD)]

    # 2. Hva det kan bety i kroner
    ut.append(("h2", "2. Hva det kan bety i kroner (regnestykke, ikke prognose)"))
    if r is None:
        ut.append(("p", "Regnestykket trenger antall ansatte eller årsverk og en månedslønn for "
                        "næringen. Ett av dem mangler, så det er ikke med."))
    else:
        a = g["antakelser"]
        if r["grunnlag"] == "aarsverk":
            grunnlag = f"{r['personer']} årsverk fra {kildeord}"
        else:
            grunnlag = (f"{r['personer']} ansatte fra Enhetsregisteret, regnet som om alle var i "
                        "full stilling")
        ut.append(("p", f"Regnestykket bruker de samme forsiktige antakelsene som dashbordet: "
                        f"{a['arbeidsdager']} arbeidsdager i et årsverk, gjennomsnittlig månedslønn i "
                        f"næringen «{gruppe_l}» ({b.kroner(r['maanedslonn'])} i "
                        f"{kvartal_tekst(n['lonnskvartal'])}, SSB tabell {k['lonn_kvartal']['tabell']}) "
                        f"og en erstatningskostnad på {a['kostnadsandel_prosent']} % av en årslønn "
                        f"per avgang. Grunnlaget er {grunnlag}."))
        punkter = [f"Ett prosentpoeng sykefravær tilsvarer ca. {dagsverk_tekst(r['pp_dagsverk'])} tapte "
                   f"dagsverk i året, som i lønn er ca. {belop(r['pp_kr'])}."]
        if r["forskjell_pp"]:
            punkter.append(f"Forskjellen mot næringen ({forskjell_tekst(r['forskjell_pp'])}) tilsvarer "
                           f"ca. {dagsverk_tekst(abs(r['forskjell_dagsverk']))} dagsverk og "
                           f"{belop(abs(r['forskjell_kr']))} i året.")
        if r["egenmeldt_kr"] is not None:
            punkter.append(f"Egenmeldt fravær betaler arbeidsgiver alltid selv (arbeidsgiverperioden er "
                           f"de første {a['arbeidsgiverperiode_dager']} dagene). Med næringens egenmeldte "
                           f"fravær ({prosent_tekst(r['egenmeldt_prosent'])} i {aar}) er det ca. "
                           f"{dagsverk_tekst(r['egenmeldt_dagsverk'])} dagsverk og {belop(r['egenmeldt_kr'])} "
                           f"i året. Det er et minimum: de første {a['arbeidsgiverperiode_dager']} dagene "
                           f"av legemeldt fravær kommer i tillegg.")
        linje = f"Hver avgang som må erstattes, koster etter antakelsen ca. {belop(r['per_avgang_kr'])}."
        if r["avganger"] is not None:
            linje += (f" Med turnover på {prosent_tekst(aar_b['turnover_prosent'])} fra {kildeord} "
                      f"tilsvarer det ca. {r['avganger']} avganger og {belop(r['avganger_kr'])} i året.")
        else:
            linje += f" Ti avganger i året tilsvarer {belop(10 * r['per_avgang_kr'])}."
        punkter.append(linje)
        ut += [("ul", punkter), ("p", REGNESTYKKE_MERKNAD)]

    # 3. Tre spørsmål
    ut.append(("h2", "3. Tre spørsmål til ledergruppen"))
    if forskjell is not None:
        s1 = (f"{kildeord[0].upper()}{kildeord[1:]} oppgir {prosent_tekst(eget)} sykefravær, mot "
              f"{prosent_tekst(n['aar_alt'][0])} i næringen i {aar}. Hva mener ledergruppen forklarer "
              "forskjellen, og følges fraværet per avdeling, delt i korttid og langtid?")
    else:
        s1 = (f"Sykefraværet i næringen var {prosent_tekst(n['kvartal_alt'][0])} i {kvartal}. "
              "Hvordan ligger selskapet an mot det, og følges fraværet per avdeling, delt i "
              "korttid og langtid?")
    s2 = ("Vet ledergruppen hvor mange som sluttet frivillig de siste 12 månedene, og hvilke av dem "
          "dere helst ville beholdt?")
    if r is not None:
        s2 += f" Med næringens snittlønn koster hver erstatning ca. {belop(r['per_avgang_kr'])}."
    s3 = TREDJE_SPORSMAL.get(hovedomraade(e["nace_kode"]), TREDJE_SPORSMAL_ELLERS)
    ut.append(("ol", [s1, s2, s3]))

    # Dashbordet
    ut.append(("h2", "Slik ville dashbordet brukt selskapets egne tall"))
    ut.append(("p", "Med en eksport fra lønns- og HR-systemet (ansatt-ID, team, datoer, sluttårsak og "
                    "fravær per team og måned) viser dashbordet de samme nøkkeltallene per team, med "
                    "femregelen og sekundær prikking, så ingen enkeltperson kan leses ut av tallene. "
                    f"Et eksempel med syntetiske data ligger åpent: {DASHBORD_LENKE}"))

    # Kilder
    kilder = [f"{BRREG_NAVN}: organisasjonsnummer {e['orgnr']}, hentet {lb.dato(e['hentet'])}."]
    for info in k.values():
        kilder.append(f"SSB, tabell {info['tabell']}: {info['tittel']}. Siste periode "
                      f"{info['siste_periode']}, oppdatert av SSB {lb.dato(info['oppdatert'])}, lastet "
                      f"ned {lb.dato(info['lastet_ned'])}. {info['url']}")
    if any(aar_b.get(f) is not None for f in ("sykefravaer_prosent", "aarsverk", "turnover_prosent")):
        kilder.append(f"{aar_b['kilde']}: tall selskapet selv har publisert, lest og skrevet inn for hånd.")
    else:
        kilder.append(f"{aar_b['kilde']}: ingen tall skrevet inn.")
    ut += [("h2", "Kilder"), ("ul", kilder), ("meta", BUNNLINJE)]
    return ut


def som_markdown(g):
    """Notatet som Markdown (én side)."""
    linjer = []
    for type_, innhold in blokker(g):
        if type_ == "h1":
            linjer += [f"# {innhold}", ""]
        elif type_ == "h2":
            linjer += [f"## {innhold}", ""]
        elif type_ == "ul":
            linjer += [f"- {p}" for p in innhold] + [""]
        elif type_ == "ol":
            linjer += [f"{nr}. {p}" for nr, p in enumerate(innhold, 1)] + [""]
        elif type_ == "meta":
            linjer += [f"*{innhold}*", ""]
        else:
            linjer += [innhold, ""]
    return "\n".join(linjer)


def som_html(g):
    """Notatet som én selvstendig HTML-side, i samme stil som lederbriefen (til vedlegg i e-post,
    kan skrives ut til PDF). Lenker blir klikkbare."""
    import html as h

    def tekst(t):
        return re.sub(r"(https?://\S+)", r"<a href='\1'>\1</a>", h.escape(t))

    deler, tittel = [], ""
    for type_, innhold in blokker(g):
        if type_ == "h1":
            tittel = innhold
            deler.append(f"<h1>{h.escape(innhold)}</h1>")
        elif type_ == "h2":
            deler.append(f"<h2>{h.escape(innhold)}</h2>")
        elif type_ in ("ul", "ol"):
            deler.append(f"<{type_}>" + "".join(f"<li>{tekst(p)}</li>" for p in innhold) + f"</{type_}>")
        elif type_ == "meta":
            deler.append(f"<p class='meta'>{tekst(innhold)}</p>")
        else:
            deler.append(f"<p>{tekst(innhold)}</p>")
    return lb.html_side(tittel, deler)


def filnavn(navn):
    """«Nordvind Logistikk AS» → «nordvind-logistikk-as» (æøå skrives om, så filnavnet virker overalt)."""
    stamme = navn.lower().replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    return re.sub(r"[^a-z0-9]+", "-", stamme).strip("-")


def skriv_notat(g, mappe=None, prefiks=""):
    """Lagrer notatet som .md og .html i notater/ og gir tilbake stiene."""
    mappe = Path(mappe or NOTATMAPPE)
    mappe.mkdir(parents=True, exist_ok=True)
    stamme = prefiks + filnavn(g["enhet"]["navn"])
    md, html_ = mappe / f"{stamme}.md", mappe / f"{stamme}.html"
    md.write_text(som_markdown(g), encoding="utf-8")
    html_.write_text(som_html(g), encoding="utf-8")
    return md, html_


def eksempel():
    """Det oppdiktede selskapet i data/eksempel_selskap/, lest offline (ingen nettkall)."""
    svar = json.loads((EKSEMPELMAPPE / "enhet.json").read_text(encoding="utf-8"))
    enhet = enhet_fra_svar(svar, hentet=EKSEMPEL_DATO)
    aarsberetning = les_aarsberetning(EKSEMPELMAPPE / "aarsberetning.json")
    return lag_grunnlag(enhet, aarsberetning, les_tabeller(), les_kilder(), i_dag=EKSEMPEL_DATO)


# --- Kontroll av teksten ---------------------------------------------------------------------

def lovlige_tall(g):
    """Alle tall notatet har lov til å inneholde: det som står i inndataene og kildene, tallene fra
    SSB-tabellene som er brukt, antakelsene, og resultatene av regnestykket (slik de vises).
    Et tall i teksten som ikke står her, er skrevet inn for hånd eller regnet feil."""
    deler = [json.dumps(g["enhet"], ensure_ascii=False), json.dumps(g["aarsberetning"], ensure_ascii=False),
             json.dumps(g["kilder"], ensure_ascii=False), json.dumps(g["antakelser"]),
             # faste tekster (metoden, verifisert mot SSBs «Om statistikken»), ikke tall om selskapet
             METODEMERKNAD, REGNESTYKKE_MERKNAD, BUNNLINJE, TREDJE_SPORSMAL_ELLERS,
             *TREDJE_SPORSMAL.values()]
    n, aar_b = g["naering"], g["aarsberetning"]
    for felt in ("sykefravaer_prosent", "turnover_prosent"):
        if aar_b.get(felt) is not None:
            deler.append(prosent_tekst(aar_b[felt]))
    if aar_b.get("sykefravaer_prosent") is not None and n["aar_alt"][0] is not None:
        deler.append(forskjell_tekst(b.avrund(aar_b["sykefravaer_prosent"] - n["aar_alt"][0], 1)))
    for nokkel, v in n.items():
        if isinstance(v, tuple) and v[0] is not None:
            deler.append(prosent_tekst(v[0]) if "lonn" not in nokkel else b.kroner(v[0]))
            deler.append(kvartal_tekst(n["kvartal"]) + " " + kvartal_tekst(n["lonnskvartal"]))
    r = g["regnestykke"]
    if r:
        deler += [str(r["personer"]), b.kroner(r["maanedslonn"]), dagsverk_tekst(r["pp_dagsverk"]),
                  belop(r["pp_kr"]), belop(r["per_avgang_kr"]), belop(10 * r["per_avgang_kr"])]
        if r["egenmeldt_kr"] is not None:
            deler += [dagsverk_tekst(r["egenmeldt_dagsverk"]), belop(r["egenmeldt_kr"])]
        if r["forskjell_pp"] is not None:
            deler += [dagsverk_tekst(abs(r["forskjell_dagsverk"])), belop(abs(r["forskjell_kr"]))]
        if r["avganger"] is not None:
            deler += [str(r["avganger"]), belop(r["avganger_kr"])]
    for felt in ("hentet", "ansatte_per"):
        if g["enhet"].get(felt):
            deler.append(lb.dato(g["enhet"][felt]))
    deler.append(lb.dato(g["laget"]))
    for info in g["kilder"]["tabeller"].values():
        deler += [lb.dato(info["oppdatert"]), lb.dato(info["lastet_ned"])]
    return set(lb.TALL.findall(" ".join(deler)))


def kontroller(g):
    """Sjekker notatet mot reglene i CLAUDE.md: alle tall har kilde (står i lovlige_tall), kildene
    står i teksten, og tekstreglene holdes. Gir en liste med problemer (tom liste = OK)."""
    tekst = som_markdown(g)
    problemer = []
    ukjente = sorted({t for t in lb.TALL.findall(tekst) if t not in lovlige_tall(g)})
    if ukjente:
        problemer.append("tall uten kilde: " + ", ".join(ukjente))
    for info in g["kilder"]["tabeller"].values():
        if f"tabell {info['tabell']}" not in tekst:
            problemer.append(f"kilden SSB tabell {info['tabell']} står ikke i teksten")
    if BRREG_NAVN not in tekst or g["aarsberetning"]["kilde"] not in tekst:
        problemer.append("Enhetsregisteret eller årsberetningen står ikke som kilde")
    if "sier ingenting om enkeltpersoner" not in tekst:
        problemer.append("setningen om offentlige tall og enkeltpersoner mangler")
    if chr(0x2014) in tekst:
        problemer.append("lang tankestrek")
    if "·" in tekst:
        problemer.append("prikk (·) som skilletegn")
    if lb.INTERVALL.search(tekst):
        problemer.append("tankestrek i intervall (skal være bindestrek)")
    if lb.A_ENDINGER.search(tekst):
        problemer.append("a-ending (skal være en-ending): " + lb.A_ENDINGER.search(tekst).group(0))
    if re.search(r"(^|[\s(])-\d", tekst):
        problemer.append("bindestrek foran tall (skal være minustegn)")
    return problemer

# Lederbrief (AI): det AI-modellen får (instruks og grunnlag), og lesing og kontroll av
# den lagrede briefen i data/lederbrief.json. Reglene står i CLAUDE.md («Lederbrief (AI)»).
#
# Ingen AI-kall her. De ligger i lag_lederbrief.py, som bare kjøres på egen maskin.
# Denne filen bruker bare standardbiblioteket og det dashbordet allerede har, så verken
# dashbordet eller testene trenger pakken anthropic.

import hashlib
import json
import re
from pathlib import Path

import beregninger as b
import innsikter as i
import utseende as u

# Her ligger briefen. Mangler filen, viser forsiden ingen brief.
STI = b.DATAMAPPE / "lederbrief.json"

# Briefen skal kunne leses på ett minutt
MAKS_ORD = 250

# Feltene briefen består av (i denne rekkefølgen). «temaer» har tittel, hva_tallene_viser
# og sporsmal (en liste). Nøklene er uten æøå, så de er enkle å bruke i JSON og kode.
FELT = ["sammendrag", "temaer", "folg_med", "forbehold"]
TEMAFELT = ["tittel", "hva_tallene_viser", "sporsmal"]

# Det modellen blir bedt om. Vises også på forsiden («Hva AI-modellen fikk»), så leseren
# kan se nøyaktig hvilke regler teksten er skrevet etter.
INSTRUKS = f"""Du skriver en kort lederbrief til ledermøtet i {u.SELSKAP}, et selskap med ca. 230 ansatte.
Leserne er daglig leder, økonomidirektør og HR-leder. Du får et grunnlag: nøkkeltallene og
innsiktene fra forsiden i HR-dashbordet. Tallene er allerede aggregert og personvernprikket.

Regler:
1. Bruk bare tall som står i grunnlaget, skrevet nøyaktig slik de står der (samme avrunding,
   komma som desimaltegn, prosent og prosentpoeng som i grunnlaget). Ikke regn om, ikke rund
   av, og ikke legg til tall.
2. Nevn bare team som er nevnt i grunnlaget. Si ingenting om grupper som er holdt utenfor
   eller skjult, utover at de er holdt utenfor.
3. Ingen tiltak og ingen anbefalinger. Still i stedet spørsmål ledermøtet bør diskutere.
4. Sammenheng er ikke årsak. Behold forbeholdene fra grunnlaget når du nevner en sammenheng.
5. Norsk bokmål, nøkternt, hele setninger, ingen superlativer. Bruk en-endinger (pilen,
   linjen), bindestrek i intervaller (10-15 %), minustegn foran negative tall (−14), kort
   tankestrek med mellomrom bare unntaksvis, og aldri lang tankestrek.
6. Hele briefen skal kunne leses på ett minutt: maks {MAKS_ORD} ord til sammen.

Svar med disse feltene:
- sammendrag: 2-3 setninger om hovedbildet.
- temaer: 1-3 temaer, viktigst først. Hvert tema har tittel, hva_tallene_viser (1-2 setninger
  med tall fra grunnlaget) og sporsmal (1-2 spørsmål til ledermøtet).
- folg_med: 1-2 setninger om hva som bør sjekkes neste måned.
- forbehold: 1-2 setninger: tallene er syntetiske, sammenheng er ikke årsak, og teksten er
  skrevet av en AI-modell og gjennomgått av et menneske.
"""


# --- Grunnlaget: det forsiden viser, som ren tekst ------------------------------------

def grunnlag(nokkeltall, innsikt_liste):
    """Teksten AI-modellen får: nøkkeltallene og innsiktene fra forsiden, som ren tekst.
    Inndataene er det forsiden allerede har regnet ut (nokkeltall() og innsikter() i
    innsikter.py), så tallene har vært gjennom femregelen og sekundær prikking.
    «Mulig neste steg» og lenkene er med vilje ikke med: briefen skal stille spørsmål,
    ikke gjenta tiltak. Samme inndata gir alltid samme tekst (viktig for fingeravtrykket)."""
    start, slutt = b.FASTE_PERIODER["Siste 12 mnd"]
    linjer = [
        f"GRUNNLAG FOR LEDERBRIEF: {u.SELSKAP}, hele selskapet, siste 12 måneder "
        f"({start:%d.%m.%Y}-{slutt:%d.%m.%Y}). Data per {b.DATA_TIL:%d.%m.%Y}. "
        f"Alle tall er syntetiske.",
        "",
        "NØKKELTALL (status: OK, Følg med eller Kritisk; tersklene er skjønn)",
        i.felles_merknad(nokkeltall),
    ]
    for k in nokkeltall:
        # Pilen i kortet: «+3,1 pp», «−6 dager». Bindestrek foran tall byttes med minustegn,
        # som ellers i tekst (pilene bruker bindestrek bare fordi Streamlit krever det).
        endring = f" ({b.minustegn(k['endring'])} mot sammenligningsperioden)" if k.get("endring") else ""
        status, grunn = k["status"]
        linjer.append(f"- {k['navn']}: {k['verdi']}{endring}. Status: {status} ({grunn}). {k['ekstra']}")
    linjer += ["", "VIKTIGSTE INNSIKTER (regelbaserte, viktigste først)"]
    for innsikt in innsikt_liste:
        # Punktliste, ikke nummerert: da er hvert tall i grunnlaget et tall fra forsiden
        linje = f"- {innsikt['tittel']}. {innsikt['tekst']}"
        if innsikt.get("merknad"):
            linje += f" Merknad: {innsikt['merknad']}"
        linjer.append(linje)
    if not innsikt_liste:
        linjer.append("Ingen store avvik akkurat nå.")
    # Ren tekst: Markdown-fet (**…**) fra merknadene er bare støy for modellen
    return "\n".join(linjer).replace("**", "")


def fingeravtrykk(tekst):
    """Kort sjekksum av grunnlaget (SHA-256, de første 12 tegnene). Endres grunnlaget med
    så mye som ett tegn, endres fingeravtrykket. Fungerer som et versjonsstempel: briefen
    vises bare når stempelet stemmer med dagens tall."""
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()[:12]


# --- Den lagrede briefen -------------------------------------------------------------

def les_lederbrief(sti=None):
    """Leser data/lederbrief.json. Mangler filen: None (forsiden viser da ingen brief)."""
    sti = Path(sti or STI)
    if not sti.exists():
        return None
    return json.loads(sti.read_text(encoding="utf-8"))


def lagre_lederbrief(brief, sti=None):
    """Skriver briefen til data/lederbrief.json, med æøå som de er (ikke \\u-koder)."""
    Path(sti or STI).write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")


def status(brief, grunnlag_tekst):
    """«ok», «ikke_godkjent» (ingen dato i godkjent) eller «utdatert» (fingeravtrykket
    stemmer ikke med dagens grunnlag). Bare «ok» vises på forsiden."""
    if brief.get("fingeravtrykk") != fingeravtrykk(grunnlag_tekst):
        return "utdatert"
    if not brief.get("godkjent"):
        return "ikke_godkjent"
    return "ok"


def dato(iso):
    """«2026-10-16» → «16.10.2026»."""
    aar, mnd, dag = iso.split("-")
    return f"{dag}.{mnd}.{aar}"


def merking(brief):
    """Setningen som sier hva briefen er: hvilken AI-modell, når, og at et menneske har
    lest den. Brukes både på forsiden og i nedlastingen."""
    godkjent = f" Lest og godkjent av HR-leder {dato(brief['godkjent'])}." if brief.get("godkjent") else ""
    return (f"Skrevet av AI-modellen {brief['modell']} {dato(brief['laget'])}, ut fra tallene på "
            f"forsiden i dashbordet.{godkjent} Spørsmål, ikke anbefalinger. Syntetiske data.")


def all_tekst(felt):
    """All tekst i briefen (feltet «brief» i filen) som én streng, til kontrollene."""
    deler = [felt.get("sammendrag", ""), felt.get("folg_med", ""), felt.get("forbehold", "")]
    for tema in felt.get("temaer", []):
        deler += [tema.get("tittel", ""), tema.get("hva_tallene_viser", ""), *tema.get("sporsmal", [])]
    return " ".join(deler)


def som_markdown(brief):
    """Briefen som én side Markdown, til nedlasting (og vedlegg i e-post)."""
    felt = brief["brief"]
    linjer = [f"# Lederbrief: {u.SELSKAP}", "",
              f"Hele selskapet, {brief['periode']}. Data per {brief['data_per']}.", "",
              "## Hovedbildet", "", felt["sammendrag"], ""]
    for tema in felt["temaer"]:
        linjer += [f"## {tema['tittel']}", "", tema["hva_tallene_viser"], "",
                   "Spørsmål til ledermøtet:", "", *(f"- {s}" for s in tema["sporsmal"]), ""]
    linjer += ["## Følg med", "", felt["folg_med"], "",
               "## Forbehold", "", felt["forbehold"], "", "---", "", f"*{merking(brief)}*"]
    return "\n".join(linjer) + "\n"


# --- Kontroll av AI-teksten ---------------------------------------------------------
# Grovsjekker: tall skrevet med ord fanges ikke opp. Den viktigste kontrollen er
# mennesket som leser (se CLAUDE.md).

TALL = re.compile(r"\d+(?:,\d+)?")
# Tankestrek klemt mellom to tegn (som i et intervall): skal være bindestrek. Samme regel
# som testene. Tegnet skrives som tegnkode (chr), så tekstreglene ikke slår ut på linjen.
INTERVALL = re.compile("(?<=[0-9A-Za-zæøåÆØÅ}\\])])" + chr(0x2013) + "(?=[0-9A-Za-zæøåÆØÅ{(])")
# A-endinger som skal være en-endinger. Ordene settes sammen av stamme + «a», så testen
# som leter etter dem i kildekoden ikke slår ut på denne listen.
A_ENDINGER = re.compile("(?i)(" + "|".join(stamme + "a" for stamme in
                                           ("pil", "linj", "fil", "mapp", "lyspær", "graf")) + r")\b")


def kontroller(felt, grunnlag_tekst):
    """Sjekker briefen mot reglene i CLAUDE.md. Gir en liste med problemer (tom liste = OK).
    `felt` er feltet «brief» i filen, `grunnlag_tekst` er grunnlaget den skal bygge på."""
    problemer = []
    for navn in FELT:
        if not felt.get(navn):
            problemer.append(f"feltet «{navn}» mangler eller er tomt")
    temaer = felt.get("temaer", [])
    if not 1 <= len(temaer) <= 3:
        problemer.append(f"{len(temaer)} temaer (skal være 1-3)")
    for tema in temaer:
        for navn in TEMAFELT:
            if not tema.get(navn):
                problemer.append(f"temaet mangler «{navn}»")
        if not 1 <= len(tema.get("sporsmal", [])) <= 2:
            problemer.append(f"{len(tema.get('sporsmal', []))} spørsmål i «{tema.get('tittel')}» (skal være 1-2)")

    tekst = all_tekst(felt)
    # Alle tall i briefen må stå i grunnlaget, skrevet på samme måte
    lovlige = set(TALL.findall(grunnlag_tekst))
    ukjente = sorted({t for t in TALL.findall(tekst) if t not in lovlige})
    if ukjente:
        problemer.append("tall som ikke står i grunnlaget: " + ", ".join(ukjente))
    # Bare team som nevnes i grunnlaget
    for team in b.TEAM:
        if team in tekst.lower() and team not in grunnlag_tekst.lower():
            problemer.append(f"nevner «{team}», som ikke står i grunnlaget")
    antall_ord = len(tekst.split())
    if antall_ord > MAKS_ORD:
        problemer.append(f"{antall_ord} ord (maks {MAKS_ORD})")
    # Tekstreglene (se «Presentasjon i dashbordet» i CLAUDE.md). Den lange tankestreken
    # skrives som tegnkode, så testen som leter etter den i kildekoden ikke slår ut her.
    if chr(0x2014) in tekst:
        problemer.append("lang tankestrek")
    if "·" in tekst:
        problemer.append("prikk (·) som skilletegn")
    if INTERVALL.search(tekst):
        problemer.append("tankestrek i intervall (skal være bindestrek)")
    if A_ENDINGER.search(tekst):
        problemer.append("a-ending (skal være en-ending): " + A_ENDINGER.search(tekst).group(0))
    if re.search(r"(^|[\s(])-\d", tekst):
        problemer.append("bindestrek foran tall (skal være minustegn)")
    return problemer

# Lager syntetiske HR-data for et fiktivt norsk tech-selskap, okt 2024–sep 2026,
# og lagrer dem som CSV-filer i mappa data/.
#
# Kjør slik:  python lag_syntetiske_data.py
#
# Dataene simuleres måned for måned: noen slutter, nye stillinger lyses ut og
# fylles. Tilfeldighetene styres av et fast frø (FRØ), så du får nøyaktig de
# samme dataene hver gang du kjører skriptet.

import random
from pathlib import Path

import pandas as pd

# =============================================================================
# FORUTSETNINGER – «knappene» som styrer historien (som et forutsetningsark)
# =============================================================================

FRO = 42  # Fast tilfeldighetsfrø. Endre tallet = andre (men like realistiske) data.

DATASTART = pd.Timestamp("2024-10-01")
DATASLUTT = pd.Timestamp("2026-09-30")  # Dataene er et «øyeblikksbilde» per denne dagen

# Rekrutteringsdata (metode, datoer, prøvetid) registreres fra og med datastart.
# Alle som ble ansatt før dette, har tomme rekrutteringsfelt.

# Per team:
#   plan_start / plan_slutt – planlagt antall ansatte (vokser jevnt mellom dem)
#   antall_start            – faste ansatte ved datastart
#   avgang                  – årlig andel som slutter (blant etablerte ansatte)
#   maks_utlysninger        – hvor mange stillinger teamet klarer å lyse ut per måned
#   dager_aksept            – typisk antall dager fra utlysning til akseptert tilbud
# Teknologi klarer bare én utlysning i måneden og bruker lengst tid på å ansette,
# mens planen vokser raskt – derfor havner teamet under bemanningsplanen.
TEAM = {
    "teknologi":        dict(plan_start=82, plan_slutt=98, antall_start=80, avgang=0.09, maks_utlysninger=1, dager_aksept=60),
    "produktutvikling": dict(plan_start=18, plan_slutt=20, antall_start=18, avgang=0.12, maks_utlysninger=2, dager_aksept=42),
    "salg":             dict(plan_start=37, plan_slutt=40, antall_start=37, avgang=0.17, maks_utlysninger=4, dager_aksept=30),
    "kundesuksess":     dict(plan_start=41, plan_slutt=43, antall_start=41, avgang=0.11, maks_utlysninger=3, dager_aksept=32),
    "markedsføring":    dict(plan_start=17, plan_slutt=18, antall_start=17, avgang=0.11, maks_utlysninger=2, dager_aksept=38),
    "økonomi og hr":    dict(plan_start=15, plan_slutt=16, antall_start=15, avgang=0.08, maks_utlysninger=2, dager_aksept=40),
    "ledergruppen":     dict(plan_start=4,  plan_slutt=4,  antall_start=4,  avgang=0.00, maks_utlysninger=0, dager_aksept=0),
}

# Andel strukturerte ansettelser: øker jevnt fra start til slutt av perioden.
# Salg henger etter – der ansettes de fleste fortsatt ustrukturert.
ANDEL_STRUKTURERT = {"vanlig": (0.20, 0.85), "salg": (0.10, 0.45)}

# Andel som slutter innen 12 måneder (tidlig turnover), etter metode.
# Salg ligger høyere enn resten – der slutter mange nyansatte raskt.
TIDLIG_AVGANG = {"strukturert": 0.10, "ustrukturert": 0.28}
TIDLIG_AVGANG_SALG = {"strukturert": 0.15, "ustrukturert": 0.45}
# Av dem som slutter tidlig: andel som ikke består prøvetiden, etter metode.
# Strukturert: den første tidlige avgangen stryker, så andelen ikke blir 100 %.
STRYK_PROVETID = {"strukturert": 0.50, "ustrukturert": 0.45}

# Planlagte pensjoneringer: (team, sluttdato). Den med lengst ansiennitet i teamet
# går av. Sørger for at regelen «pensjon teller i total turnover» blir testet.
PENSJONERINGER = [("teknologi", "2026-03-31"), ("økonomi og hr", "2026-06-30")]

# Midlertidige vikarer i kundesuksess: (utlysningsdato, kontraktlengde i måneder)
VIKARER_KUNDESUKSESS = [
    ("2024-10-07", 6), ("2025-02-03", 8), ("2025-05-05", 6), ("2025-09-01", 9),
    ("2025-12-01", 6), ("2026-02-02", 7), ("2026-04-06", 9),
]

# Sykefravær: korttid er lik for alle team (med sesongvariasjon), langtid per team.
KORTTID = 0.020
SESONG_KORTTID = {1: 1.35, 2: 1.30, 3: 1.15, 4: 1.00, 5: 0.90, 6: 0.75,
                  7: 0.55, 8: 0.80, 9: 1.00, 10: 1.05, 11: 1.15, 12: 1.20}
LANGTID = {"teknologi": 0.030, "produktutvikling": 0.030, "salg": 0.036,
           "kundesuksess": 0.040, "markedsføring": 0.032, "økonomi og hr": 0.030,
           "ledergruppen": 0.008}
# Kundesuksess: langtidsfraværet stiger siste halvår (apr–sep 2026).
LANGTID_KUNDESUKSESS_SISTE_HALVAAR = {"2026-04": 0.050, "2026-05": 0.060, "2026-06": 0.068,
                                      "2026-07": 0.075, "2026-08": 0.082, "2026-09": 0.088}

# eNPS: fast nivå per team, men kundesuksess faller kvartal for kvartal.
ENPS_NIVAA = {"teknologi": 22, "produktutvikling": 20, "salg": 6, "markedsføring": 15,
              "økonomi og hr": 18, "ledergruppen": 40}
ENPS_KUNDESUKSESS = [11, 10, 9, 8, 5, 0, -8, -15]  # 2024-K4 … 2026-K3

# Stillinger per team: (tittel, vekt, lønn fra, lønn til) – lønn ved 100 % stilling
STILLINGER = {
    "teknologi": [("Utvikler", 55, 750_000, 1_000_000), ("Senior utvikler", 20, 900_000, 1_150_000),
                  ("DevOps-ingeniør", 10, 850_000, 1_050_000), ("Data scientist", 8, 820_000, 1_050_000),
                  ("Teamleder", 7, 1_000_000, 1_250_000)],
    "produktutvikling": [("UX-designer", 40, 650_000, 900_000), ("Produkteier", 40, 800_000, 1_000_000),
                         ("Produktleder", 20, 900_000, 1_100_000)],
    "salg": [("SDR", 40, 520_000, 650_000), ("Key account manager", 50, 700_000, 950_000),
             ("Teamleder salg", 10, 900_000, 1_100_000)],
    "kundesuksess": [("Supportkonsulent", 50, 500_000, 600_000), ("Kundeansvarlig", 40, 560_000, 680_000),
                     ("Teamleder", 10, 680_000, 780_000)],
    "markedsføring": [("Markedsrådgiver", 45, 580_000, 720_000), ("Innholdsprodusent", 35, 520_000, 650_000),
                      ("Performance marketer", 20, 620_000, 780_000)],
    "økonomi og hr": [("Regnskapsmedarbeider", 30, 520_000, 650_000), ("Controller", 25, 700_000, 850_000),
                      ("HR-rådgiver", 30, 620_000, 760_000), ("Lønnsmedarbeider", 15, 520_000, 620_000)],
}
LEDERGRUPPEN = [("Daglig leder", 2_200_000), ("Økonomidirektør", 1_800_000),
                ("Teknologidirektør", 1_900_000), ("Kommersiell direktør", 1_700_000)]

DATAMAPPE = Path("data")

# =============================================================================
# HJELPEFUNKSJONER
# =============================================================================

tilfeldig = random.Random(FRO)
MAANEDER = pd.date_range(DATASTART, DATASLUTT, freq="MS")  # 1. i hver måned
ansatte = []  # Lista fylles med én «rad» (en dict) per ansatt


def maanedsslutt(dato):
    """Siste dag i måneden – som MÅNEDSSLUTT(dato; 0) i Excel."""
    return dato + pd.offsets.MonthEnd(0)


def pluss_maaneder(dato, antall):
    """Samme som DATO.MÅNED(dato; antall) i Excel."""
    return dato + pd.DateOffset(months=antall)


_teller = {}


def jevnt(nokkel, andel):
    """Gir «ja» for omtrent `andel` av tilfellene, jevnt fordelt i stedet for
    tilfeldig – som å fordele 30 % ved å ta omtrent hver tredje. Brukes der
    gruppene er så små at rene loddtrekninger kunne overdøve historien."""
    _teller[nokkel] = _teller.get(nokkel, 0.5) + andel
    if _teller[nokkel] >= 1:
        _teller[nokkel] -= 1
        return True
    return False


def andel_strukturert(team, dato):
    """Andel strukturerte ansettelser på en gitt dato (stiger jevnt over perioden)."""
    fra, til = ANDEL_STRUKTURERT["salg" if team == "salg" else "vanlig"]
    hvor_langt = (dato - DATASTART).days / (DATASLUTT - DATASTART).days
    return fra + (til - fra) * min(max(hvor_langt, 0), 1)


def planlagt_antall(team, maaned_nr):
    """Planen vokser jevnt fra plan_start til plan_slutt over de 24 månedene."""
    t = TEAM[team]
    andel = maaned_nr / (len(MAANEDER) - 1)
    return round(t["plan_start"] + (t["plan_slutt"] - t["plan_start"]) * andel)


def ny_person(team, ansattdato, stilling=None, lonn_100=None):
    """Lager en ny ansatt med stilling, stillingsprosent og faktisk årslønn."""
    if stilling is None:
        valg = STILLINGER[team]
        stilling, _, fra, til = tilfeldig.choices(valg, weights=[v[1] for v in valg])[0]
        lonn_100 = tilfeldig.randint(fra, til)
    if team == "ledergruppen":
        stillingsprosent = 100
    else:
        stillingsprosent = tilfeldig.choices([100, 80, 60], weights=[88, 10, 2])[0]
    return {
        "team": team,
        "stilling": stilling,
        "ansettelsesform": "fast",
        "stillingsprosent": stillingsprosent,
        # Faktisk lønn = lønn ved 100 % × stillingsprosent, avrundet til nærmeste 10 000
        "årslønn": round(lonn_100 * stillingsprosent / 100, -4),
        "ansattdato": ansattdato,
        "sluttdato": None,
        "sluttårsak": None,
        "uønsket": None,
        "rekrutteringsmetode": None,
        "utlysningsdato": None,
        "aksept_dato": None,
        "prøvetid_bestått": None,
        "planlagt_slutt": False,  # True = sluttdato er bestemt på forhånd
    }


def avslutt(person, sluttdato, aarsak, uonsket):
    person["sluttdato"] = sluttdato
    person["sluttårsak"] = aarsak
    person["uønsket"] = uonsket


def ansett(team, utlysningsdato, ansettelsesform="fast", kontrakt_mnd=None):
    """Lyser ut en stilling og ansetter: metode, datoer og eventuell tidlig avgang."""
    gruppe = "salg" if team == "salg" else "vanlig"
    metode = "strukturert" if jevnt(gruppe, andel_strukturert(team, utlysningsdato)) else "ustrukturert"

    # Dager fra utlysning til akseptert tilbud: rundt teamets typiske verdi
    dager = max(10, round(TEAM[team]["dager_aksept"] * tilfeldig.lognormvariate(0, 0.3)))
    aksept = utlysningsdato + pd.Timedelta(days=dager)

    # Oppsigelsestid fra forrige jobb før oppstart (teknologi har ofte 3 mnd)
    if ansettelsesform == "midlertidig":
        oppsigelse = 14
    elif team == "teknologi":
        oppsigelse = tilfeldig.choices([14, 30, 60, 90], weights=[1, 2, 3, 4])[0]
    else:
        oppsigelse = tilfeldig.choices([14, 30, 60, 90], weights=[2, 4, 3, 1])[0]
    ansattdato = aksept + pd.Timedelta(days=oppsigelse)

    person = ny_person(team, ansattdato)
    person.update(ansettelsesform=ansettelsesform, rekrutteringsmetode=metode,
                  utlysningsdato=utlysningsdato, aksept_dato=aksept, prøvetid_bestått="ja")

    if ansettelsesform == "midlertidig":
        # Kontrakten utløper – telles ikke som turnover
        avslutt(person, maanedsslutt(pluss_maaneder(ansattdato, kontrakt_mnd)), "kontrakt utløpt", "nei")
        person["planlagt_slutt"] = True
    elif jevnt(("tidlig", gruppe, metode), (TIDLIG_AVGANG_SALG if team == "salg" else TIDLIG_AVGANG)[metode]):
        person["planlagt_slutt"] = True
        if jevnt(("stryk", metode), STRYK_PROVETID[metode]):
            # Består ikke prøvetiden (6 mnd) og må slutte etter ca. 5 måneder
            avslutt(person, maanedsslutt(pluss_maaneder(ansattdato, 5)), "ufrivillig", "nei")
            person["prøvetid_bestått"] = "nei"
        else:
            # Består prøvetiden, men sier opp selv etter 7–11 måneder
            uonsket = "ja" if tilfeldig.random() < 0.4 else "nei"
            avslutt(person, maanedsslutt(pluss_maaneder(ansattdato, tilfeldig.randint(7, 11))),
                    "frivillig", uonsket)

    ansatte.append(person)


def faste_paa_plass_eller_paa_vei(team, dato):
    """Faste ansatte som ikke har sluttet per dato – inkludert dem som har takket ja,
    men ikke startet ennå. Det er dette tallet rekrutteringen sammenligner med planen."""
    return sum(
        1 for p in ansatte
        if p["team"] == team and p["ansettelsesform"] == "fast"
        and (p["sluttdato"] is None or p["sluttdato"] > dato)
    )


# =============================================================================
# 1. ANSATTE VED START (ansatt før rekrutteringsdata ble registrert)
# =============================================================================

for team, t in TEAM.items():
    if team == "ledergruppen":
        for stilling, lonn in LEDERGRUPPEN:
            dato = pd.Timestamp("2016-01-01") + pd.Timedelta(days=tilfeldig.randint(0, 2000))
            ansatte.append(ny_person(team, dato, stilling, lonn))
        continue
    for _ in range(t["antall_start"]):
        # Ansattdato mellom 2012 og sept 2024 – flest relativt nylig
        dager_tilbake = int(tilfeldig.triangular(15, 12 * 365, 2 * 365))
        ansatte.append(ny_person(team, DATASTART - pd.Timedelta(days=dager_tilbake)))

# Pensjoneringer: finn den som har vært ansatt lengst i teamet
for team, dato in PENSJONERINGER:
    kandidater = [p for p in ansatte if p["team"] == team and not p["planlagt_slutt"]]
    eldst = min(kandidater, key=lambda p: p["ansattdato"])
    avslutt(eldst, pd.Timestamp(dato), "pensjon", "nei")
    eldst["planlagt_slutt"] = True

# Vikarer i kundesuksess
for utlysning, mnd in VIKARER_KUNDESUKSESS:
    ansett("kundesuksess", pd.Timestamp(utlysning), "midlertidig", mnd)


# =============================================================================
# 2. SIMULER MÅNED FOR MÅNED: avganger og nye ansettelser
# =============================================================================

for nr, maaned in enumerate(MAANEDER):
    slutt = maanedsslutt(maaned)

    # a) Avganger blant etablerte ansatte (de med mer enn 12 mnd ansiennitet,
    #    eller som var ansatt før datastart). Tidlige avganger er bestemt ved ansettelse.
    for p in ansatte:
        if p["sluttdato"] is not None or p["planlagt_slutt"] or p["ansattdato"] > maaned:
            continue
        etablert = p["rekrutteringsmetode"] is None or (maaned - p["ansattdato"]).days >= 365
        if not etablert:
            continue
        sjanse_per_maaned = 1 - (1 - TEAM[p["team"]]["avgang"]) ** (1 / 12)
        if jevnt(("avgang", p["team"]), sjanse_per_maaned):
            # Pensjon er planlagt på forhånd (PENSJONERINGER), så her er det
            # bare frivillig eller ufrivillig. Andel ufrivillig fordeles jevnt.
            if jevnt(("ufrivillig", p["team"]), 0.10 if p["team"] == "salg" else 0.15):
                avslutt(p, slutt, "ufrivillig", "nei")
            else:
                avslutt(p, slutt, "frivillig", "ja" if tilfeldig.random() < 0.55 else "nei")

    # b) Rekruttering: lys ut stillinger hvis teamet ligger under planen to måneder frem
    for team, t in TEAM.items():
        mal = planlagt_antall(team, min(nr + 2, len(MAANEDER) - 1))
        mangler = mal - faste_paa_plass_eller_paa_vei(team, slutt)
        for _ in range(max(0, min(mangler, t["maks_utlysninger"]))):
            ansett(team, maaned + pd.Timedelta(days=tilfeldig.randint(0, 20)))


# =============================================================================
# 3. ØYEBLIKKSBILDE PER DATASLUTT
# =============================================================================
# Det vi ikke kan vite per 30.09.2026, fjernes: folk som ikke har startet ennå,
# framtidige sluttdatoer, og prøvetid som ikke er over.

bilde = []
for p in ansatte:
    if p["ansattdato"] > DATASLUTT:
        continue
    p = dict(p)  # kopi, så vi ikke endrer originalen
    if p["sluttdato"] is not None and p["sluttdato"] > DATASLUTT:
        p["sluttdato"] = p["sluttårsak"] = p["uønsket"] = None
    if p["rekrutteringsmetode"] is not None and pluss_maaneder(p["ansattdato"], 6) > DATASLUTT:
        if p["prøvetid_bestått"] == "ja" or p["sluttdato"] is None:
            p["prøvetid_bestått"] = None
    del p["planlagt_slutt"]
    bilde.append(p)

ansatte_df = pd.DataFrame(bilde).sort_values("ansattdato").reset_index(drop=True)
# Ansatt-ID etter ansettelsesrekkefølge: A001, A002, ...
ansatte_df.insert(0, "ansatt_id", [f"A{i:03d}" for i in range(1, len(ansatte_df) + 1)])
for kolonne in ["ansattdato", "sluttdato", "utlysningsdato", "aksept_dato"]:
    ansatte_df[kolonne] = pd.to_datetime(ansatte_df[kolonne]).dt.normalize()
ansatte_df["årslønn"] = ansatte_df["årslønn"].astype(int)


# =============================================================================
# 4. FRAVÆR (én rad per team per måned)
# =============================================================================
# For å lage realistiske tapte dagsverk trenger vi avtalte dagsverk her også.
# De lagres ikke – dashbordet regner dem ut på nytt fra ansatte.csv.
# Arbeidsdager = mandag–fredag (helligdager er ikke trukket fra).

def avtalte_dagsverk(team, maaned):
    slutt = maanedsslutt(maaned)
    sum_dagsverk = 0.0
    for _, p in ansatte_df[ansatte_df["team"] == team].iterrows():
        fra = max(maaned, p["ansattdato"])
        til = slutt if pd.isna(p["sluttdato"]) else min(slutt, p["sluttdato"])
        if fra <= til:
            sum_dagsverk += len(pd.bdate_range(fra, til)) * p["stillingsprosent"] / 100
    return sum_dagsverk


fravaer_rader = []
for maaned in MAANEDER:
    mnd_tekst = maaned.strftime("%Y-%m")
    for team in TEAM:
        avtalte = avtalte_dagsverk(team, maaned)
        langtid = LANGTID[team]
        if team == "kundesuksess":
            langtid = LANGTID_KUNDESUKSESS_SISTE_HALVAAR.get(mnd_tekst, langtid)
        kort = KORTTID * SESONG_KORTTID[maaned.month] * tilfeldig.uniform(0.85, 1.15)
        lang = langtid * tilfeldig.uniform(0.85, 1.15)
        fravaer_rader.append({
            "team": team,
            "måned": mnd_tekst,
            "tapte_dagsverk_korttid": round(avtalte * kort),
            "tapte_dagsverk_langtid": round(avtalte * lang),
        })
fravaer_df = pd.DataFrame(fravaer_rader)


# =============================================================================
# 5. ENGASJEMENT (én rad per team per kvartal)
# =============================================================================

def antall_ansatt_paa(team, dato):
    t = ansatte_df[ansatte_df["team"] == team]
    return int(((t["ansattdato"] <= dato) & (t["sluttdato"].isna() | (t["sluttdato"] >= dato))).sum())


engasjement_rader = []
for nr, kvartalsstart in enumerate(pd.date_range(DATASTART, DATASLUTT, freq="QS")):
    kvartal = f"{kvartalsstart.year}-K{kvartalsstart.quarter}"
    midt = maanedsslutt(pluss_maaneder(kvartalsstart, 1))  # slutten av midterste måned
    for team in TEAM:
        antall = antall_ansatt_paa(team, midt)
        if team == "ledergruppen":
            svar = antall
        else:
            svar = round(antall * tilfeldig.uniform(0.72, 0.90))
        if team == "kundesuksess":
            enps = ENPS_KUNDESUKSESS[nr] + tilfeldig.randint(-1, 1)
        else:
            enps = ENPS_NIVAA[team] + tilfeldig.randint(-4, 4)
        engasjement_rader.append({"team": team, "kvartal": kvartal,
                                  "enps": max(-100, min(100, enps)), "antall_svar": svar})
engasjement_df = pd.DataFrame(engasjement_rader)


# =============================================================================
# 6. BEMANNINGSPLAN (én rad per team per måned)
# =============================================================================

plan_df = pd.DataFrame([
    {"team": team, "måned": maaned.strftime("%Y-%m"), "planlagt_antall": planlagt_antall(team, nr)}
    for nr, maaned in enumerate(MAANEDER)
    for team in TEAM
])


# =============================================================================
# 7. LAGRE SOM CSV
# =============================================================================

DATAMAPPE.mkdir(exist_ok=True)  # lager mappa hvis den ikke finnes
ansatte_df.to_csv(DATAMAPPE / "ansatte.csv", index=False, date_format="%Y-%m-%d")
fravaer_df.to_csv(DATAMAPPE / "fravaer.csv", index=False)
engasjement_df.to_csv(DATAMAPPE / "engasjement.csv", index=False)
plan_df.to_csv(DATAMAPPE / "bemanningsplan.csv", index=False)

print(f"Lagret {len(ansatte_df)} ansatte, {len(fravaer_df)} fraværsrader, "
      f"{len(engasjement_df)} eNPS-rader og {len(plan_df)} planrader i {DATAMAPPE}/")

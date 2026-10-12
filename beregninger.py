# Formler for dashbordet – som et eget beregningsark i Excel.
# Sidene i dashbordet henter tallene herfra, så hver formel finnes bare ett sted.
# Alle definisjoner følger CLAUDE.md.

from pathlib import Path

import pandas as pd

# Mappa med CSV-filene (ligger ved siden av denne fila)
DATAMAPPE = Path(__file__).parent / "data"

# Første og siste dag dataene dekker
DATA_FRA = pd.Timestamp("2024-10-01")
DATA_TIL = pd.Timestamp("2026-09-30")

# Avganger som teller i turnover: stillingen må erstattes (se CLAUDE.md)
TELLER_I_TURNOVER = ["frivillig", "ufrivillig", "pensjon"]

# Femregelen: grupper med færre enn 5 skjules
MIN_GRUPPE = 5

# Merking som vises øverst på alle sider (se «Presentasjon» i CLAUDE.md)
SYNTETISK_MERKNAD = (
    "**Syntetiske data.** Alle tall i dette dashbordet er oppdiktet og konstruert "
    "for å illustrere metodikk. De er ikke ekte funn om noe selskap."
)

TEAM = ["teknologi", "produktutvikling", "salg", "kundesuksess",
        "markedsføring", "økonomi og hr", "ledergruppen"]


# --- Lese data ----------------------------------------------------------------

def les_ansatte():
    """Leser ansatte.csv og gjør datokolonnene om til ekte datoer."""
    return pd.read_csv(
        DATAMAPPE / "ansatte.csv",
        parse_dates=["ansattdato", "sluttdato", "utlysningsdato", "aksept_dato"],
    )


# --- Datoer og perioder -------------------------------------------------------

def maanedsslutt(dato):
    """Siste dag i måneden – som MÅNEDSSLUTT(dato; 0) i Excel."""
    return dato + pd.offsets.MonthEnd(0)


def maanedsslutter(start, slutt):
    """Alle månedsslutter i perioden, f.eks. 31.10, 30.11 … 30.09."""
    return pd.date_range(start, slutt, freq="ME")


def forrige_periode(start, slutt):
    """Perioden med samme lengde rett før. 12 mnd fra okt 2025 → 12 mnd fra okt 2024."""
    antall = len(maanedsslutter(start, slutt))
    forrige_start = start - pd.DateOffset(months=antall)
    forrige_slutt = start - pd.Timedelta(days=1)
    return forrige_start, forrige_slutt


# --- Antall ansatte -----------------------------------------------------------

def antall_ansatt_paa(ansatte, dato):
    """Hvor mange var ansatt denne dagen? Startet senest i dag, og har ikke sluttet
    før i dag (sluttdato er siste arbeidsdag). Som ANTALL.HVIS.SETT med to krav."""
    har_startet = ansatte["ansattdato"] <= dato
    ikke_sluttet = ansatte["sluttdato"].isna() | (ansatte["sluttdato"] >= dato)
    return int((har_startet & ikke_sluttet).sum())


def snitt_ansatte(ansatte, start, slutt):
    """Gjennomsnitt av antall ansatte ved hver månedsslutt i perioden."""
    dager = maanedsslutter(start, slutt)
    return sum(antall_ansatt_paa(ansatte, dag) for dag in dager) / len(dager)


# --- Turnover -----------------------------------------------------------------

def sluttet_i_perioden(ansatte, start, slutt):
    """Alle som sluttet i perioden, uansett sluttårsak (som et autofilter på sluttdato)."""
    return ansatte[(ansatte["sluttdato"] >= start) & (ansatte["sluttdato"] <= slutt)]


def turnover(ansatte, start, slutt):
    """Regner ut alle turnovertall for en gruppe ansatte og en periode.
    Svaret er en «oppslagsliste» (dict): navn → verdi."""
    sluttet = sluttet_i_perioden(ansatte, start, slutt)
    teller = sluttet[sluttet["sluttårsak"].isin(TELLER_I_TURNOVER)]
    frivillig = teller[teller["sluttårsak"] == "frivillig"]
    uonsket = frivillig[frivillig["uønsket"] == "ja"]

    snitt = snitt_ansatte(ansatte, start, slutt)
    # Annualisering: gang opp til helår hvis perioden ikke er 12 måneder
    til_helaar = 12 / len(maanedsslutter(start, slutt))

    def rate(antall):
        return antall / snitt * til_helaar if snitt > 0 else None

    return {
        "snitt_ansatte": snitt,
        "avganger": len(teller),
        "frivillig": len(frivillig),
        "ufrivillig": int((teller["sluttårsak"] == "ufrivillig").sum()),
        "pensjon": int((teller["sluttårsak"] == "pensjon").sum()),
        "uønsket": len(uonsket),
        "kontrakt_utløpt": int((sluttet["sluttårsak"] == "kontrakt utløpt").sum()),
        "total_rate": rate(len(teller)),
        "frivillig_rate": rate(len(frivillig)),
        "uønsket_rate": rate(len(uonsket)),
        "lønn_uønsket": int(uonsket["årslønn"].sum()),
    }


def turnover_per_team(ansatte, start, slutt, team_liste=TEAM):
    """Én rad per team – som en pivottabell. Femregelen er bygd inn:
    - team med færre enn 5 ansatte (i snitt): alt skjules
    - fordeling på sluttårsak og uønsket: bare når teamet har minst 5 avganger
    Skjulte tall settes til None (tom celle)."""
    rader = []
    for team in team_liste:
        t = turnover(ansatte[ansatte["team"] == team], start, slutt)
        rad = {"team": team, **t}
        if t["snitt_ansatte"] < MIN_GRUPPE:
            for felt in t:
                rad[felt] = None
            rad["skjult"] = "lite team"
        elif t["avganger"] < MIN_GRUPPE:
            for felt in ["frivillig", "ufrivillig", "pensjon", "uønsket", "kontrakt_utløpt",
                         "frivillig_rate", "uønsket_rate"]:
                rad[felt] = None
            rad["skjult"] = "få avganger"
        else:
            rad["skjult"] = ""
        rad.pop("lønn_uønsket")  # Lønn vises aldri per team
        rader.append(rad)
    return pd.DataFrame(rader)


def avganger_per_maaned(ansatte, start, slutt):
    """Avganger som teller i turnover, per måned, delt i uønsket og øvrige.
    Alle måneder i perioden er med, også de uten avganger (0)."""
    sluttet = sluttet_i_perioden(ansatte, start, slutt)
    teller = sluttet[sluttet["sluttårsak"].isin(TELLER_I_TURNOVER)]
    er_uonsket = (teller["sluttårsak"] == "frivillig") & (teller["uønsket"] == "ja")
    maaned = teller["sluttdato"].dt.strftime("%Y-%m")

    alle_maaneder = [d.strftime("%Y-%m") for d in maanedsslutter(start, slutt)]
    tabell = pd.DataFrame({
        "Uønsket": er_uonsket.groupby(maaned).sum(),
        "Øvrige": (~er_uonsket).groupby(maaned).sum(),
    })
    # reindex = sørg for at alle måneder er med, tomme fylles med 0
    return tabell.reindex(alle_maaneder, fill_value=0).astype(int)


# --- Formatering (norsk tallformat) -------------------------------------------

def prosent(andel, desimaler=1):
    """0.143 → «14,3 %». Tom verdi → «–»."""
    if andel is None or pd.isna(andel):
        return "–"
    return f"{andel * 100:.{desimaler}f} %".replace(".", ",")


def prosent_med_n(teller, nevner):
    """Prosent med n, for små grupper: «12,5 % (1 av 8)»."""
    if not nevner:
        return "–"
    return f"{prosent(teller / nevner)} ({teller} av {nevner})"


def endring_pp(ny, gammel):
    """Endring i prosentpoeng som tekst: «+3,1 pp», «−0,4 pp» eller «±0,0 pp»
    når endringen rundes av til null."""
    pp = round((ny - gammel) * 100, 1)
    if pp == 0:
        return "±0,0 pp"
    return f"{pp:+.1f} pp".replace(".", ",")


def pilfarge(endring_tekst, hoyere_er_bedre=False):
    """Farge på pila i KPI-kort. Vanligvis er økning dårlig (rød), f.eks. turnover.
    Med hoyere_er_bedre=True er økning bra (grønn). Ingen farge når endringen er null."""
    if endring_tekst and endring_tekst.startswith("±"):
        return "off"
    return "normal" if hoyere_er_bedre else "inverse"


def kroner(belop):
    """2700000 → «2 700 000 kr»."""
    return f"{belop:,.0f} kr".replace(",", " ")


# --- Sykefravær ---------------------------------------------------------------

# Benchmark: landssnitt for sykefravær 2025 (kilde: NAV)
SYKEFRAVAER_LANDSSNITT = 0.0657
SYKEFRAVAER_KILDE = "NAV, årsnotat sykefravær 2025"
SYKEFRAVAER_KILDE_URL = (
    "https://www.nav.no/_/attachment/inline/93423200-87fc-4941-ad03-b763066da97e:b1217b72b4bebb26ac77729528f034ab57969675/%C3%85rsnotat%20sykefrav%C3%A6r%20%C3%A5ret%202025.pdf"
)


def les_fravaer():
    """Leser fravaer.csv: tapte dagsverk per team og måned."""
    return pd.read_csv(DATAMAPPE / "fravaer.csv")


def avtalte_dagsverk(ansatte):
    """Avtalte dagsverk per team og måned, regnet ut fra ansatte (se CLAUDE.md):
    arbeidsdager (mandag–fredag) mens personen var ansatt × stillingsprosent.
    Helligdager og ferie er ikke trukket fra."""
    rader = []
    for maaned_start in pd.date_range(DATA_FRA, DATA_TIL, freq="MS"):
        maaned_slutt = maanedsslutt(maaned_start)
        for _, p in ansatte.iterrows():  # én ansatt om gangen, som å gå nedover rader
            fra = max(maaned_start, p["ansattdato"])
            til = maaned_slutt if pd.isna(p["sluttdato"]) else min(maaned_slutt, p["sluttdato"])
            if fra <= til:  # var ansatt minst én dag denne måneden
                arbeidsdager = len(pd.bdate_range(fra, til))  # bdate = hverdager
                rader.append({
                    "team": p["team"],
                    "måned": maaned_start.strftime("%Y-%m"),
                    "avtalte_dagsverk": arbeidsdager * p["stillingsprosent"] / 100,
                })
    # Summer per team og måned – som en pivottabell
    return pd.DataFrame(rader).groupby(["team", "måned"], as_index=False)["avtalte_dagsverk"].sum()


def fravaer_med_avtalte(ansatte, fravaer):
    """Legger avtalte dagsverk inn ved siden av tapte dagsverk.
    merge = slå opp på team og måned, som XOPPSLAG med to kriterier."""
    return fravaer.merge(avtalte_dagsverk(ansatte), on=["team", "måned"], how="left")


def samme_periode_i_fjor(start, slutt):
    """Samme måneder ett år tidligere (sykefravær varierer med årstiden)."""
    return start - pd.DateOffset(years=1), maanedsslutt(slutt - pd.DateOffset(years=1))


def fravaer_i_perioden(fravaer, start, slutt):
    """Filtrer til måneder i perioden. «2025-10» som tekst kan sammenlignes direkte."""
    return fravaer[(fravaer["måned"] >= f"{start:%Y-%m}") & (fravaer["måned"] <= f"{slutt:%Y-%m}")]


def sykefravaer(fravaer, start, slutt):
    """Sykefravær for perioden: tapte dagsverk / avtalte dagsverk."""
    f = fravaer_i_perioden(fravaer, start, slutt)
    avtalte = f["avtalte_dagsverk"].sum()
    kort = f["tapte_dagsverk_korttid"].sum()
    lang = f["tapte_dagsverk_langtid"].sum()
    if avtalte == 0:
        return None
    return {
        "avtalte": avtalte,
        "total_rate": (kort + lang) / avtalte,
        "korttid_rate": kort / avtalte,
        "langtid_rate": lang / avtalte,
    }


def sykefravaer_per_maaned(fravaer, start, slutt):
    """Sykefravær per måned i prosent, delt i korttid og langtid."""
    f = fravaer_i_perioden(fravaer, start, slutt)
    per_mnd = f.groupby("måned")[["tapte_dagsverk_korttid", "tapte_dagsverk_langtid",
                                  "avtalte_dagsverk"]].sum()
    return pd.DataFrame({
        "Korttid": per_mnd["tapte_dagsverk_korttid"] / per_mnd["avtalte_dagsverk"] * 100,
        "Langtid": per_mnd["tapte_dagsverk_langtid"] / per_mnd["avtalte_dagsverk"] * 100,
    })


def sykefravaer_per_team(ansatte, fravaer, start, slutt, team_liste=TEAM):
    """Én rad per team, med samme periode i fjor til sammenligning.
    Femregelen: team med færre enn 5 ansatte (snitt i perioden) skjules (None)."""
    fjor_start, fjor_slutt = samme_periode_i_fjor(start, slutt)
    har_fjor = fjor_start >= DATA_FRA
    rader = []
    for team in team_liste:
        snitt = snitt_ansatte(ansatte[ansatte["team"] == team], start, slutt)
        f_team = fravaer[fravaer["team"] == team]
        if snitt < MIN_GRUPPE:
            rader.append({"team": team, "snitt_ansatte": None, "skjult": True})
            continue
        naa = sykefravaer(f_team, start, slutt)
        fjor = sykefravaer(f_team, fjor_start, fjor_slutt) if har_fjor else None
        rader.append({
            "team": team,
            "snitt_ansatte": snitt,
            "total_rate": naa["total_rate"],
            "korttid_rate": naa["korttid_rate"],
            "langtid_rate": naa["langtid_rate"],
            "endring_pp": (naa["total_rate"] - fjor["total_rate"]) * 100 if fjor else None,
            "skjult": False,
        })
    return pd.DataFrame(rader)


# --- Rekruttering ---------------------------------------------------------------

# Rekrutteringsdata (metode, datoer, prøvetid) er registrert fra og med denne datoen
REKRUTTERING_FRA = DATA_FRA

KVALITET_MERKNAD = (
    "**Sammenheng, ikke nødvendigvis årsak.** Utvalget er lite, og strukturert "
    "rekruttering kan ha blitt brukt på andre typer stillinger."
)


def ansettelser_i_perioden(ansatte, start, slutt):
    """Alle med registrerte rekrutteringsdata som startet i perioden (alle
    ansettelsesformer), med en ny kolonne: dager fra utlysning til aksept."""
    a = ansatte[
        ansatte["rekrutteringsmetode"].notna()
        & (ansatte["ansattdato"] >= start) & (ansatte["ansattdato"] <= slutt)
    ].copy()  # .copy() = egen kopi, så vi kan legge til en kolonne trygt
    a["dager_til_ansettelse"] = (a["aksept_dato"] - a["utlysningsdato"]).dt.days
    return a


def rekruttering(ansatte, start, slutt):
    """Nøkkeltall for ansettelser i perioden."""
    a = ansettelser_i_perioden(ansatte, start, slutt)
    if len(a) == 0:
        return {"antall": 0, "median_dager": None, "andel_strukturert": None, "strukturert": 0}
    strukturert = int((a["rekrutteringsmetode"] == "strukturert").sum())
    return {
        "antall": len(a),
        "median_dager": a["dager_til_ansettelse"].median(),
        "andel_strukturert": strukturert / len(a),
        "strukturert": strukturert,
    }


def tid_til_ansettelse_per_team(ansatte, start, slutt, team_liste=TEAM):
    """Median dager fra utlysning til aksept per team, med antall ansettelser (n)."""
    a = ansettelser_i_perioden(ansatte, start, slutt)
    rader = []
    for team in team_liste:
        t = a[a["team"] == team]
        rader.append({"team": team, "antall": len(t),
                      "median_dager": t["dager_til_ansettelse"].median() if len(t) else None})
    return pd.DataFrame(rader)


def strukturert_per_kvartal(ansatte, start, slutt):
    """Andel strukturerte ansettelser per kvartal, med antall ansettelser (n)."""
    a = ansettelser_i_perioden(ansatte, start, slutt)
    kvartal = a["ansattdato"].dt.year.astype(str) + "-K" + a["ansattdato"].dt.quarter.astype(str)
    er_strukturert = a["rekrutteringsmetode"] == "strukturert"
    tabell = pd.DataFrame({
        "antall": er_strukturert.groupby(kvartal).size(),
        "strukturert": er_strukturert.groupby(kvartal).sum(),
    })
    tabell["andel"] = tabell["strukturert"] / tabell["antall"]
    return tabell.reset_index(names="kvartal")


def kvalitet_kohorter(ansatte, slutt):
    """Hvem som inngår i kvalitetstallene (kohortene), styrt av periodeslutt:
    faste ansatte med registrerte rekrutteringsdata, som har vært ansatt lenge nok
    til å kunne observeres – 12 mnd for tidlig turnover, 6 mnd for prøvetid."""
    faste = ansatte[(ansatte["ansettelsesform"] == "fast") & ansatte["rekrutteringsmetode"].notna()]
    siste_12 = slutt - pd.DateOffset(months=12)
    siste_6 = slutt - pd.DateOffset(months=6)
    return {
        "tidlig": faste[faste["ansattdato"] <= siste_12],
        "tidlig_til": siste_12,
        "provetid": faste[(faste["ansattdato"] <= siste_6) & faste["prøvetid_bestått"].notna()],
        "provetid_til": siste_6,
    }


def kvalitet_per_metode(ansatte, slutt):
    """Tidlig turnover og prøvetid bestått per rekrutteringsmetode, med n.
    Femregelen: grupper med færre enn 5 i kohorten får None (skjules)."""
    k = kvalitet_kohorter(ansatte, slutt)
    tidlig, provetid = k["tidlig"], k["provetid"]
    # Sluttet innen 12 mnd, av en grunn som teller i turnover
    sluttet_tidlig = (
        tidlig["sluttdato"].notna()
        & (tidlig["sluttdato"] < tidlig["ansattdato"] + pd.DateOffset(months=12))
        & tidlig["sluttårsak"].isin(TELLER_I_TURNOVER)
    )
    rader = []
    for metode in ["strukturert", "ustrukturert"]:
        er_t = tidlig["rekrutteringsmetode"] == metode
        er_p = provetid["rekrutteringsmetode"] == metode
        n_t, n_p = int(er_t.sum()), int(er_p.sum())
        rader.append({
            "metode": metode,
            "tidlig_n": n_t,
            "tidlig_antall": int((sluttet_tidlig & er_t).sum()) if n_t >= MIN_GRUPPE else None,
            "provetid_n": n_p,
            "provetid_bestatt": int((provetid.loc[er_p, "prøvetid_bestått"] == "ja").sum())
                                if n_p >= MIN_GRUPPE else None,
        })
    return pd.DataFrame(rader)

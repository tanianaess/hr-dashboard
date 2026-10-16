# Formler for dashbordet – som et eget beregningsark i Excel.
# Sidene i dashbordet henter tallene herfra, så hver formel finnes bare ett sted.
# Alle definisjoner følger CLAUDE.md.

import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd

# Mappen med CSV-filene (ligger ved siden av denne filen)
DATAMAPPE = Path(__file__).parent / "data"

# Første og siste dag dataene dekker
DATA_FRA = pd.Timestamp("2024-10-01")
DATA_TIL = pd.Timestamp("2026-09-30")

def _faste_perioder():
    """Faste, IKKE-overlappende perioder for sider med sensitive tall: siste 12 mnd og
    de 12 månedene før. Perioder som overlapper (f.eks. siste 24 mnd og et kalenderår),
    kunne trekkes fra hverandre og avsløre små grupper (se CLAUDE.md)."""
    siste_start = DATA_TIL + pd.Timedelta(days=1) - pd.DateOffset(months=12)
    forrige_start = siste_start - pd.DateOffset(months=12)
    return {
        "Siste 12 mnd": (siste_start, DATA_TIL),
        "Forrige 12 mnd": (forrige_start, siste_start - pd.Timedelta(days=1)),
    }


# Avganger som teller i turnover: stillingen må erstattes (se CLAUDE.md)
TELLER_I_TURNOVER = ["frivillig", "ufrivillig", "pensjon"]

# Femregelen: grupper med færre enn 5 skjules
MIN_GRUPPE = 5

FASTE_PERIODER = _faste_perioder()

# Trendgrafene for sykefravær og eNPS viser alltid hele dataperioden – én fast visning,
# uansett periodevalg. Femregelen gjelder da per punkt (måned eller kvartal).
TRENDPERIODE = (DATA_FRA, DATA_TIL)


def er_siste_12(start, slutt):
    """Sant når perioden er «Siste 12 mnd». Kostnaden ved uønsket turnover vises bare da."""
    return (start, slutt) == FASTE_PERIODER["Siste 12 mnd"]


def sekundar_prikking(skjulte):
    """Sekundær prikking: hvilke skjulte team må holdes utenfor totalen?
    `skjulte` er {team: størrelse} for team som allerede er skjult (primær prikking),
    der størrelse er antall ansatte, svar eller avganger.
    Er de skjulte teamene til sammen under 5, kunne de regnes ut som «total minus
    de synlige» – da holdes de utenfor. Er de til sammen 5 eller flere, kan de ikke
    skilles fra hverandre, og totalen kan ta med alle. Gir tilbake en sortert liste."""
    if skjulte and sum(skjulte.values()) < MIN_GRUPPE:
        return sorted(skjulte)
    return []


def med_unntak(navn, utenfor):
    """«Hele selskapet» → «Hele selskapet (uten ledergruppen)» når noen holdes utenfor."""
    return f"{navn} (uten {', '.join(utenfor)})" if utenfor else navn

# Standard kostnadsandel ved uønsket turnover (andel av årslønn) – antakelse
KOSTNADSANDEL_STANDARD = 0.75

# Merking som vises øverst på alle sider (se «Presentasjon» i CLAUDE.md)
SYNTETISK_MERKNAD = (
    "**Syntetiske data.** Alle tall i dette dashbordet er oppdiktet og konstruert "
    "for å illustrere metodikk, og bygger ikke på data fra noe ekte selskap."
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
    - totalt antall avganger og «kontrakt utløpt» vises alltid (ikke sensitivt)
    - team med færre enn 5 ansatte (i snitt): alt annet skjules
    - fordeling på frivillig/ufrivillig/pensjon og uønsket: bare med minst 5 avganger
    Skjulte tall settes til None (tom celle)."""
    sensitive = ["frivillig", "ufrivillig", "pensjon", "uønsket", "frivillig_rate", "uønsket_rate"]
    rader = []
    for team in team_liste:
        t = turnover(ansatte[ansatte["team"] == team], start, slutt)
        rad = {"team": team, **t}
        if t["snitt_ansatte"] < MIN_GRUPPE:
            for felt in [*sensitive, "snitt_ansatte", "total_rate"]:
                rad[felt] = None
            rad["skjult"] = "lite team"
        elif t["avganger"] < MIN_GRUPPE:
            for felt in sensitive:
                rad[felt] = None
            rad["skjult"] = "få avganger"
        else:
            rad["skjult"] = ""
        rad.pop("lønn_uønsket")  # Lønn vises aldri per team
        rader.append(rad)
    return pd.DataFrame(rader)


def avganger_per_maaned(ansatte, start, slutt):
    """Antall avganger som teller i turnover, per måned. Bare totalen: fordelingen på
    uønsket og sluttårsak vises aldri per måned, fordi én måned ofte er én person.
    Alle måneder i perioden er med, også de uten avganger (0)."""
    sluttet = sluttet_i_perioden(ansatte, start, slutt)
    teller = sluttet[sluttet["sluttårsak"].isin(TELLER_I_TURNOVER)]
    maaned = teller["sluttdato"].dt.strftime("%Y-%m")
    alle_maaneder = [d.strftime("%Y-%m") for d in maanedsslutter(start, slutt)]
    tabell = pd.DataFrame({"Avganger": teller.groupby(maaned).size()})
    # reindex = sørg for at alle måneder er med, tomme fylles med 0
    return tabell.reindex(alle_maaneder, fill_value=0).astype(int)


# --- Formatering (norsk tallformat) -------------------------------------------

def avrund(tall, desimaler=0):
    """Avrunding som AVRUND i Excel: 5 rundes opp (bort fra null).
    31,25 → 31,3 · 0,5 → 1 · −0,25 → −0,3.
    Pythons egen round() runder 5 mot nærmeste partall (31,25 → 31,2), så den
    skal ikke brukes til tall som vises i dashbordet."""
    # round(..., 10) fjerner bitte små regnerester først (f.eks. 14,449999999 → 14,45)
    renset = Decimal(str(round(float(tall), 10)))
    resultat = renset.quantize(Decimal(1).scaleb(-desimaler), rounding=ROUND_HALF_UP)
    return int(resultat) if desimaler == 0 else float(resultat)


def prosent(andel, desimaler=1):
    """0.143 → «14,3 %». Tom verdi → «–»."""
    if andel is None or pd.isna(andel):
        return "–"
    return f"{avrund(andel * 100, desimaler):.{desimaler}f} %".replace(".", ",")


def prosent_med_n(teller, nevner):
    """Prosent med n, for små grupper: «12,5 % (1 av 8)»."""
    if not nevner:
        return "–"
    return f"{prosent(teller / nevner)} ({teller} av {nevner})"


def endring_pp(ny, gammel):
    """Endring i prosentpoeng som tekst: «+3,1 pp», «−0,4 pp» eller «±0,0 pp»
    når endringen rundes av til null."""
    pp = avrund((ny - gammel) * 100, 1)
    if pp == 0:
        return "±0,0 pp"
    return f"{pp:+.1f} pp".replace(".", ",")


def minustegn(tekst):
    """Bytter bindestrek foran tall med ekte minustegn: «-14» → «−14».
    Brukes på tall som VISES. Ikke på pilene i st.metric (delta), der Streamlit
    bruker bindestreken til å avgjøre retningen på pilen."""
    return re.sub(r"(^|[\s(])-(?=\d)", lambda m: m.group(1) + "−", tekst) if tekst else tekst


def fortegn(tall):
    """Heltall med fortegn og ekte minustegn i tekst: +2, −14, 0."""
    return "0" if tall == 0 else f"{tall:+d}".replace("-", "−")


def enps_tekst(verdi):
    """eNPS som tekst: 13,6 → «+14», −14 → «−14», 0 → «0». Tom verdi → «–»."""
    if verdi is None or pd.isna(verdi):
        return "–"
    return fortegn(avrund(verdi))


def endring_antall(diff, enhet, entall=None):
    """Endring i hele enheter til pilen i KPI-kort: «+3 poeng», «-6 dager», «±0 dager».
    `entall` brukes når endringen er 1 («+1 dag»). Tom verdi → None (ingen pil).
    Bindestrek, ikke minustegn: Streamlit bruker den til å avgjøre retningen på pilen."""
    if diff is None or pd.isna(diff):
        return None
    tall = avrund(diff)
    if tall == 0:
        return f"±0 {enhet}"
    return f"{tall:+d} {entall if entall and abs(tall) == 1 else enhet}"


# Felles tekst for tall som er skjult av personvernhensyn
SKJULT = "skjult"
SKJULT_UNDER_5 = "skjult (under 5)"
SKJULT_PRIKKET = "skjult (sekundær prikking)"


def pilfarge(endring_tekst, hoyere_er_bedre=False):
    """Farge på pilen i KPI-kort. Vanligvis er økning dårlig (rød), f.eks. turnover.
    Med hoyere_er_bedre=True er økning bra (grønn). Ingen farge når endringen er null."""
    if endring_tekst and endring_tekst.startswith("±"):
        return "off"
    return "normal" if hoyere_er_bedre else "inverse"


def millioner(belop, desimaler=1):
    """5 580 000 → «5,6 mill. kr». Kostnaden rundes grovt med vilje (se CLAUDE.md)."""
    tall = f"{avrund(belop / 1_000_000, desimaler):.{desimaler}f}".replace(".", ",")
    return f"{tall} mill. kr"


def endring_millioner(ny, gammel):
    """Endring i grovt avrundet kostnad, f.eks. «+3,1 mill. kr». Regnes på de avrundede
    tallene som vises, så endringen ikke avslører mer enn tallene selv.
    Bindestrek, ikke minustegn: Streamlit bruker den til å avgjøre retningen på pilen."""
    diff = avrund(ny / 1_000_000, 1) - avrund(gammel / 1_000_000, 1)
    tekst = f"{abs(diff):.1f}".replace(".", ",")
    return "±0,0 mill. kr" if diff == 0 else f"{'+' if diff > 0 else '-'}{tekst} mill. kr"


def kroner(belop):
    """2700000 → «2 700 000 kr»."""
    return f"{avrund(belop):,} kr".replace(",", " ")


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
    arbeidsdager (mandag-fredag) mens personen var ansatt × stillingsprosent.
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


def antall_per_team_og_maaned(ansatte):
    """Antall ansatte ved hver månedsslutt, per team – brukes til femregelen per punkt."""
    return pd.DataFrame([
        {"team": team, "måned": dag.strftime("%Y-%m"),
         "antall_ansatte": antall_ansatt_paa(ansatte[ansatte["team"] == team], dag)}
        for dag in maanedsslutter(DATA_FRA, DATA_TIL) for team in TEAM
    ])


def fravaer_med_avtalte(ansatte, fravaer):
    """Legger avtalte dagsverk og antall ansatte inn ved siden av tapte dagsverk.
    merge = slå opp på team og måned, som XOPPSLAG med to kriterier."""
    return (fravaer.merge(avtalte_dagsverk(ansatte), on=["team", "måned"], how="left")
                   .merge(antall_per_team_og_maaned(ansatte), on=["team", "måned"], how="left"))


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
    """Sykefravær per måned i prosent, delt i korttid og langtid. Femregelen gjelder
    per punkt: små team holdes utenfor måneden hvis de til sammen er under 5
    (sekundær prikking), og måneder med under 5 ansatte i utvalget vises ikke."""
    f = fravaer_i_perioden(fravaer, start, slutt)
    rader = {}
    for maaned, f_m in f.groupby("måned"):
        if f_m["team"].nunique() > 1:
            skjulte = dict(zip(f_m.loc[f_m["antall_ansatte"] < MIN_GRUPPE, "team"],
                               f_m.loc[f_m["antall_ansatte"] < MIN_GRUPPE, "antall_ansatte"]))
            f_m = f_m[~f_m["team"].isin(sekundar_prikking(skjulte))]
        if f_m["antall_ansatte"].sum() < MIN_GRUPPE:
            continue  # for få i utvalget denne måneden
        avtalte = f_m["avtalte_dagsverk"].sum()
        rader[maaned] = {"Korttid": f_m["tapte_dagsverk_korttid"].sum() / avtalte * 100,
                         "Langtid": f_m["tapte_dagsverk_langtid"].sum() / avtalte * 100}
    return pd.DataFrame.from_dict(rader, orient="index").rename_axis("måned")


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
    """Nøkkeltall for ansettelser i perioden. Femregelen: med under 5 ansettelser
    skjules median og andel strukturert (None) – de kan peke ut enkeltpersoner."""
    a = ansettelser_i_perioden(ansatte, start, slutt)
    strukturert = int((a["rekrutteringsmetode"] == "strukturert").sum())
    if len(a) < MIN_GRUPPE:
        return {"antall": len(a), "median_dager": None, "andel_strukturert": None,
                "strukturert": None}
    return {
        "antall": len(a),
        "median_dager": a["dager_til_ansettelse"].median(),
        "andel_strukturert": strukturert / len(a),
        "strukturert": strukturert,
    }


def tid_til_ansettelse_per_team(ansatte, start, slutt, team_liste=TEAM):
    """Median dager fra utlysning til aksept per team, med antall ansettelser (n).
    Femregelen: median vises bare med minst 5 ansettelser (ellers None)."""
    a = ansettelser_i_perioden(ansatte, start, slutt)
    rader = []
    for team in team_liste:
        t = a[a["team"] == team]
        rader.append({"team": team, "antall": len(t),
                      "median_dager": t["dager_til_ansettelse"].median()
                                      if len(t) >= MIN_GRUPPE else None})
    return pd.DataFrame(rader)


def strukturert_per_kvartal(ansatte, start, slutt):
    """Andel strukturerte ansettelser per kvartal, med antall ansettelser (n).
    Femregelen: kvartaler med under 5 ansettelser tas ikke med."""
    a = ansettelser_i_perioden(ansatte, start, slutt)
    kvartal = a["ansattdato"].dt.year.astype(str) + "-K" + a["ansattdato"].dt.quarter.astype(str)
    er_strukturert = a["rekrutteringsmetode"] == "strukturert"
    tabell = pd.DataFrame({
        "antall": er_strukturert.groupby(kvartal).size(),
        "strukturert": er_strukturert.groupby(kvartal).sum(),
    })
    tabell = tabell[tabell["antall"] >= MIN_GRUPPE]
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


def _kvalitet_per_gruppe(ansatte, slutt, gruppe, grupper):
    """Felles regnestykke: tidlig turnover og prøvetid bestått for hver gruppe.
    `gruppe` er en funksjon som gir hver ansatt en gruppe (f.eks. metode eller nivå).
    Femregelen: grupper med færre enn 5 i kohorten får None (skjules)."""
    k = kvalitet_kohorter(ansatte, slutt)
    tidlig, provetid = k["tidlig"], k["provetid"]
    # Sluttet innen 12 mnd, av en grunn som teller i turnover
    sluttet_tidlig = (
        tidlig["sluttdato"].notna()
        & (tidlig["sluttdato"] < tidlig["ansattdato"] + pd.DateOffset(months=12))
        & tidlig["sluttårsak"].isin(TELLER_I_TURNOVER)
    )
    gruppe_t, gruppe_p = gruppe(tidlig), gruppe(provetid)
    rader = []
    for navn in grupper:
        er_t, er_p = gruppe_t == navn, gruppe_p == navn
        n_t, n_p = int(er_t.sum()), int(er_p.sum())
        rader.append({
            "gruppe": navn,
            "tidlig_n": n_t,
            "tidlig_antall": int((sluttet_tidlig & er_t).sum()) if n_t >= MIN_GRUPPE else None,
            "provetid_n": n_p,
            "provetid_bestatt": int((provetid.loc[er_p, "prøvetid_bestått"] == "ja").sum())
                                if n_p >= MIN_GRUPPE else None,
        })
    return pd.DataFrame(rader)


def kvalitet_per_nivaa(ansatte, slutt):
    """Tidlig turnover og prøvetid bestått på tre nivåer, med n."""
    return _kvalitet_per_gruppe(ansatte, slutt, rekrutteringsnivaa, NIVAAER)


def kvalitet_per_nivaa_prikket(ansatte, slutt, team_liste=TEAM):
    """Som kvalitet_per_nivaa, men med sekundær prikking når flere team er med:
    en celle i totalen skjules hvis teamene som er skjult i den cellen (under 5),
    til sammen er 1-4 – ellers kunne de regnes ut som total minus de synlige teamene.
    Kolonnene «tidlig_prikket» og «provetid_prikket» viser hvilke celler det gjelder."""
    utvalg = ansatte[ansatte["team"].isin(team_liste)]
    total = kvalitet_per_nivaa(utvalg, slutt).set_index("gruppe")
    total["tidlig_prikket"] = total["provetid_prikket"] = False
    if len(team_liste) > 1:
        per_team = {t: kvalitet_per_nivaa(utvalg[utvalg["team"] == t], slutt).set_index("gruppe")
                    for t in team_liste}
        for nivaa in NIVAAER:
            for maal, n_kol in [("tidlig", "tidlig_n"), ("provetid", "provetid_n")]:
                skjult_rest = sum(int(k.loc[nivaa, n_kol]) for k in per_team.values()
                                  if 0 < k.loc[nivaa, n_kol] < MIN_GRUPPE)
                antall_kol = "tidlig_antall" if maal == "tidlig" else "provetid_bestatt"
                # Bare celler som ellers ville vært synlige, prikkes sekundært
                if 0 < skjult_rest < MIN_GRUPPE and pd.notna(total.loc[nivaa, antall_kol]):
                    total.loc[nivaa, f"{maal}_prikket"] = True
                    total.loc[nivaa, antall_kol] = None
    return total.reset_index()


# --- Bemanning mot plan -----------------------------------------------------------

# Team med større avvik enn dette (i begge retninger) markeres
AVVIK_GRENSE = 0.05


def over_avviksgrense(faktisk, plan):
    """Sant når faktisk avviker mer enn 5 % fra plan – i begge retninger.
    Brukes både i tabellen og på KPI-kortet, så regelen er lik overalt."""
    return plan > 0 and abs(faktisk - plan) / plan > AVVIK_GRENSE


def les_bemanningsplan():
    """Leser bemanningsplan.csv: planlagt antall per team og måned."""
    return pd.read_csv(DATAMAPPE / "bemanningsplan.csv")


def bemanning_per_maaned(ansatte, plan, start, slutt):
    """Faktisk og planlagt antall ansatte ved hver månedsslutt i perioden.
    Faktisk = alle ansettelsesformer. Gjelder de team som er med i tabellene."""
    rader = []
    for dag in maanedsslutter(start, slutt):
        maaned = dag.strftime("%Y-%m")
        rader.append({
            "måned": maaned,
            "Faktisk": antall_ansatt_paa(ansatte, dag),
            "Plan": int(plan.loc[plan["måned"] == maaned, "planlagt_antall"].sum()),
        })
    return pd.DataFrame(rader)


def bemanning_per_team(ansatte, plan, start, slutt, team_liste=TEAM):
    """Én rad per team: plan og faktisk ved periodeslutt, avvik, bemanningsgrad,
    ansettelser og avganger i perioden, og median tid til tiltredelse
    (None når den bygger på under 5 ansettelser – femregelen)."""
    siste_maaned = slutt.strftime("%Y-%m")
    rader = []
    for team in team_liste:
        a = ansatte[ansatte["team"] == team]
        planlagt = int(plan.loc[(plan["team"] == team) & (plan["måned"] == siste_maaned),
                                "planlagt_antall"].sum())
        faktisk = antall_ansatt_paa(a, slutt)
        midlertidige = antall_ansatt_paa(a[a["ansettelsesform"] == "midlertidig"], slutt)

        # Ansettelser og avganger i perioden (alle ansettelsesformer og sluttårsaker)
        ansatt_i_perioden = a[(a["ansattdato"] >= start) & (a["ansattdato"] <= slutt)]
        sluttet = sluttet_i_perioden(a, start, slutt)

        # Tid til tiltredelse: fra utlysning til første arbeidsdag
        med_data = ansatt_i_perioden[ansatt_i_perioden["utlysningsdato"].notna()]
        dager = (med_data["ansattdato"] - med_data["utlysningsdato"]).dt.days

        avvik = faktisk - planlagt
        rader.append({
            "team": team,
            "plan": planlagt,
            "faktisk": faktisk,
            "midlertidige": midlertidige,
            "avvik": avvik,
            "bemanningsgrad": faktisk / planlagt if planlagt else None,
            "markert": over_avviksgrense(faktisk, planlagt),
            "ansettelser": len(ansatt_i_perioden),
            "avganger": len(sluttet),
            # Femregelen: medianen vises bare når den bygger på minst 5 ansettelser
            "tiltredelse_median": dager.median() if len(dager) >= MIN_GRUPPE else None,
            "tiltredelse_n": len(dager),
        })
    return pd.DataFrame(rader)



# --- Tilleggsmetoder og forskning --------------------------------------------------

# Kolonnenavn → visningsnavn
TILLEGGSMETODER = {"case_study": "case study", "personlighetstest": "personlighetstest",
                   "evnetest": "evnetest"}

NIVAAER = ["ustrukturert", "strukturert intervju alene", "strukturert + tillegg"]


def rekrutteringsnivaa(ansatte):
    """Gir hver ansatt ett av tre nivåer (eller tom verdi før registrering).
    Som en HVIS-formel i en hjelpekolonne i Excel."""
    har_tillegg = (ansatte[list(TILLEGGSMETODER)] == "ja").any(axis=1)
    nivaa = pd.Series(None, index=ansatte.index, dtype="object")
    nivaa[ansatte["rekrutteringsmetode"] == "ustrukturert"] = NIVAAER[0]
    nivaa[(ansatte["rekrutteringsmetode"] == "strukturert") & ~har_tillegg] = NIVAAER[1]
    nivaa[(ansatte["rekrutteringsmetode"] == "strukturert") & har_tillegg] = NIVAAER[2]
    return nivaa


def bruk_av_tilleggsmetoder(ansatte, start, slutt):
    """Antall ansettelser i perioden per tilleggsmetode – bare antall, aldri resultater.
    Femregelen: under 5 skjules (None), også for hele selskapet."""
    a = ansettelser_i_perioden(ansatte, start, slutt)
    tellinger = {navn: int((a[kolonne] == "ja").sum()) for kolonne, navn in TILLEGGSMETODER.items()}
    tellinger["minst én metode"] = int((a[list(TILLEGGSMETODER)] == "ja").any(axis=1).sum())
    return {k: (v if v >= MIN_GRUPPE else None) for k, v in tellinger.items()}


# Validitet (korrigert, operasjonell) for jobbprestasjon.
# Sackett, Zhang, Berry og Lievens (2022): «Revisiting meta-analytic estimates of
# validity in personnel selection», Journal of Applied Psychology 107(11), 2040-2068,
# tabell 3. Verifisert av brukeren mot tabell 3.
# Schmidt og Hunter (1998) sine tidligere anslag gjengis i samme tabell 3 i
# Sackett mfl. (2022). Verifisert av brukeren.
FORSKNING_KILDE = "Sackett mfl. (2022), tabell 3"
FORSKNING_KILDE_URL = "https://doi.org/10.1037/apl0000994"
TIDLIGERE_KILDE = "Schmidt og Hunter (1998), gjengitt i Sackett mfl. (2022), tabell 3"
FORSKNING_VALIDITET = [
    # (metode i dashbordet, kategori i forskningen, Sackett mfl. 2022, Schmidt og Hunter 1998)
    ("Strukturert intervju", "strukturert intervju", 0.42, 0.51),
    ("Case study", "arbeidsprøve (work sample), nærmeste kategori", 0.33, 0.54),
    ("Evnetest", "generell kognitiv evne", 0.31, 0.51),
    ("Ustrukturert intervju", "ustrukturert intervju", 0.19, 0.38),
    ("Personlighetstest (Big Five)", "planmessighet", 0.19, 0.31),
    ("Personlighetstest (Big Five)", "ekstroversjon", 0.10, None),
    ("Personlighetstest (Big Five)", "medmenneskelighet", 0.10, None),
    ("Personlighetstest (Big Five)", "emosjonell stabilitet", 0.09, None),
    ("Personlighetstest (Big Five)", "åpenhet for erfaring", 0.05, None),
]


# --- Engasjement (eNPS) -----------------------------------------------------------

# Svarandel under dette markeres som lav
LAV_SVARANDEL = 0.50

# Et team uthevet i eNPS-grafen bare hvis det har falt minst så mange poeng
UTHEV_FALL = 10

KOBLING_MERKNAD = (
    "**Sammenheng, ikke nødvendigvis årsak** – og den kan gå begge veier: lavt "
    "engasjement kan gi mer fravær, og høyt fravær gir mer belastning på dem som er igjen."
)


def les_engasjement():
    """Leser engasjement.csv: eNPS, antall svar og antall invitert per team og kvartal."""
    return pd.read_csv(DATAMAPPE / "engasjement.csv")


def kvartaler_i_perioden(start, slutt):
    """Kvartaler som ligger helt innenfor perioden, f.eks. ['2025-K4', '2026-K1', …]."""
    kvartaler = []
    for kvartal_start in pd.date_range(start, slutt, freq="QS"):
        if maanedsslutt(kvartal_start + pd.DateOffset(months=2)) <= slutt:
            kvartaler.append(f"{kvartal_start.year}-K{kvartal_start.quarter}")
    return kvartaler


def kvartal_minus(kvartal, antall):
    """«2026-K3» minus 1 → «2026-K2», minus 4 → «2025-K3»."""
    aar, k = int(kvartal[:4]), int(kvartal[-1])
    nr = aar * 4 + (k - 1) - antall
    return f"{nr // 4}-K{nr % 4 + 1}"


def enps_samlet(engasjement):
    """eNPS for flere team samlet: gjennomsnitt vektet med antall svar.
    Som SUMMERPRODUKT(eNPS; svar) / SUMMER(svar) i Excel.
    Femregelen: under 5 svar totalt gir None."""
    svar = engasjement["antall_svar"].sum()
    if svar < MIN_GRUPPE:
        return None
    return {
        "enps": (engasjement["enps"] * engasjement["antall_svar"]).sum() / svar,
        "svar": int(svar),
        "invitert": int(engasjement["antall_invitert"].sum()),
        "svarandel": svar / engasjement["antall_invitert"].sum(),
    }


def enps_per_kvartal(engasjement, kvartaler):
    """Samlet eNPS (vektet) for hvert kvartal. Kvartaler med under 5 svar utelates."""
    rader = []
    for kvartal in kvartaler:
        e = enps_samlet(engasjement[engasjement["kvartal"] == kvartal])
        if e:
            rader.append({"kvartal": kvartal, **e})
    # Faste kolonner, så tabellen har riktig form også når alle kvartaler er skjult
    return pd.DataFrame(rader, columns=["kvartal", "enps", "svar", "invitert", "svarandel"])


def langtid_per_kvartal(fravaer, kvartaler):
    """Langtidsfravær per kvartal: tapte langtid / avtalte dagsverk for kvartalets måneder.
    Femregelen per punkt: et kvartal tas bare med når utvalget hadde minst 5 ansatte
    i hver av kvartalets måneder."""
    f = fravaer.copy()
    maaned = pd.to_datetime(f["måned"], format="%Y-%m")
    f["kvartal"] = maaned.dt.year.astype(str) + "-K" + maaned.dt.quarter.astype(str)
    f = f[f["kvartal"].isin(kvartaler)]
    # Minste antall ansatte i en måned i kvartalet (summert over teamene i utvalget)
    minst = f.groupby(["kvartal", "måned"])["antall_ansatte"].sum().groupby("kvartal").min()
    per_k = f.groupby("kvartal")[["tapte_dagsverk_langtid", "avtalte_dagsverk"]].sum()
    per_k = per_k[minst.reindex(per_k.index) >= MIN_GRUPPE]
    return (per_k["tapte_dagsverk_langtid"] / per_k["avtalte_dagsverk"]).rename("langtid_rate")


def alle_sammenligningsperioder():
    """Alle perioder som kan vises eller sammenlignes med på sider med faste perioder:
    hver fast periode, perioden rett før, og samme periode i fjor (innenfor dataene).
    Brukes til å gjøre sekundær prikking lik i alle periodevalg."""
    perioder = set()
    for start, slutt in FASTE_PERIODER.values():
        for p_start, p_slutt in [(start, slutt), forrige_periode(start, slutt),
                                 samme_periode_i_fjor(start, slutt)]:
            if p_start >= DATA_FRA:
                perioder.add((p_start, p_slutt))
    return sorted(perioder)


# --- Sekundær prikking per tema (brukes av sidene OG forsiden) ---------------------
# Alle tre: prikkingen er lik i alle periodevalg (sjekkes i alle perioder som kan
# velges eller sammenlignes med), og gjelder bare totaler – ett team alene får [].

def _utenfor(skjulte_per_periode):
    """Felles regnestykke: `skjulte_per_periode` er en liste – én per periode – med
    {team: størrelse} for team som er skjult I DEN perioden. Er de skjulte til sammen
    under 5 i minst én periode, holdes de utenfor totalen i alle periodevalg."""
    utenfor = set()
    # Gjenta til ingenting endrer seg: når noen team holdes utenfor, kan resten av de
    # skjulte i en annen periode bli under 5 – da må også de holdes utenfor.
    endret = True
    while endret:
        endret = False
        for skjulte in skjulte_per_periode:
            rest = {t: n for t, n in skjulte.items() if t not in utenfor}
            ny = set(sekundar_prikking(rest))
            if ny:
                utenfor |= ny
                endret = True
    return sorted(utenfor)


def utenfor_turnoverfordeling(ansatte, team_liste):
    """Team som holdes utenfor fordelingen (uønsket og sluttårsak) i totaler."""
    if len(team_liste) <= 1:
        return []
    skjulte_per_periode = []
    for start, slutt in alle_sammenligningsperioder():
        skjulte = {}
        for team in team_liste:
            t = turnover(ansatte[ansatte["team"] == team], start, slutt)
            if t["snitt_ansatte"] < MIN_GRUPPE or t["avganger"] < MIN_GRUPPE:
                skjulte[team] = t["avganger"]
        skjulte_per_periode.append(skjulte)
    return _utenfor(skjulte_per_periode)


def utenfor_sykefravaer(ansatte, team_liste):
    """Team som holdes utenfor sykefraværstotaler (små team etter antall ansatte)."""
    if len(team_liste) <= 1:
        return []
    skjulte_per_periode = []
    for start, slutt in alle_sammenligningsperioder():
        snitt = {team: snitt_ansatte(ansatte[ansatte["team"] == team], start, slutt)
                 for team in team_liste}
        skjulte_per_periode.append({t: n for t, n in snitt.items() if n < MIN_GRUPPE})
    return _utenfor(skjulte_per_periode)


def utenfor_enps(engasjement, team_liste):
    """Team som holdes utenfor eNPS-totaler (team med under 5 svar i et kvartal)."""
    if len(team_liste) <= 1:
        return []
    e = engasjement[engasjement["team"].isin(team_liste)]
    return _utenfor([
        {team: int(n) for team, n in zip(k["team"], k["antall_svar"]) if n < MIN_GRUPPE}
        for _, k in e.groupby("kvartal")
    ])

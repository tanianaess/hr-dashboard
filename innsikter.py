# Regler for ledelsesoversikten: status for nøkkeltall og automatiske innsikter.
# Regelbasert (ingen AI). Bruker de samme formlene og personvernreglene som sidene,
# så forsiden aldri viser noe som ikke også vises der – og aldri noe om skjulte grupper.

import pandas as pd

import beregninger as b

OK, FOLG_MED, KRITISK = "OK", "Følg med", "Kritisk"

# Terskler for status (skjønn, ikke en standard – vises åpent på forsiden).
# ok / kritisk: grensene. ok_inkludert: om «inntil» (≤) eller «under» (<).
# forverring: så stor forverring løfter OK til minst «Følg med» (None = ingen regel).
TERSKLER = {
    "Total turnover": dict(ok=10.0, kritisk=15.0, hoyere_er_verre=True, ok_inkludert=False,
                           forverring=3.0, tekst=("under 10 %", "10-15 %", "over 15 %"),
                           forverring_tekst="+3 pp"),
    "Uønsket turnover": dict(ok=3.0, kritisk=5.0, hoyere_er_verre=True, ok_inkludert=False,
                             forverring=2.0, tekst=("under 3 %", "3-5 %", "over 5 %"),
                             forverring_tekst="+2 pp"),
    "Sykefravær": dict(ok=5.0, kritisk=6.0, hoyere_er_verre=True, ok_inkludert=False,
                       forverring=1.0, tekst=("under 5 %", "5-6 %", "over 6 % (internt mål)"),
                       forverring_tekst="+1 pp"),
    "eNPS": dict(ok=10, kritisk=0, hoyere_er_verre=False, ok_inkludert=True,
                 forverring=10, tekst=("+10 eller høyere", "0 til +9", "under 0"),
                 forverring_tekst="−10 poeng"),
    "Bemanning mot plan": dict(ok=5.0, kritisk=10.0, hoyere_er_verre=True, ok_inkludert=True,
                               forverring=None, tekst=("avvik inntil 5 %", "5-10 %", "over 10 %"),
                               forverring_tekst="–"),
    "Tid til ansettelse": dict(ok=45, kritisk=60, hoyere_er_verre=True, ok_inkludert=True,
                               forverring=15, tekst=("inntil 45 dager", "46-60 dager", "over 60 dager"),
                               forverring_tekst="+15 dager"),
}


def status(navn, verdi, endring=None):
    """Status for et nøkkeltall: (status, grunn). `verdi` og `endring` skal være de
    avrundede tallene som vises (prosent i prosentpoeng, eNPS i poeng, dager i dager)."""
    t = TERSKLER[navn]
    if t["hoyere_er_verre"]:
        ok = verdi <= t["ok"] if t["ok_inkludert"] else verdi < t["ok"]
        kritisk = verdi > t["kritisk"]
        forverret = endring is not None and t["forverring"] is not None and endring >= t["forverring"]
    else:
        ok = verdi >= t["ok"] if t["ok_inkludert"] else verdi > t["ok"]
        kritisk = verdi < t["kritisk"]
        forverret = endring is not None and t["forverring"] is not None and -endring >= t["forverring"]
    if kritisk:
        return KRITISK, t["tekst"][2]
    if ok and forverret:
        return FOLG_MED, f"rask forverring ({t['forverring_tekst']} eller mer)"
    if ok:
        return OK, t["tekst"][0]
    return FOLG_MED, t["tekst"][1]


def _prosentpoeng(andel, desimaler=1):
    """0.1434 → 14.3 (avrundet som visningen)."""
    return b.avrund(andel * 100, desimaler)


def _liste(navn):
    """['a', 'b', 'c'] → «a, b og c»."""
    return navn[0] if len(navn) == 1 else f"{', '.join(navn[:-1])} og {navn[-1]}"


def felles_merknad(liste):
    """Det som gjelder flere kort, sagt én gang over kortene i stedet for på hvert kort:
    hva pilene sammenligner med, og hvilke grupper som er holdt utenfor."""
    forrige = [k["kortnavn"] for k in liste if k.get("sammenligning") == "forrige"]
    fjor = [k["kortnavn"] for k in liste if k.get("sammenligning") == "fjor"]
    deler = []
    if forrige and fjor:
        deler.append(f"Pilene viser endring mot forrige 12 måneder for {_liste(forrige)}, "
                     f"og mot samme periode i fjor for {_liste(fjor)}.")
    elif forrige or fjor:
        deler.append("Pilene viser endring mot "
                     + ("forrige 12 måneder." if forrige else "samme periode i fjor."))
    grupper = {}
    for k in liste:
        if k.get("utenfor"):
            grupper.setdefault(tuple(k["utenfor"]), []).append(k["kortnavn"])
    for utenfor, navn in grupper.items():
        deler.append(f"{_liste(list(utenfor)).capitalize()} er holdt utenfor {_liste(navn)}, "
                     "fordi gruppen er for liten til å vises.")
    return " ".join(deler)


# =============================================================================
# NØKKELTALL (hele selskapet, siste 12 mnd)
# =============================================================================

def nokkeltall(ansatte, fravaer, engasjement, plan):
    """De viktigste tallene for hele selskapet, med endring og status.
    Samme formler og samme sekundære prikking som på de andre sidene."""
    start, slutt = b.FASTE_PERIODER["Siste 12 mnd"]
    fs, fe = b.forrige_periode(start, slutt)
    js, je = b.samme_periode_i_fjor(start, slutt)
    liste = []

    # Total turnover (alle team – ikke sensitivt)
    naa, forrige = b.turnover(ansatte, start, slutt), b.turnover(ansatte, fs, fe)
    v, d = _prosentpoeng(naa["total_rate"]), _prosentpoeng(naa["total_rate"] - forrige["total_rate"])
    liste.append(dict(navn="Total turnover", verdi=b.prosent(naa["total_rate"]),
                      endring=b.endring_pp(naa["total_rate"], forrige["total_rate"]),
                      status=status("Total turnover", v, d),
                      ekstra=f"{naa['avganger']} avganger.",
                      kortnavn="turnover", sammenligning="forrige",
                      side="Turnover"))

    # Uønsket turnover og kostnad (fordeling – sekundær prikking)
    utenfor = b.utenfor_turnoverfordeling(ansatte, b.TEAM)
    a_f = ansatte[~ansatte["team"].isin(utenfor)]
    nf, ff = b.turnover(a_f, start, slutt), b.turnover(a_f, fs, fe)
    v, d = _prosentpoeng(nf["uønsket_rate"]), _prosentpoeng(nf["uønsket_rate"] - ff["uønsket_rate"])
    st_uonsket = status("Uønsket turnover", v, d)
    liste.append(dict(navn="Uønsket turnover", verdi=b.prosent(nf["uønsket_rate"]),
                      endring=b.endring_pp(nf["uønsket_rate"], ff["uønsket_rate"]),
                      status=st_uonsket, ekstra=f"{nf['uønsket']} vi ville beholdt.",
                      kortnavn="uønsket turnover", sammenligning="forrige", utenfor=utenfor,
                      side="Turnover"))
    # Erstatningskostnad for ALLE avganger som må erstattes, med uønsket som en del av den.
    # Bygger på lønn: bare siste 12 mnd mot forrige 12 mnd (de to faste periodene), grovt
    # avrundet, og bare med minst 5 avganger (se CLAUDE.md).
    st_total = liste[0]["status"]
    if naa["avganger"] >= b.MIN_GRUPPE:
        kostnad = naa["lønn_avganger"] * b.KOSTNADSANDEL_STANDARD
        pil = (b.endring_millioner(kostnad, forrige["lønn_avganger"] * b.KOSTNADSANDEL_STANDARD)
               if forrige["avganger"] >= b.MIN_GRUPPE else None)
        herav = (f"Herav uønsket {b.millioner(nf['lønn_uønsket'] * b.KOSTNADSANDEL_STANDARD)}."
                 if nf["uønsket"] >= b.MIN_GRUPPE else "Uønsket er skjult (under 5).")
        liste.append(dict(navn="Erstatningskostnad", verdi=b.millioner(kostnad), endring=pil,
                          status=(st_total[0], "følger total turnover"),
                          ekstra=f"{naa['avganger']} avganger. {herav} Antar "
                                 f"{b.prosent(b.KOSTNADSANDEL_STANDARD, 0)} av årslønn per avgang.",
                          kortnavn="erstatningskostnad", sammenligning="forrige",
                          side="Turnover"))

    # Sykefravær (sekundær prikking)
    utenfor_s = b.utenfor_sykefravaer(ansatte, b.TEAM)
    f_s = fravaer[~fravaer["team"].isin(utenfor_s)]
    sn, sj = b.sykefravaer(f_s, start, slutt), b.sykefravaer(f_s, js, je)
    # Status settes på tallene som vises: verdien med 2 desimaler, endringen med 1 (som pilen)
    v, d = _prosentpoeng(sn["total_rate"], 2), _prosentpoeng(sn["total_rate"] - sj["total_rate"], 1)
    st_fravaer = status("Sykefravær", v, d)
    liste.append(dict(navn="Sykefravær", verdi=b.prosent(sn["total_rate"], 2),
                      endring=b.endring_pp(sn["total_rate"], sj["total_rate"]),
                      terskel=b.VESENTLIG_ENDRING_SYKEFRAVAER_PP,
                      status=st_fravaer,
                      ekstra=f"Internt mål {b.prosent(b.SYKEFRAVAER_MAL, 0)}.",
                      kortnavn="sykefravær", sammenligning="fjor", utenfor=utenfor_s,
                      side="Sykefravær"))

    # Kostnad i arbeidsgiverperioden (bygger på lønn: hele selskapet, siste 12 mnd)
    a_s = ansatte[~ansatte["team"].isin(utenfor_s)]
    fk, fk_fjor = b.fravaerskostnad(a_s, f_s, start, slutt), b.fravaerskostnad(a_s, f_s, js, je)
    pil = b.endring_millioner(fk, fk_fjor) if fk_fjor else None
    liste.append(dict(navn="Fraværskostnad", verdi=b.millioner(fk), endring=pil,
                      status=(st_fravaer[0], "følger sykefravær"),
                      ekstra="Bare lønn for korttidsfravær (dag 1-16). Reell kostnad er høyere.",
                      kortnavn="fraværskostnad", sammenligning="fjor", utenfor=utenfor_s,
                      side="Sykefravær"))

    # eNPS (sekundær prikking), siste kvartal mot samme kvartal i fjor
    utenfor_e = b.utenfor_enps(engasjement, b.TEAM)
    e_e = engasjement[~engasjement["team"].isin(utenfor_e)]
    siste = b.kvartaler_i_perioden(start, slutt)[-1]
    fjor_k = b.kvartal_minus(siste, 4)
    en = b.enps_samlet(e_e[e_e["kvartal"] == siste])
    ej = b.enps_samlet(e_e[e_e["kvartal"] == fjor_k])
    d_poeng = b.avrund(en["enps"] - ej["enps"]) if ej else None
    liste.append(dict(navn=f"eNPS {siste}", verdi=b.enps_tekst(en["enps"]),
                      endring=b.endring_antall(d_poeng, "poeng"),
                      hoyere_er_bedre=True,
                      status=status("eNPS", b.avrund(en["enps"]), d_poeng),
                      # Lav svarandel (under 50 %) markeres, som på Engasjement-siden
                      ekstra=f"Svarandel {b.prosent(en['svarandel'], 0)}"
                             + (" (lav)." if en["svarandel"] < b.LAV_SVARANDEL else "."),
                      kortnavn="eNPS", sammenligning="fjor", utenfor=utenfor_e,
                      side="Engasjement"))

    # Bemanning mot plan (alle team – ikke sensitivt), nøytral visning uten pil
    bt, bf = b.bemanning_per_team(ansatte, plan, start, slutt), b.bemanning_per_team(ansatte, plan, fs, fe)
    faktisk, planlagt = int(bt["faktisk"].sum()), int(bt["plan"].sum())
    avvik, avvik_for = faktisk - planlagt, int(bf["faktisk"].sum() - bf["plan"].sum())
    v = _prosentpoeng(abs(avvik) / planlagt)
    liste.append(dict(navn="Bemanning mot plan", verdi=b.fortegn(avvik),
                      endring=None, status=status("Bemanning mot plan", v),
                      ekstra=f"{faktisk} ansatte av {planlagt} planlagt ({b.prosent(faktisk / planlagt)}). "
                             f"Avvik for ett år siden: {b.fortegn(avvik_for)}.",
                      kortnavn="bemanning",
                      side="Bemanning"))

    # Tid til ansettelse, mot samme periode i fjor
    # Femregelen: medianen er None når den bygger på under 5 ansettelser
    rn, rj = b.rekruttering(ansatte, start, slutt), b.rekruttering(ansatte, js, je)
    if rn["median_dager"] is not None:
        dager = b.avrund(rn["median_dager"])
        d_dager = (b.avrund(rn["median_dager"] - rj["median_dager"])
                   if rj["median_dager"] is not None else None)
        st_tid = status("Tid til ansettelse", dager, d_dager)
        # Snittet kan skjule et team som trekker ned: vis tregeste team (minst 5
        # ansettelser, som på Rekruttering), og løft status til minst «Følg med»
        # hvis det teamet er over grensen for kritisk.
        per_team = b.tid_til_ansettelse_per_team(ansatte, start, slutt).dropna(subset=["median_dager"])
        tregest = per_team.loc[per_team["median_dager"].idxmax()] if len(per_team) else None
        tregest_tekst = ""
        if tregest is not None:
            t_dager = b.avrund(tregest["median_dager"])
            tregest_tekst = (f" Tregest: {tregest['team']}, {t_dager} dager "
                             f"({int(tregest['antall'])} ansettelser).")
            if st_tid[0] == OK and t_dager > TERSKLER["Tid til ansettelse"]["kritisk"]:
                st_tid = (FOLG_MED, f"{tregest['team']} over {TERSKLER['Tid til ansettelse']['kritisk']} dager")
        liste.append(dict(navn="Tid til ansettelse", verdi=f"{dager} dager",
                          endring=b.endring_antall(d_dager, "dager", "dag"),
                          status=st_tid,
                          ekstra=f"Median av {rn['antall']} ansettelser.{tregest_tekst}",
                          kortnavn="tid til ansettelse", sammenligning="fjor",
                          side="Rekruttering"))
    return liste


# =============================================================================
# INNSIKTER («Viktigste innsikter»)
# =============================================================================
# Hver innsikt: tittel, tekst, merknad (valgfri), neste_steg (forslag), lenker
# [(sidenavn, team eller None)], alvor (høyere = viktigere).

MAKS_INNSIKTER = 5


def innsikter(ansatte, fravaer, engasjement, plan, nokkeltall_liste=None, samtaler=None):
    start, slutt = b.FASTE_PERIODER["Siste 12 mnd"]
    js, je = b.samme_periode_i_fjor(start, slutt)
    siste = b.kvartaler_i_perioden(start, slutt)[-1]
    fjor_k = b.kvartal_minus(siste, 4)
    liste = []

    # --- Regel 1: fravær og engasjement per team ---------------------------------
    for team in b.TEAM:
        a_team = ansatte[ansatte["team"] == team]
        deler, lenker, alvor, lav_svar = [], [], 0, False
        tittel_deler = []

        # Fravær – bare team med minst 5 ansatte (samme femregel som siden)
        if b.snitt_ansatte(a_team, start, slutt) >= b.MIN_GRUPPE:
            f_team = fravaer[fravaer["team"] == team]
            naa, fjor = b.sykefravaer(f_team, start, slutt), b.sykefravaer(f_team, js, je)
            # Regelen bruker de avrundede tallene som vises (2 desimaler, endringen 1 som pilen)
            fravaer_pp = _prosentpoeng(naa["total_rate"], 2)
            endring_pp = _prosentpoeng(naa["total_rate"] - fjor["total_rate"], 1)
            over_maal = fravaer_pp > _prosentpoeng(b.SYKEFRAVAER_MAL, 0)
            if over_maal or endring_pp >= 1:
                deler.append(f"Sykefravær {b.prosent(naa['total_rate'], 2)} "
                             f"({b.endring_pp(naa['total_rate'], fjor['total_rate']).replace('-', '−')} mot i fjor), "
                             f"langtid {b.prosent(naa['langtid_rate'], 2)}"
                             + (", over det interne målet på 6 %" if over_maal else ""))
                tittel_deler.append("høyt sykefravær")
                lenker.append(("Sykefravær", team))
                alvor += 2 if over_maal else 1

        # eNPS – bare når teamet har minst 5 svar i begge kvartalene (femregelen)
        e_team = engasjement[engasjement["team"] == team]
        en = b.enps_samlet(e_team[e_team["kvartal"] == siste])
        ej = b.enps_samlet(e_team[e_team["kvartal"] == fjor_k])
        # Samme avrunding som visningen (eNPS vises som hele poeng)
        if en and ej and (b.avrund(en["enps"]) < 0 or b.avrund(en["enps"] - ej["enps"]) <= -10):
            lav_svar = en["svarandel"] < b.LAV_SVARANDEL
            fall = b.avrund(en["enps"] - ej["enps"])
            deler.append(f"eNPS {b.enps_tekst(en['enps'])} ({b.fortegn(fall)} poeng mot {fjor_k}), "
                         f"{en['svar']} av {en['invitert']} svarte "
                         f"({b.prosent(en['svarandel'], 0)}{', lav' if lav_svar else ''})")
            tittel_deler.append("fallende engasjement")
            lenker.append(("Engasjement", team))
            alvor += 2 if en["enps"] < 0 else 1

        if deler:
            merknader = []
            if len(deler) == 2:
                merknader.append(b.KOBLING_MERKNAD)
            if lav_svar:
                merknader.append("Lav svarandel kan bety at det reelle engasjementet er lavere "
                                 "(frafallsskjevhet).")
            liste.append(dict(
                tittel=f"{team.capitalize()}: {' og '.join(tittel_deler)}",
                tekst=". ".join(deler) + ".",
                merknad=" ".join(merknader) or None,
                neste_steg="Samtale med teamleder om arbeidsbelastning, og systematisk "
                           "oppfølging av langtidssykmeldte.",
                lenker=lenker, alvor=alvor + 1,
            ))

    # --- Regel 2: bemanning – team med over 5 % avvik --------------------------------
    bt = b.bemanning_per_team(ansatte, plan, start, slutt)
    for _, r in bt[bt["markert"]].iterrows():
        grad = r["faktisk"] / r["plan"]
        tekst = (f"{int(r['faktisk'])} av {int(r['plan'])} planlagte ({b.fortegn(int(r['avvik']))}, "
                 f"bemanningsgrad {b.prosent(grad)}).")
        if r["avvik"] < 0 and pd.notna(r["tiltredelse_median"]):  # skjult under 5
            dager = b.avrund(r["tiltredelse_median"])
            tekst += f" Median tid til tiltredelse {dager} dager (n = {int(r['tiltredelse_n'])})."
            neste = (f"Lys ut tidligere – med {dager} dager til tiltredelse trenger "
                     f"bemanningsplanen ca. {b.avrund(dager / 30)} måneders ledetid.")
        else:
            neste = "Gå gjennom om bemanningsplanen for teamet er oppdatert."
        liste.append(dict(
            tittel=f"{r['team'].capitalize()}: {'under' if r['avvik'] < 0 else 'over'} bemanningsplanen",
            tekst=tekst, merknad=None, neste_steg=neste,
            lenker=[("Bemanning", r["team"])],
            alvor=3 if abs(r["avvik"]) / r["plan"] > 0.10 else 2,
        ))

    # --- Regel 3: turnover – høy frivillig turnover i et team ---------------------------
    utenfor = b.utenfor_turnoverfordeling(ansatte, b.TEAM)
    selskap = b.turnover(ansatte[~ansatte["team"].isin(utenfor)], start, slutt)
    # 1:1 med lederen for hele selskapet (små team holdes utenfor, som på Utvikling-siden)
    utenfor_s = b.utenfor_sykefravaer(ansatte, b.TEAM)
    s_selskap = (b.en_til_en(ansatte[~ansatte["team"].isin(utenfor_s)], samtaler, start, slutt)
                 if samtaler is not None else None)
    for team in b.TEAM:
        t = b.turnover(ansatte[ansatte["team"] == team], start, slutt)
        # Fordelingen er bare synlig med minst 5 ansatte og minst 5 avganger
        if t["snitt_ansatte"] < b.MIN_GRUPPE or t["avganger"] < b.MIN_GRUPPE:
            continue
        if t["frivillig_rate"] >= 0.15 and t["frivillig_rate"] >= 1.5 * selskap["frivillig_rate"]:
            innsikt = dict(
                tittel=f"{team.capitalize()}: høy frivillig turnover",
                tekst=(f"Frivillig turnover {b.prosent(t['frivillig_rate'])} "
                       f"({t['frivillig']} av snitt {b.avrund(t['snitt_ansatte'])} ansatte) mot "
                       f"{b.prosent(selskap['frivillig_rate'])} for "
                       f"{b.med_unntak('hele selskapet', utenfor)}. "
                       f"{t['uønsket']} av avgangene var uønsket."),
                merknad=None,
                neste_steg="Sluttsamtaler og gjennomgang av rekrutteringsmetode i teamet.",
                lenker=[("Turnover", team)], alvor=2,
            )
            # Lite jevnlig oppfølging i samme team? (under 60 % og minst 20 pp under selskapet)
            s_team = (b.en_til_en(ansatte[ansatte["team"] == team], samtaler, start, slutt)
                      if samtaler is not None else None)
            if s_team and s_selskap and s_team["andel_jevnlige"] < 0.60 \
                    and s_team["andel_jevnlige"] <= s_selskap["andel_jevnlige"] - 0.20:
                innsikt["tittel"] = f"{team.capitalize()}: høy frivillig turnover og lite oppfølging"
                innsikt["tekst"] += (
                    f" Bare {b.prosent_med_n(s_team['jevnlige'], s_team['n'])} har jevnlige 1:1 "
                    f"med lederen, mot {b.prosent(s_selskap['andel_jevnlige'], 0)} for "
                    f"{b.med_unntak('hele selskapet', utenfor_s)}.")
                innsikt["merknad"] = b.OPPFOLGING_TURNOVER_MERKNAD
                innsikt["neste_steg"] = ("Sluttsamtaler, og avtal faste 1:1 mellom teamleder og "
                                         "hver ansatt i teamet.")
                innsikt["lenker"] = [("Turnover", team), ("Utvikling", team)]
            liste.append(innsikt)

    # --- Regel 4: rekruttering – tidlig turnover etter metode -----------------------------
    # Samme tall som Rekruttering-siden viser for hele selskapet (med sekundær prikking)
    kv = b.kvalitet_per_nivaa_prikket(ansatte, slutt).set_index("gruppe")
    u, s = kv.loc["ustrukturert"], kv.loc["strukturert intervju alene"]
    if pd.notna(u["tidlig_antall"]) and pd.notna(s["tidlig_antall"]):
        andel_u = u["tidlig_antall"] / u["tidlig_n"]
        andel_s = s["tidlig_antall"] / s["tidlig_n"]
        if andel_u - andel_s >= 0.10:
            n_min = int(min(u["tidlig_n"], s["tidlig_n"]))
            liste.append(dict(
                tittel="Strukturert rekruttering: lavere tidlig turnover",
                tekst=(f"Tidlig turnover (slutter innen 12 mnd): "
                       f"{b.prosent_med_n(int(u['tidlig_antall']), int(u['tidlig_n']))} ved "
                       f"ustrukturert rekruttering mot "
                       f"{b.prosent_med_n(int(s['tidlig_antall']), int(s['tidlig_n']))} med "
                       f"strukturert intervju."),
                merknad=(f"Sammenheng, ikke nødvendigvis årsak. Peker i riktig retning, men "
                         f"grunnlaget er lite (n = {n_min}). Følg utviklingen – metodevalget "
                         f"støttes uansett av forskningen."),
                neste_steg="Fortsett å øke andelen strukturerte prosesser.",
                lenker=[("Rekruttering", None)], alvor=1,
            ))

    # --- Regel 5: kritiske nøkkeltall for hele selskapet -----------------------------------
    for k in nokkeltall_liste or []:
        # Kort som bare følger et annet kort (kostnadene) gir ingen egen innsikt. Ellers
        # kom samme avvik to ganger, med teksten «Grensen for kritisk er følger …».
        if k["status"][0] == KRITISK and not k["status"][1].startswith("følger"):
            liste.append(dict(
                tittel=f"{k['navn']} er kritisk",
                tekst=f"{k['navn']} er {k['verdi']}. Grensen for kritisk er {k['status'][1]}.",
                merknad=None,
                neste_steg="Se detaljene for å finne hvilke team som driver tallet.",
                lenker=[(k["side"], None)], alvor=4,
            ))

    # Viktigste først (stabil sortering beholder rekkefølgen ved likt alvor)
    liste.sort(key=lambda i: -i["alvor"])
    return liste[:MAKS_INNSIKTER]

# Selskapsnotat: bygger bare på offentlige tall, alle tall har kilde, kildene står i teksten,
# tekstreglene holdes, og eksempelet kjører helt uten nett. Reglene står i CLAUDE.md
# («Selskapsnotat»).

import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import pandas as pd
import pytest

import beregninger as b
import lederbrief as lb
import selskapsnotat as sn

PROSJEKT = Path(__file__).resolve().parent.parent
EKSEMPEL_MD = PROSJEKT / "notater" / "eksempel-nordvind-logistikk-as.md"
EKSEMPEL_HTML = PROSJEKT / "notater" / "eksempel-nordvind-logistikk-as.html"


def _ingen_nett(*args, **kwargs):
    raise AssertionError("notatet prøvde å bruke nettet")


@pytest.fixture(scope="module")
def g():
    """Eksempelet, laget med nettet «koblet fra»: både vår egen hent_json og urllib stoppes."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(sn, "hent_json", _ingen_nett)
        mp.setattr(urllib.request, "urlopen", _ingen_nett)
        yield sn.eksempel()


@pytest.fixture(scope="module")
def tekst(g):
    return sn.som_markdown(g)


# --- Eksempelet kjører offline ------------------------------------------------------------------

def test_eksempelet_kjorer_offline_og_gaar_gjennom_kontrollene(g):
    assert sn.kontroller(g) == []


def test_skriptet_lager_eksempelnotatet(tmp_path):
    svar = subprocess.run([sys.executable, str(PROSJEKT / "lag_selskapsnotat.py"), "--eksempel",
                           "--mappe", str(tmp_path)], cwd=tmp_path, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=120)
    assert svar.returncode == 0, svar.stderr
    assert "Kontrollene fant ingen problemer" in svar.stdout
    assert (tmp_path / "eksempel-nordvind-logistikk-as.md").exists()
    assert (tmp_path / "eksempel-nordvind-logistikk-as.html").exists()


def test_eksempelnotatet_i_repoet_er_oppdatert(g, tekst):
    """Filene i notater/ er laget av dagens kode og dagens tabeller. Stemmer det ikke, kjør
    python lag_selskapsnotat.py --eksempel på nytt."""
    assert EKSEMPEL_MD.read_text(encoding="utf-8") == tekst
    assert EKSEMPEL_HTML.read_text(encoding="utf-8") == sn.som_html(g)


def test_eksempelselskapet_er_oppdiktet(g):
    svar = json.loads((sn.EKSEMPELMAPPE / "enhet.json").read_text(encoding="utf-8"))
    # Ekte organisasjonsnumre begynner på 8 eller 9, så dette kan ikke være et ekte selskap
    assert svar["organisasjonsnummer"][0] not in "89"
    assert "oppdiktet" in svar["_merknad"].lower()
    assert g["enhet"]["navn"] == "Nordvind Logistikk AS"
    assert "oppdiktet" in g["aarsberetning"]["kilde"].lower()


# --- Alle tall har kilde -------------------------------------------------------------------------

def test_alle_tall_i_notatet_har_kilde(g, tekst):
    ukjente = {t for t in lb.TALL.findall(tekst) if t not in sn.lovlige_tall(g)}
    assert not ukjente, ukjente


def test_naeringstallene_er_lest_rett_ut_av_tabellene(g):
    """Som et XOPPSLAG mot riktig rad i CSV-filen: samme gruppe, type og periode."""
    tabeller = sn.les_tabeller()
    n = g["naering"]

    def rad(navn, **filter_):
        t = tabeller[navn]
        for kolonne, onsket in filter_.items():
            t = t[t[kolonne] == onsket]
        assert len(t) == 1, (navn, filter_, len(t))
        return float(t["verdi"].iloc[0])

    verdi, kode, _ = n["kvartal_alt"]
    assert kode == "49"  # Landtransport og rørtransport (49.410 Godstransport på vei)
    assert verdi == rad("sykefravaer_kvartal", NACE2007="49", Sykefraver2="Alt", Tid=n["kvartal"])
    assert n["kvartal_i_fjor_alt"][0] == rad("sykefravaer_kvartal", NACE2007="49", Sykefraver2="Alt",
                                             Tid=sn.samme_kvartal_i_fjor(n["kvartal"]))
    verdi, kode, _ = n["aar_alt"]
    assert kode == "49-53"  # Transport og lagring: årstabellen har bare 17 grupper
    assert verdi == rad("sykefravaer_aar", NACE2007="49-53", Sykefraver2="Alt", Tid=n["aar"])
    assert n["aar_egenmeldt"][0] == rad("sykefravaer_aar", NACE2007="49-53", Sykefraver2="E", Tid=n["aar"])
    verdi, kode, _ = n["maanedslonn"]
    assert kode == "49"
    assert verdi == rad("lonn_kvartal", NACE2007="49", ContentsCode="GjMndlonn", Tid=n["lonnskvartal"])
    assert n["kvartal_alle_naeringer"][1] == "A-U" and n["aar_alle_naeringer"][1] == "00-99"


def test_regnestykket_er_ren_aritmetikk(g):
    """Samme formler som dashbordet: 260 arbeidsdager i et årsverk og 75 % av en årslønn per avgang."""
    r, aar_b, n = g["regnestykke"], g["aarsberetning"], g["naering"]
    lonn, personer = n["maanedslonn"][0], aar_b["aarsverk"]
    assert r["grunnlag"] == "aarsverk" and r["personer"] == personer
    assert r["per_avgang_kr"] == pytest.approx(0.75 * 12 * lonn)
    assert r["pp_dagsverk"] == pytest.approx(personer * 260 / 100)
    assert r["pp_kr"] == pytest.approx(personer * 260 / 100 * lonn * 12 / 260)
    assert r["egenmeldt_dagsverk"] == pytest.approx(personer * 260 * n["aar_egenmeldt"][0] / 100)
    assert r["egenmeldt_kr"] == pytest.approx(r["egenmeldt_dagsverk"] * lonn * 12 / 260)
    assert r["forskjell_pp"] == b.avrund(aar_b["sykefravaer_prosent"] - n["aar_alt"][0], 1)
    assert r["forskjell_kr"] == pytest.approx(personer * 260 * r["forskjell_pp"] / 100 * lonn * 12 / 260)
    assert r["avganger"] is None  # turnover står ikke i eksempelets årsberetning


def test_regnestykket_med_turnover_og_uten_aarsverk(g):
    """Uten årsverk brukes antall ansatte fra Enhetsregisteret; med turnover regnes avganger."""
    aar_b = {"kilde": "Årsberetning 2025, side 3", "aar": 2025, "turnover_prosent": 10.0}
    r = sn.regnestykke(g["enhet"], aar_b, g["naering"])
    assert r["grunnlag"] == "ansatte" and r["personer"] == g["enhet"]["antall_ansatte"]
    assert r["avganger"] == b.avrund(0.10 * g["enhet"]["antall_ansatte"])
    assert r["avganger_kr"] == pytest.approx(r["avganger"] * r["per_avgang_kr"])
    assert r["forskjell_pp"] is None
    g2 = {**g, "aarsberetning": aar_b, "regnestykke": r}
    assert sn.kontroller(g2) == []
    md = sn.som_markdown(g2)
    assert "Med turnover på 10,0 % fra årsberetningen for 2025" in md
    assert "regnet som om alle var i full stilling" in md
    assert "Selskapets eget sykefravær er ikke oppgitt" in md


def test_uten_ansatte_og_uten_aarsberetning_blir_det_ikke_regnestykke(g):
    enhet = {**g["enhet"], "antall_ansatte": None}  # Enhetsregisteret oppgir ikke tallet under 5
    aar_b = {"kilde": "årsberetningen (ikke lest ennå)"}
    assert sn.regnestykke(enhet, aar_b, g["naering"]) is None
    g2 = {**g, "enhet": enhet, "aarsberetning": aar_b, "regnestykke": None}
    md = sn.som_markdown(g2)
    assert "uten registrert antall ansatte" in md and "så det er ikke med" in md
    assert "ingen tall skrevet inn" in md
    assert sn.kontroller(g2) == []


# --- Kildene står i teksten -----------------------------------------------------------------------

def test_kildene_staar_i_teksten(g, tekst):
    for info in g["kilder"]["tabeller"].values():
        assert f"SSB, tabell {info['tabell']}: {info['tittel']}" in tekst
        assert info["url"] in tekst
        assert f"lastet ned {lb.dato(info['lastet_ned'])}" in tekst
        assert f"oppdatert av SSB {lb.dato(info['oppdatert'])}" in tekst
        assert f"Siste periode {info['siste_periode']}" in tekst
    assert "Enhetsregisteret (Brønnøysundregistrene), åpne data" in tekst
    assert "hentet 21.10.2026" in tekst  # EKSEMPEL_DATO
    assert g["aarsberetning"]["kilde"] in tekst
    assert sn.DASHBORD_LENKE in tekst
    assert tekst.rstrip().endswith(f"*{sn.BUNNLINJE}*")
    assert "ikke regnet ut på samme måte" in tekst and "regnestykke, ikke prognose" in tekst


def test_kilder_json_stemmer_med_csv_filene_og_readme():
    kilder = sn.les_kilder()
    assert set(kilder["tabeller"]) == {"sykefravaer_kvartal", "sykefravaer_aar", "lonn_kvartal"}
    readme = (sn.MAPPE / "README.md").read_text(encoding="utf-8")
    for navn, info in kilder["tabeller"].items():
        t = pd.read_csv(sn.MAPPE / info["fil"], dtype=str, keep_default_na=False)
        assert info["siste_periode"] == t["Tid"].max()
        assert info["tabell"] == sn.TABELLER[navn]["tabell"]
        assert info["api_url"].startswith(sn.SSB_API.format(tabell=info["tabell"]))
        assert info["lastet_ned"] and info["oppdatert"] and info["tittel"]
        assert not info["tittel"].startswith(info["tabell"])
        assert info["tabell"] in readme and info["siste_periode"] in readme
        assert lb.dato(info["lastet_ned"]) in readme
    assert "CC BY 4.0" in readme and "NLOD" in readme


def test_ssb_adressen_har_hele_sporringen():
    url = sn.ssb_url("12440", {"Kjonn": "0", "NACE2007": "*", "Tid": "top(5)"})
    assert url.startswith("https://data.ssb.no/api/pxwebapi/v2/tables/12440/data?lang=no&outputFormat=json-stat2")
    assert "valueCodes%5BNACE2007%5D=*" in url and "valueCodes%5BTid%5D=top(5)" in url


def test_jsonstat_til_tabell():
    """Et lite SSB-svar (JSON-stat2) pakkes ut til én rad per tall, i SSBs rekkefølge."""
    data = {"id": ["NACE2007", "Tid"], "size": [2, 2],
            "dimension": {"NACE2007": {"category": {"index": {"J": 1, "A-U": 0},
                                                    "label": {"J": "Informasjon og kommunikasjon",
                                                              "A-U": "Alle næringer"}}},
                          "Tid": {"category": {"index": {"2026K1": 0, "2026K2": 1},
                                               "label": {"2026K1": "2026K1", "2026K2": "2026K2"}}}},
            "value": [6.6, 6.4, None, 4.5]}
    t = sn.jsonstat_til_tabell(data)
    assert list(t["NACE2007"]) == ["A-U", "A-U", "J", "J"]
    assert list(t["NACE2007_tekst"])[2] == "Informasjon og kommunikasjon"
    assert list(t["Tid"]) == ["2026K1", "2026K2"] * 2
    assert list(t["verdi"])[:2] == [6.6, 6.4] and pd.isna(t["verdi"][2])


# --- Næringsgruppene -----------------------------------------------------------------------------

def test_tolk_ssb_kode():
    assert sn.tolk_ssb_kode("61-63") == ({61, 62, 63}, set())
    assert sn.tolk_ssb_kode("D-E") == (set(range(35, 40)), set())
    assert sn.tolk_ssb_kode("05_07_08_09.9") == ({5, 7, 8}, {"09.9"})
    assert sn.tolk_ssb_kode("06.1-06.2_09.1") == (set(), {"06.1", "06.2", "09.1"})
    assert sn.tolk_ssb_kode("30.1b") == (set(), {"30.1"})
    assert sn.tolk_ssb_kode("A-U")[0] >= {1, 33, 62, 99}
    assert sn.hovedomraade("62.010") == "J" and sn.hovedomraade("49.410") == "H"


@pytest.mark.parametrize("nace, kvartal, aar, lonn", [
    ("62.010", "61-63", "58-63", "62"),         # programmering: IKT-virksomhet
    ("49.410", "49", "49-53", "49"),            # godstransport på vei
    ("84.110", "O", "84", "84"),                # offentlig administrasjon: bare hovedområdet i 12440
    ("70.220", "69-71", "68-75", "70"),         # bedriftsrådgivning
    ("09.900", "05_07_08_09.9", "05-09", "09"), # tjenester til bergverk: gruppenivå
])
def test_naeringskoden_finner_den_mest_spesifikke_gruppen(nace, kvartal, aar, lonn):
    tabeller = sn.les_tabeller()

    def forste(navn):
        return sn.finn_grupper(nace, tabeller[navn], sn.TABELLER[navn]["alle"])[0][0]

    assert forste("sykefravaer_kvartal") == kvartal
    assert forste("sykefravaer_aar") == aar
    assert forste("lonn_kvartal") == lonn


def test_alle_naeringer_er_siste_utvei():
    tabeller = sn.les_tabeller()
    grupper = sn.finn_grupper("62.010", tabeller["sykefravaer_kvartal"], "A-U")
    assert [kode for kode, _ in grupper] == ["61-63", "J", "A-U"]
    assert grupper[-1] == ("A-U", "Alle næringer")


def test_verdi_gaar_videre_naar_tallet_er_holdt_tilbake():
    t = pd.DataFrame({"NACE2007": ["62", "58-63"], "Tid": ["2026K2", "2026K2"],
                      "verdi": [float("nan"), 60000.0]})
    grupper = [("62", "IT-tjenester"), ("58-63", "Informasjon og kommunikasjon")]
    assert sn.verdi(t, grupper, Tid="2026K2") == (60000.0, "58-63", "Informasjon og kommunikasjon")
    assert sn.verdi(t, grupper, Tid="2025K1") == (None, None, None)


# --- Enhetsregisteret ----------------------------------------------------------------------------

def test_enhet_fra_svar_plukker_bare_det_notatet_trenger():
    svar = {"organisasjonsnummer": "123456785", "navn": "FJORDLYS TECH AS",
            "organisasjonsform": {"kode": "AS", "beskrivelse": "Aksjeselskap"},
            "naeringskode1": {"kode": "62.010", "beskrivelse": "Programmeringstjenester"},
            "antallAnsatte": 230, "registreringsdatoAntallAnsatteEnhetsregisteret": "2026-10-01",
            "forretningsadresse": {"adresse": ["Gate 1"]}, "epostadresse": "post@eksempel.no"}
    enhet = sn.enhet_fra_svar(svar, hentet=sn.EKSEMPEL_DATO)
    assert enhet["navn"] == "Fjordlys Tech AS" and enhet["nace_kode"] == "62.010"
    assert enhet["antall_ansatte"] == 230 and enhet["hentet"] == "2026-10-21"
    assert "adresse" not in json.dumps(enhet) and "epost" not in json.dumps(enhet)
    # 0-4 ansatte: Enhetsregisteret oppgir ikke tallet
    assert sn.enhet_fra_svar({**svar, "antallAnsatte": None})["antall_ansatte"] is None


def test_pent_navn():
    assert sn.pent_navn("NORDVIND LOGISTIKK AS") == "Nordvind Logistikk AS"
    assert sn.pent_navn("FJORDLYS TECH ASA") == "Fjordlys Tech ASA"


def test_hent_enhet_krever_9_sifre(monkeypatch):
    monkeypatch.setattr(sn, "hent_json", _ingen_nett)
    with pytest.raises(SystemExit):
        sn.hent_enhet("12345")


# --- Tekstreglene og HTML ------------------------------------------------------------------------

def test_tekstreglene_holdes(g, tekst):
    for t in (tekst, sn.som_html(g)):
        assert chr(0x2014) not in t  # lang tankestrek
        assert "·" not in t
        assert not lb.INTERVALL.search(t)
        assert not lb.A_ENDINGER.search(t)
        assert not re.search(r"(^|[\s(])-\d", t)


def test_html_er_selvstendig_og_i_samme_stil_som_lederbriefen(g):
    side = sn.som_html(g)
    assert side.startswith("<!doctype html>") and "<meta charset='utf-8'>" in side
    assert "<title>Tre spørsmål til Nordvind Logistikk AS</title>" in side
    assert lb.HTML_STIL in side and "<script" not in side
    assert "http" not in side.split("<body>")[0]  # ingenting hentes fra nettet
    assert f"<a href='{sn.DASHBORD_LENKE}'>" in side
    assert sn.BUNNLINJE in side and "<ol><li>" in side


def test_kontrollene_fanger_feil(g, monkeypatch):
    monkeypatch.setattr(sn, "AVSENDER", "Tania Næss, 99 år")
    assert any("tall uten kilde: 99" in p for p in sn.kontroller(g))
    monkeypatch.setattr(sn, "AVSENDER", "Tania Næss, se «pila»")
    assert any("a-ending" in p for p in sn.kontroller(g))
    monkeypatch.setattr(sn, "AVSENDER", "Tania " + chr(0x2014) + " Næss")
    assert any("lang tankestrek" in p for p in sn.kontroller(g))
    monkeypatch.setattr(sn, "BUNNLINJE", "Notatet bygger bare på offentlige tall.")
    assert any("enkeltpersoner mangler" in p for p in sn.kontroller(g))


# --- Dokumentasjon og repo -----------------------------------------------------------------------

def test_dokumentert_i_readme_og_claude_md():
    readme = (PROSJEKT / "README.md").read_text(encoding="utf-8")
    assert "python lag_selskapsnotat.py --eksempel" in readme
    assert readme.index("**Selskapsnotat på fem minutter") > readme.index("## Slik kan dette tas i bruk hos dere")
    claude = (PROSJEKT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "## Selskapsnotat" in claude
    seksjon = claude.split("## Selskapsnotat")[1].split("\n## ")[0]
    for regel in ("Bare offentlige tall", "Kilde alltid", "Ingen påstander om selskapet",
                  "Ingen personopplysninger"):
        assert regel in seksjon, regel


def test_ekte_notater_holdes_utenfor_repoet():
    gitignore = (PROSJEKT / ".gitignore").read_text(encoding="utf-8")
    assert "notater/*" in gitignore and "!notater/eksempel-*" in gitignore

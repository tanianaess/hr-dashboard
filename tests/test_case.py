# Eksempelsiden «fra funn til tiltak» (sider/7_Case.py): teksten bygger på at salg skiller
# seg ut. Feiler hvis dataene endres så teksten ikke lenger stemmer.

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import beregninger as b
import innsikter as i
from filtre import CASE_SIDE, SIDER

PROSJEKT = Path(__file__).resolve().parent.parent
TEAM = i.CASE_TEAM


@pytest.fixture(scope="module")
def tall(ansatte):
    start, slutt = b.FASTE_PERIODER["Siste 12 mnd"]
    turnover = b.turnover_per_team(ansatte, start, slutt).set_index("team")
    kompetanse = b.kompetanse_per_team(ansatte, b.les_opplaering(), b.les_en_til_en(),
                                       b.les_stillingsendringer(), start, slutt).set_index("team")
    utenfor = b.utenfor_turnoverfordeling(ansatte, b.TEAM)
    selskap = b.turnover(ansatte[~ansatte["team"].isin(utenfor)], start, slutt)
    return turnover, kompetanse, selskap


def test_salg_har_hoyest_frivillig_turnover(tall):
    turnover, _, _ = tall
    synlige = turnover["frivillig_rate"].dropna()  # skjulte team (femregelen) er ikke med
    assert TEAM in synlige and synlige.idxmax() == TEAM, synlige


def test_salg_har_lavest_andel_jevnlige_1til1(tall):
    _, kompetanse, _ = tall
    synlige = kompetanse["andel_jevnlige"].dropna()
    assert TEAM in synlige and synlige.idxmin() == TEAM, synlige


def test_salg_har_minst_opplaering(tall):
    # «minst opplæring og oppfølging» i Kort fortalt
    _, kompetanse, _ = tall
    synlige = kompetanse["timer_per_ansatt"].dropna()
    assert TEAM in synlige and synlige.idxmin() == TEAM, synlige


def test_forhold_tekst():
    # Regnes på de viste (avrundede) prosentene
    assert i.forhold_tekst(0.207, 0.103) == "dobbelt så høy"      # 20,7 / 10,3 = 2,01
    assert i.forhold_tekst(0.19, 0.103) == "nesten dobbelt så høy"  # 1,84
    assert i.forhold_tekst(0.23, 0.103) == "over dobbelt så høy"    # 2,23
    assert i.forhold_tekst(0.165, 0.103) == "1,6 ganger så høy"


def test_salg_minst_halvannen_gang_selskapet(tall):
    turnover, _, selskap = tall
    assert turnover.loc[TEAM, "frivillig_rate"] >= 1.5 * selskap["frivillig_rate"]


def test_siden_viser_tallene_og_ingen_lonn(tall):
    at = AppTest.from_file(str(PROSJEKT / SIDER[CASE_SIDE]), default_timeout=180)
    at.run()
    assert not at.exception, at.exception
    assert not at.sidebar.selectbox and not at.sidebar.multiselect  # ingen filter: én fast visning
    tekst = " ".join([*(m.value for m in at.markdown), *(c.value for c in at.caption),
                      *(x.value for x in at.info)])
    assert "Analysen og tiltakene er mine vurderinger" in tekst
    assert "Kort fortalt" in tekst
    turnover, _, selskap = tall
    forhold = i.forhold_tekst(turnover.loc[TEAM, "frivillig_rate"], selskap["frivillig_rate"])
    assert f"salg har {forhold} frivillig turnover som selskapet" in tekst
    assert all(len(str(m.value)) <= 12 for m in at.metric)  # KPI-verdier kuttes ikke
    assert len(at.metric) == 4
    assert " kr" not in tekst and "lønn" not in tekst.lower()  # lønn vises aldri per team
    assert "·" not in tekst


def test_innsikten_om_salg_lenker_til_eksempelet(ansatte, fravaer, engasjement, plan):
    liste = i.innsikter(ansatte, fravaer, engasjement, plan, samtaler=b.les_en_til_en())
    salg = [x for x in liste if x["tittel"].lower().startswith(TEAM)]
    assert salg and all(x.get("case") for x in salg)
    assert not any(x.get("case") for x in liste if x not in salg)

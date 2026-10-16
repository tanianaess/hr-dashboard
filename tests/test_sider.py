# Sidene: kjører uten feil for alle filtervalg, også når filteret endres.
# Bruker Streamlits AppTest, som kjører sidene uten nettleser.

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import beregninger as b

PROSJEKT = Path(__file__).resolve().parent.parent
SENSITIVE = ["sider/1_Turnover.py", "sider/2_Sykefravaer.py", "sider/3_Rekruttering.py",
             "sider/5_Engasjement.py", "sider/6_Utvikling.py"]
FRIE = ["sider/4_Bemanning.py"]


def kjor(side):
    at = AppTest.from_file(str(PROSJEKT / side), default_timeout=180)
    at.run()
    return at


@pytest.mark.parametrize("side", SENSITIVE)
@pytest.mark.parametrize("periode", list(b.FASTE_PERIODER))
@pytest.mark.parametrize("team", ["Hele selskapet", "kundesuksess", "ledergruppen"])
def test_sensitive_sider_alle_valg(side, periode, team):
    at = kjor(side)
    at.sidebar.selectbox(key="filter_periode").set_value(periode).run()
    at.sidebar.selectbox(key="filter_team").set_value(team).run()
    assert not at.exception, at.exception


@pytest.mark.parametrize("side", FRIE)
def test_fritt_filter_kan_endres(side):
    # K1: siden krasjet når filteret ble endret (glideren mistet intervallet)
    at = kjor(side)
    at.sidebar.multiselect[0].set_value(["teknologi", "salg"]).run()
    assert not at.exception, at.exception
    at.sidebar.select_slider[0].set_value(("2026-01", "2026-09")).run()
    assert not at.exception, at.exception


def test_oversikt():
    at = kjor("app.py")
    assert not at.exception
    # Med to faste, ikke-overlappende perioder trenger ingen team å holdes utenfor
    # turnoverfordelingen lenger (før: fem team), så uønsket turnover gjelder alle.
    # Sykefravær er fortsatt uten ledergruppen (sekundær prikking).
    assert [m.value for m in at.metric] == [
        "14,3 %", "4,5 %", "17,8 mill. kr", "5,69 %", "3,3 mill. kr", "+15", "−13", "36 dager"]


@pytest.mark.parametrize("side", ["app.py", *SENSITIVE, *FRIE])
def test_negative_tall_har_minustegn(side):
    # Viste tall skal bruke minustegn (−), ikke bindestrek. Pilene (delta) er unntatt,
    # fordi Streamlit bruker bindestreken til å avgjøre retningen på pilen.
    at = kjor(side)
    tekster = [str(m.value) for m in at.metric]
    for tabell in at.dataframe:
        tekster += [str(v) for v in tabell.value.to_numpy().ravel()]
    feil = [t for t in tekster if re.search(r"(^|[\s(])-\d", t)]
    assert not feil, feil


def test_ingen_lang_tankestrek():
    filer = [*PROSJEKT.glob("*.py"), *PROSJEKT.glob("sider/*.py"), PROSJEKT / "README.md"]
    treff = [str(f.name) for f in filer if "—" in f.read_text(encoding="utf-8")]
    assert not treff, treff

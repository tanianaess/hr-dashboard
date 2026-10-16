# Kritisk gjennomgang 16.10.2026 (som HR-leder og økonomidirektør): kostnader i kroner,
# riktig sammenligning for sykefravær, like målepunkter, grå pil for små endringer, årsverk.

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import beregninger as b
import innsikter as i

PROSJEKT = Path(__file__).resolve().parent.parent


def kjor(side, periode=None, team=None):
    at = AppTest.from_file(str(PROSJEKT / side), default_timeout=180)
    at.run()
    if periode:
        at.sidebar.selectbox(key="filter_periode").set_value(periode).run()
    if team:
        at.sidebar.selectbox(key="filter_team").set_value(team).run()
    assert not at.exception, at.exception
    return at


# --- Grå pil for små endringer -------------------------------------------------------------

@pytest.mark.parametrize("tekst, vesentlig", [
    ("-0,1 pp", False), ("+1,0 pp", True), ("+3,1 pp", True),
    ("+2 dager", False), ("-6 dager", True), ("+4 poeng", False), ("-21 poeng", True),
    ("-0,7 timer", False), ("+0,1 mill. kr", False), ("+4,4 mill. kr", True),
])
def test_er_vesentlig(tekst, vesentlig):
    assert b.er_vesentlig(tekst) == vesentlig
    assert (b.pilfarge(tekst) != "off") == vesentlig


def test_sykefravaer_har_lavere_grense_og_lite_utvalg_gir_graa_pil():
    assert b.pilfarge("+0,3 pp", terskel=b.VESENTLIG_ENDRING_SYKEFRAVAER_PP) == "off"
    assert b.pilfarge("+0,6 pp", terskel=b.VESENTLIG_ENDRING_SYKEFRAVAER_PP) == "inverse"
    assert b.pilfarge("-19,9 pp", hoyere_er_bedre=True, vesentlig=False) == "off"


# --- Kostnader ----------------------------------------------------------------------------------

def test_erstatningskostnad_omfatter_alle_avganger(ansatte, siste_12):
    t = b.turnover(ansatte, *siste_12)
    assert t["lønn_avganger"] > t["lønn_uønsket"] > 0
    assert "lønn_avganger" not in b.turnover_per_team(ansatte, *siste_12).columns  # aldri per team


def test_fravaerskostnad(ansatte, fravaer, siste_12):
    kostnad = b.fravaerskostnad(ansatte, fravaer, *siste_12)
    korttid = b.fravaer_i_perioden(fravaer, *siste_12)["tapte_dagsverk_korttid"].sum()
    dagslonn = b.lonn_per_aarsverk(ansatte, *siste_12) / b.ARBEIDSDAGER_PER_AARSVERK
    assert kostnad == pytest.approx(korttid * dagslonn)
    assert b.millioner(kostnad).endswith("mill. kr")


def test_opplaering_tidskostnad(ansatte, siste_12):
    tid = b.opplaering_tidskostnad(ansatte, b.les_opplaering(), *siste_12)
    assert tid > 0


@pytest.mark.parametrize("side, team, tekst", [
    ("sider/2_Sykefravaer.py", "salg", "bare for hele selskapet"),
    ("sider/1_Turnover.py", "salg", "bare for hele selskapet"),
])
def test_lonnskostnader_bare_for_hele_selskapet(side, team, tekst):
    at = kjor(side, "Siste 12 mnd", team)
    assert any(tekst in x.value for x in at.info)


def test_utvikling_et_team_viser_bare_direkte_kostnad():
    at = kjor("sider/6_Utvikling.py", "Siste 12 mnd", "salg")
    etiketter = [m.label for m in at.metric]
    assert "Direkte kostnad per ansatt" in etiketter and "Kostnad per ansatt" not in etiketter


def test_forsiden_viser_kostnader_i_kroner():
    at = kjor("app.py")
    kort = {m.label: m.value for m in at.metric}
    assert kort["Erstatningskostnad"].endswith("mill. kr")
    assert kort["Fraværskostnad"].endswith("mill. kr")


# --- Sykefravær: referanse, ikke sammenligning --------------------------------------------------

def test_bransjetall_ikke_fylt_inn_uten_verifisering():
    assert b.SYKEFRAVAER_BRANSJE is None
    assert "ikke fylt inn" in b.SYKEFRAVAER_REFERANSE_MERKNAD


def test_sykefravaer_status_styres_av_internt_maal():
    at = kjor("sider/2_Sykefravaer.py")
    assert "Internt mål" in [m.label for m in at.metric]
    assert "Landssnitt 2025" not in [m.label for m in at.metric]


# --- Like målepunkter og årsverk -------------------------------------------------------------------

def test_tid_til_besatt_maales_til_samme_endepunkt(ansatte, siste_12):
    ekstern = b.tid_til_tiltredelse(ansatte, *siste_12)
    intern = b.intern_mobilitet(ansatte, b.les_stillingsendringer(), *siste_12)["median_dager_intern"]
    assert ekstern > b.rekruttering(ansatte, *siste_12)["median_dager"]  # inkluderer oppsigelsestid
    assert intern < ekstern


def test_aarsverk(ansatte, plan, siste_12):
    bt = b.bemanning_per_team(ansatte, plan, *siste_12)
    assert (bt["faktisk_aarsverk"] <= bt["faktisk"]).all()
    assert bt["faktisk_aarsverk"].sum() == pytest.approx(b.aarsverk_paa(ansatte, siste_12[1]))


def test_tid_til_ansettelse_viser_tregeste_team(ansatte, fravaer, engasjement, plan):
    kort = next(k for k in i.nokkeltall(ansatte, fravaer, engasjement, plan) if k["navn"] == "Tid til ansettelse")
    assert "Tregest: teknologi" in kort["ekstra"]


def test_toppen_viser_bare_selskapsnavnet():
    at = kjor("app.py")
    assert at.caption[0].value == "**Fjordlys Tech AS**"


def test_kortene_har_hele_setninger_og_felles_merknad(ansatte, fravaer, engasjement, plan):
    """Det som gjelder flere kort står én gang over kortene, ikke med prikker på hvert kort."""
    kort = i.nokkeltall(ansatte, fravaer, engasjement, plan)
    for k in kort:
        assert "·" not in k["ekstra"], k["navn"]
        assert "Minst" not in k["ekstra"]
        assert "Uten " not in k["ekstra"]
    tekst = i.felles_merknad(kort)
    assert "Pilene viser endring mot forrige 12 måneder for turnover" in tekst
    assert "mot samme periode i fjor for sykefravær" in tekst
    assert "Ledergruppen er holdt utenfor" in tekst

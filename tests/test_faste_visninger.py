# Punkt 2 fra kodegjennomgangen: sensitive tall vises bare i faste, ikke-overlappende
# visninger, og fritt filter brukes bare på tall som ikke er sensitive (se CLAUDE.md).

from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import beregninger as b
import filtre

PROSJEKT = Path(__file__).resolve().parent.parent


def kjor(side, periode=None, team=None):
    """Kjører en side, eventuelt med valgt periode og team i det begrensede filteret."""
    at = AppTest.from_file(str(PROSJEKT / side), default_timeout=180)
    at.run()
    if periode:
        at.sidebar.selectbox(key="filter_periode").set_value(periode).run()
    if team:
        at.sidebar.selectbox(key="filter_team").set_value(team).run()
    assert not at.exception, at.exception
    return at


# --- Faste, ikke-overlappende perioder ----------------------------------------------

def test_faste_perioder_overlapper_ikke():
    (s1, e1), (s2, e2) = sorted(b.FASTE_PERIODER.values())
    assert e1 + pd.Timedelta(days=1) == s2  # rett etter hverandre, ingen overlapp
    assert (s1, e2) == (b.DATA_FRA, b.DATA_TIL)
    for start, slutt in b.FASTE_PERIODER.values():
        assert len(b.maanedsslutter(start, slutt)) == 12


def test_sammenligninger_er_bare_de_faste_periodene():
    # Ingen sammenligningsperiode skal overlappe en fast periode delvis
    assert set(b.alle_sammenligningsperioder()) == set(b.FASTE_PERIODER.values())


def test_sensitive_sider_har_begrenset_filter():
    alle = {f"sider/{p.name}" for p in (PROSJEKT / "sider").glob("[1-9]_*.py")}
    assert alle - filtre.SENSITIVE_SIDER == {"sider/4_Bemanning.py"}


# --- Turnover: månedsgraf og kostnad --------------------------------------------------

def test_avganger_per_maaned_bare_totalen(ansatte, siste_12):
    per_maaned = b.avganger_per_maaned(ansatte, *siste_12)
    assert list(per_maaned.columns) == ["Avganger"]
    assert len(per_maaned) == 12
    assert per_maaned["Avganger"].sum() == b.turnover(ansatte, *siste_12)["avganger"]


def test_kostnad_bare_siste_12():
    assert b.er_siste_12(*b.FASTE_PERIODER["Siste 12 mnd"])
    assert not b.er_siste_12(*b.FASTE_PERIODER["Forrige 12 mnd"])


def test_millioner_rundes_grovt():
    assert b.millioner(5_580_000) == "5,6 mill. kr"
    assert b.millioner(3_450_000) == "3,5 mill. kr"  # 5 rundes opp, som i Excel


@pytest.mark.parametrize("periode, team, vises", [
    ("Siste 12 mnd", None, True),
    ("Forrige 12 mnd", None, False),
    ("Siste 12 mnd", "salg", False),
])
def test_turnoverside_kostnad(periode, team, vises):
    at = kjor("sider/1_Turnover.py", periode, team)
    kostnad = [m.value for m in at.metric if m.label == "Anslått kostnad"]
    assert bool(kostnad) == vises
    if vises:
        assert kostnad[0].endswith("mill. kr")


def test_endring_millioner_regnes_paa_avrundede_tall():
    assert b.endring_millioner(5_580_000, 2_467_500) == "+3,1 mill. kr"  # 5,6 − 2,5
    assert b.endring_millioner(2_467_500, 5_580_000) == "-3,1 mill. kr"
    assert b.endring_millioner(5_560_000, 5_640_000) == "±0,0 mill. kr"  # begge 5,6


def test_forsiden_kostnad_mot_forrige_12():
    at = kjor("app.py")
    kort = next(m for m in at.metric if m.label == "Turnoverkostnad")
    assert kort.value == "5,6 mill. kr"
    assert kort.delta == "+3,1 mill. kr"


def test_turnover_avganger_vises_ogsaa_for_ledergruppen(ansatte, siste_12):
    rad = b.turnover_per_team(ansatte, *siste_12).set_index("team").loc["ledergruppen"]
    assert rad["skjult"] == "lite team"
    assert rad["avganger"] == 0 and rad["kontrakt_utløpt"] == 0  # vises, ikke skjult
    assert pd.isna(rad["total_rate"]) and pd.isna(rad["uønsket"])
    at = kjor("sider/1_Turnover.py", "Siste 12 mnd", "ledergruppen")
    assert [m.label for m in at.metric] == ["Avganger", "Kontrakt utløpt"]


# --- Trendgrafer over hele dataperioden, femregel per punkt ----------------------------

def test_sykefravaer_trend_hele_perioden(fravaer):
    per_maaned = b.sykefravaer_per_maaned(fravaer, *b.TRENDPERIODE)
    assert len(per_maaned) == 24


def test_sykefravaer_trend_femregel_per_maaned(fravaer):
    # Ledergruppen (4 ansatte) holdes utenfor hver måned (sekundær prikking) ...
    alle = b.sykefravaer_per_maaned(fravaer, *b.TRENDPERIODE)
    uten = b.sykefravaer_per_maaned(fravaer[fravaer["team"] != "ledergruppen"], *b.TRENDPERIODE)
    pd.testing.assert_frame_equal(alle, uten)
    # ... og vises aldri alene
    alene = b.sykefravaer_per_maaned(fravaer[fravaer["team"] == "ledergruppen"], *b.TRENDPERIODE)
    assert alene.empty


def test_langtid_per_kvartal_femregel(fravaer):
    kvartaler = b.kvartaler_i_perioden(*b.TRENDPERIODE)
    assert len(b.langtid_per_kvartal(fravaer[fravaer["team"] != "ledergruppen"], kvartaler)) == 8
    assert b.langtid_per_kvartal(fravaer[fravaer["team"] == "ledergruppen"], kvartaler).empty


def test_enps_per_kvartal_skjult_har_riktig_form(engasjement):
    kvartaler = b.kvartaler_i_perioden(*b.TRENDPERIODE)
    tom = b.enps_per_kvartal(engasjement[engasjement["team"] == "ledergruppen"], kvartaler)
    assert tom.empty and "enps" in tom.columns


@pytest.mark.parametrize("side", ["sider/2_Sykefravaer.py", "sider/5_Engasjement.py"])
@pytest.mark.parametrize("periode", list(b.FASTE_PERIODER))
def test_trendgraf_viser_hele_perioden_uansett_valg(side, periode):
    at = kjor(side, periode)
    assert any("Hele dataperioden" in c.value for c in at.caption)


# --- Rekruttering: femregelen på median, andel og antall -------------------------------

def test_rekruttering_under_5_skjules(ansatte, siste_12):
    tre = b.ansettelser_i_perioden(ansatte, *siste_12).head(3)["ansatt_id"]
    r = b.rekruttering(ansatte[ansatte["ansatt_id"].isin(tre)], *siste_12)
    assert r["antall"] == 3
    assert r["median_dager"] is None and r["andel_strukturert"] is None


def test_tid_til_ansettelse_per_team_femregel(ansatte, siste_12):
    per_team = b.tid_til_ansettelse_per_team(ansatte, *siste_12)
    assert (per_team["median_dager"].isna() == (per_team["antall"] < b.MIN_GRUPPE)).all()


@pytest.mark.parametrize("periode", list(b.FASTE_PERIODER))
def test_strukturert_per_kvartal_minst_5(ansatte, periode):
    assert (b.strukturert_per_kvartal(ansatte, *b.FASTE_PERIODER[periode])["antall"]
            >= b.MIN_GRUPPE).all()


@pytest.mark.parametrize("periode", list(b.FASTE_PERIODER))
def test_tilleggsmetoder_femregel_ogsa_for_hele_selskapet(ansatte, periode):
    for antall in b.bruk_av_tilleggsmetoder(ansatte, *b.FASTE_PERIODER[periode]).values():
        assert antall is None or antall >= b.MIN_GRUPPE


@pytest.mark.parametrize("periode", list(b.FASTE_PERIODER))
def test_kvalitet_sekundar_prikking(ansatte, periode):
    slutt = b.FASTE_PERIODER[periode][1]
    total = b.kvalitet_per_nivaa_prikket(ansatte, slutt).set_index("gruppe")
    per_team = {t: b.kvalitet_per_nivaa(ansatte[ansatte["team"] == t], slutt).set_index("gruppe")
                for t in b.TEAM}
    for nivaa in b.NIVAAER:
        for n_kol, antall_kol in [("tidlig_n", "tidlig_antall"), ("provetid_n", "provetid_bestatt")]:
            if pd.isna(total.loc[nivaa, antall_kol]):
                continue  # cellen er skjult – ingenting å regne ut
            rest = sum(int(k.loc[nivaa, n_kol]) for k in per_team.values()
                       if 0 < k.loc[nivaa, n_kol] < b.MIN_GRUPPE)
            assert rest == 0 or rest >= b.MIN_GRUPPE, (nivaa, n_kol, rest)


def test_kvalitet_ett_team_prikkes_ikke_sekundaert(ansatte):
    k = b.kvalitet_per_nivaa_prikket(ansatte, b.DATA_TIL, ["salg"])
    assert not k["tidlig_prikket"].any() and not k["provetid_prikket"].any()


def test_rekrutteringssiden_har_begrenset_filter():
    at = kjor("sider/3_Rekruttering.py", "Forrige 12 mnd", "salg")
    assert len(at.sidebar.select_slider) == 0 and len(at.sidebar.multiselect) == 0


# --- Bemanning: median tid til tiltredelse ---------------------------------------------

@pytest.mark.parametrize("periode", list(b.FASTE_PERIODER))
def test_bemanning_median_skjult_under_5(ansatte, plan, periode):
    bt = b.bemanning_per_team(ansatte, plan, *b.FASTE_PERIODER[periode])
    assert (bt["tiltredelse_median"].isna() == (bt["tiltredelse_n"] < b.MIN_GRUPPE)).all()

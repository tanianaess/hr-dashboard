# Lenkene mellom Bemanning og Rekruttering: knapp bare for team som er markert (◆)
# og under plan, og forhåndsvalget gir ett team og en fast periode på Rekruttering.

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

import beregninger as b
import filtre

PROSJEKT = Path(__file__).resolve().parent.parent


def kjor(side, session_state=None):
    at = AppTest.from_file(str(PROSJEKT / side), default_timeout=180)
    for nokkel, verdi in (session_state or {}).items():
        at.session_state[nokkel] = verdi
    at.run()
    assert not at.exception, at.exception
    return at


def knapper(at):
    return [k.label for k in at.button if k.label.startswith("Se rekruttering for")]


# --- Regelen: markert OG under plan --------------------------------------------------

def test_bare_markerte_team_under_plan():
    per_team = pd.DataFrame([
        {"team": "a", "markert": True, "avvik": -3},   # under plan, over grensen → knapp
        {"team": "b", "markert": True, "avvik": 4},    # over plan → ingen knapp
        {"team": "c", "markert": False, "avvik": -1},  # under plan, innenfor grensen → ingen
        {"team": "d", "markert": False, "avvik": 0},
    ])
    assert b.team_under_plan(per_team) == ["a"]
    assert b.team_under_plan(per_team[per_team["team"] != "a"]) == []


def test_dagens_data_bare_teknologi(ansatte, plan, siste_12):
    assert b.team_under_plan(b.bemanning_per_team(ansatte, plan, *siste_12)) == ["teknologi"]


# --- Bemanning-siden ---------------------------------------------------------------

def test_bemanning_viser_knapp_bare_for_teknologi():
    assert knapper(kjor("sider/4_Bemanning.py")) == ["Se rekruttering for teknologi"]


def test_bemanning_ingen_knapper_uten_team_under_plan():
    at = kjor("sider/4_Bemanning.py",
              {filtre.NOKKEL_FLERVALG: [t for t in b.TEAM if t != "teknologi"]})
    assert knapper(at) == []


def kjor_via_menyen(side, session_state=None):
    """Kjører dashbordet fra app.py (med menyen) og går til en side, slik at
    st.switch_page() i forhandsvelg() virker som i nettleseren."""
    at = AppTest.from_file(str(PROSJEKT / "app.py"), default_timeout=180)
    for nokkel, verdi in (session_state or {}).items():
        at.session_state[nokkel] = verdi
    at.switch_page(side).run()
    assert not at.exception, at.exception
    return at


def test_knappen_forhandsvelger_teamet_paa_rekruttering():
    at = kjor_via_menyen("sider/4_Bemanning.py")
    at.button(key="rekruttering_teknologi").click().run()
    assert not at.exception, at.exception
    # Nå vises Rekruttering, med teknologi og siste 12 mnd valgt. Femregelen og faste
    # visninger: ett team i det begrensede filteret, aldri flervalg.
    assert any("Utvalg: teknologi." in c.value for c in at.main.caption)
    assert at.sidebar.selectbox(key=filtre.NOKKEL_TEAM).value == "teknologi"
    assert at.sidebar.selectbox(key=filtre.NOKKEL_PERIODE).value == "Siste 12 mnd"
    assert not at.sidebar.multiselect  # ikke noe flervalg på siden


# --- Rekruttering-siden ------------------------------------------------------------

def test_rekruttering_lenker_til_bemanning_uten_team():
    at = kjor_via_menyen("sider/3_Rekruttering.py", {filtre.NOKKEL_TEAM: "teknologi"})
    at.button(key="til_bemanning").click().run()
    assert not at.exception, at.exception
    # Nå vises Bemanning, med alle team (ikke teknologi alene) og siste 12 mnd
    assert any("Utvalg: hele selskapet." in c.value for c in at.main.caption)
    assert at.sidebar.multiselect[0].value == list(b.TEAM)
    assert at.sidebar.select_slider[0].value == ("2025-10", "2026-09")


def test_lenken_vises_naar_siden_stopper_tidlig():
    # Ledergruppen har ingen ansettelser siste 12 mnd, så siden stopper tidlig
    at = kjor("sider/3_Rekruttering.py", {filtre.NOKKEL_TEAM: "ledergruppen"})
    assert any("Ingen ansettelser" in i.value for i in at.info)
    assert [k.key for k in at.button] == ["til_bemanning"]


# --- Tid til tiltredelse og regelen om oppsigelsestid ------------------------------

def test_oppsigelsestid_dominerer():
    assert b.oppsigelsestid_dominerer(36, 77)        # mer enn dobbelt
    assert b.oppsigelsestid_dominerer(30, 60)        # akkurat dobbelt
    assert not b.oppsigelsestid_dominerer(31, 61)    # litt under dobbelt
    assert b.oppsigelsestid_dominerer(32.4, 64)      # bruker tallene som vises: 32 og 64
    assert not b.oppsigelsestid_dominerer(None, 77)  # skjult (femregelen)
    assert not b.oppsigelsestid_dominerer(36, None)


def tiltredelse_kort(at):
    return next(m for m in at.metric if m.label == "Median tid til tiltredelse")


def test_tiltredelse_kort_og_linje_hele_selskapet():
    at = kjor("sider/3_Rekruttering.py")
    assert tiltredelse_kort(at).value == "77 dager"
    assert any(c.value == "Fra utlysning til første arbeidsdag, inkludert oppsigelsestid"
               for c in at.caption)
    assert any(m.value == b.OPPSIGELSESTID_TEKST for m in at.markdown)


def test_ingen_linje_naar_tiltredelse_er_under_dobbelt():
    at = kjor("sider/3_Rekruttering.py", {filtre.NOKKEL_TEAM: "salg"})  # 61 mot 31 dager
    assert tiltredelse_kort(at).value == "61 dager"
    assert not any(m.value == b.OPPSIGELSESTID_TEKST for m in at.markdown)


def test_tiltredelse_skjult_under_fem():
    at = kjor("sider/3_Rekruttering.py", {filtre.NOKKEL_TEAM: "markedsføring"})  # 4 ansettelser
    assert tiltredelse_kort(at).value == "–"
    assert not any(m.value == b.OPPSIGELSESTID_TEKST for m in at.markdown)


def test_tiltredelse_samme_tall_som_bemanning(ansatte, plan, siste_12):
    per_team = b.bemanning_per_team(ansatte, plan, *siste_12).set_index("team")
    for team in ["teknologi", "salg", "kundesuksess"]:
        utvalg = ansatte[ansatte["team"] == team]
        assert b.tid_til_tiltredelse(utvalg, *siste_12) == per_team.loc[team, "tiltredelse_median"]

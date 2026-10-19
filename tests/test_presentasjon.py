# Tilbakemeldinger før deploy 16.10.2026: skjulte KPI-kort, introduksjon og tekster på
# forsiden, spørsmål per side, «Mulig neste steg»-farge, en-endinger og GitHub Actions.

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import beregninger as b
import utseende as u
from filtre import SIDER, SPORSMAL

PROSJEKT = Path(__file__).resolve().parent.parent
FORSIDE = PROSJEKT / "sider" / "0_Oversikt.py"


def kjor(side, periode=None, team=None):
    at = AppTest.from_file(str(PROSJEKT / side), default_timeout=180)
    at.run()
    if periode:
        at.sidebar.selectbox(key="filter_periode").set_value(periode).run()
    if team:
        at.sidebar.selectbox(key="filter_team").set_value(team).run()
    assert not at.exception, at.exception
    return at


def all_tekst(at):
    """All tekst på siden: markdown, tekst under (caption), og KPI-kortene."""
    return " ".join([*(m.value for m in at.markdown), *(c.value for c in at.caption),
                     *(str(m.value) for m in at.metric), *(m.label for m in at.metric)])


# --- 1. Skjulte tall i KPI-kort ------------------------------------------------------

@pytest.mark.parametrize("side, periode, team", [
    ("app.py", None, None),
    ("sider/1_Turnover.py", "Siste 12 mnd", "produktutvikling"),  # få avganger: fordeling skjult
    ("sider/3_Rekruttering.py", "Siste 12 mnd", None),             # tilleggsmetoder skjult
    ("sider/3_Rekruttering.py", "Siste 12 mnd", "produktutvikling"),  # 3 ansettelser: median skjult
    ("sider/5_Engasjement.py", "Siste 12 mnd", None),
])
def test_ingen_lange_verdier_i_kpi_kort(side, periode, team):
    at = kjor(side, periode, team)
    for m in at.metric:
        # «17,8 mill. kr» (13 tegn) er lengste lovlige verdi; «skjult (under 5)» (16) var feilen
        assert len(str(m.value)) <= 13, (m.label, m.value)


def test_skjult_kort_viser_strek_og_forklaring():
    at = kjor("sider/3_Rekruttering.py", "Siste 12 mnd", "produktutvikling")  # 3 ansettelser
    kort = {m.label: m.value for m in at.metric}
    assert kort["Median tid til ansettelse"] == "–"
    assert any("Skjult" in c.value and "færre enn 5" in c.value for c in at.caption)


# --- 2-4 og 7. Forsiden ---------------------------------------------------------------

def test_forsiden_har_introduksjon_periode_og_datodato():
    at = kjor("app.py")
    tekst = all_tekst(at)
    assert "For ledergruppen i selskaper med 50-500 ansatte." in tekst
    assert "virker endringene i rekrutteringen?" in tekst
    start, slutt = b.FASTE_PERIODER["Siste 12 mnd"]
    assert (f"Tallene gjelder hele selskapet de siste 12 månedene "
            f"({start:%d.%m.%Y}-{slutt:%d.%m.%Y})") in tekst
    assert f"Data per {b.DATA_TIL:%d.%m.%Y}" in tekst
    assert "Regelbaserte innsikter om de største avvikene. De bruker bare tall som også vises " \
           "under de andre temaene" in tekst
    assert "(ikke AI)" not in tekst


def test_syntetisk_merknad_paa_alle_sider_og_i_readme():
    ny = "og bygger ikke på data fra noe ekte selskap"
    assert ny in b.SYNTETISK_MERKNAD and "ikke ekte funn" not in b.SYNTETISK_MERKNAD
    readme = (PROSJEKT / "README.md").read_text(encoding="utf-8")
    assert "ikke ekte funn" not in readme and "bygger ikke på data fra noe ekte" in readme
    for side in SIDER.values():
        assert any(ny in c.value for c in kjor(side).caption), side


# --- 8. Spørsmålet på hver detaljside -----------------------------------------------------

@pytest.mark.parametrize("navn", list(SPORSMAL))
def test_detaljsiden_viser_sporsmaalet(navn):
    at = kjor(SIDER[navn])
    assert any(SPORSMAL[navn] in m.value for m in at.markdown)


def test_alle_detaljsider_har_et_sporsmaal():
    assert set(SPORSMAL) == set(SIDER) - {"Oversikt"}


# --- 5. «Mulig neste steg» i lys petrol ----------------------------------------------------

def test_neste_steg_faar_lys_petrol_paa_ett_sted():
    kilde = FORSIDE.read_text(encoding="utf-8")
    assert "u.neste_steg_stil()" in kilde
    assert 'key=f"{u.NESTE_STEG_NOKKEL}{nr}"' in kilde
    assert u.MARKERT_BAKGRUNN == "#E4EEF0"
    # Fargen står ikke i sidene, bare i utseende.py
    for side in (PROSJEKT / "sider").glob("*.py"):
        assert "#E4EEF0" not in side.read_text(encoding="utf-8"), side.name
    at = kjor("app.py")
    assert any("Mulig neste steg" in m.value for m in at.markdown)


# --- 6. En-endinger -----------------------------------------------------------------------

A_ENDINGER = re.compile(r"(?i)(pila|linja|fila|mappa|lyspæra|grafa)\b")


def test_ingen_a_endinger():
    filer = [*PROSJEKT.glob("*.py"), *PROSJEKT.glob("sider/*.py"), *PROSJEKT.glob("tests/*.py"),
             PROSJEKT / "README.md", PROSJEKT / "CLAUDE.md"]
    treff = []
    for f in filer:
        tekst = f.read_text(encoding="utf-8")
        if f.name == Path(__file__).name:
            tekst = tekst.replace(A_ENDINGER.pattern, "")  # mønsteret selv teller ikke
        # Eksempler i anførselstegn («pila») er lov – de forklarer regelen i CLAUDE.md
        treff += [f"{f.name}: {m.group(0)}" for m in A_ENDINGER.finditer(tekst)
                  if tekst[m.start() - 1:m.start()] != "«"]
    assert not treff, treff


# --- 11. Testene kjører på GitHub ------------------------------------------------------------

def test_github_actions_kjorer_testene():
    flyt = (PROSJEKT / ".github" / "workflows" / "tester.yml").read_text(encoding="utf-8")
    assert 'python-version: "3.12"' in flyt
    assert "requirements.txt" in flyt and "requirements-dev.txt" in flyt
    assert "pytest" in flyt
    readme = (PROSJEKT / "README.md").read_text(encoding="utf-8")
    assert "actions/workflows/tester.yml/badge.svg" in readme


# --- Intervaller med bindestrek (Tanias valg 16.10.2026) -----------------------------------

def test_intervaller_med_bindestrek():
    # Tankestrek (–) mellom to tall eller ord, f.eks. «50–500», skal være bindestrek: «50-500».
    # «–» alene (ingen verdi) og tankestrek med mellomrom ( – ) er lov.
    intervall = re.compile(r"(?<=[0-9A-Za-zæøåÆØÅ}\])])–(?=[0-9A-Za-zæøåÆØÅ{(])")
    filer = [*PROSJEKT.glob("*.py"), *PROSJEKT.glob("sider/*.py"),
             PROSJEKT / "README.md", PROSJEKT / "CLAUDE.md"]
    treff = [f"{f.name}: {m.group(0)}" for f in filer
             for m in intervall.finditer(f.read_text(encoding="utf-8"))]
    assert not treff, treff
    at = kjor("app.py")
    assert "50-500 ansatte" in all_tekst(at)


# --- Samme ikon i menyen og foran overskriften ----------------------------------------------

@pytest.mark.parametrize("navn", ["Oversikt", "Turnover", "Sykefravær", "Rekruttering",
                                  "Bemanning", "Engasjement", "Utvikling"])
def test_overskriften_har_samme_ikon_som_menyen(navn):
    from filtre import IKONER
    at = kjor(SIDER[navn])
    assert at.title[0].value.startswith(f":blue[{IKONER[navn]}]"), at.title[0].value


def test_forsiden_merknad_og_periode_under_introen():
    at = kjor("app.py")
    # Introen ligger i en ramme, og de to setningene kommer etter den
    tekster = [e.value for e in at.main if hasattr(e, "value") and isinstance(e.value, str)]
    intro = next(i for i, t in enumerate(tekster) if t.startswith("**For ledergruppen"))
    syntetisk = next(i for i, t in enumerate(tekster) if "bygger ikke på data fra noe ekte" in t)
    periode = next(i for i, t in enumerate(tekster) if t.startswith("Tallene gjelder hele selskapet"))
    assert intro < syntetisk < periode

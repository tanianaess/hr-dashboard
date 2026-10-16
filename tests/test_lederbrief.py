# Lederbrief (AI): grunnlaget AI-modellen får, den lagrede briefen, kontrollene og
# visningen på forsiden. Reglene står i CLAUDE.md («Lederbrief (AI)»).

import re
from pathlib import Path

import pytest

import beregninger as b
import innsikter as i
import lederbrief as lb
from test_presentasjon import all_tekst, kjor

PROSJEKT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def forside(ansatte, fravaer, engasjement, plan):
    """Det forsiden regner ut: nøkkeltall, innsikter og grunnlaget som bygger på dem."""
    nokkeltall = i.nokkeltall(ansatte, fravaer, engasjement, plan)
    innsikt_liste = i.innsikter(ansatte, fravaer, engasjement, plan, nokkeltall,
                                samtaler=b.les_en_til_en())
    return nokkeltall, innsikt_liste, lb.grunnlag(nokkeltall, innsikt_liste)


# --- Grunnlaget ---------------------------------------------------------------------------

def test_grunnlaget_er_det_forsiden_viser(forside):
    """Ingen ansatt-ID, og hvert tall i grunnlaget står også på forsiden."""
    _, _, grunnlag = forside
    assert not re.search(r"\bA\d{3}\b", grunnlag)
    at = kjor("app.py")
    side = all_tekst(at) + " " + " ".join(str(m.delta) for m in at.metric)
    lovlige = set(lb.TALL.findall(side))
    ukjente = {t for t in lb.TALL.findall(grunnlag) if t not in lovlige}
    assert not ukjente, ukjente


def test_grunnlaget_har_ikke_tiltak_eller_lenker(forside):
    """«Mulig neste steg» holdes utenfor, så briefen ikke gjentar tiltak."""
    _, innsikt_liste, grunnlag = forside
    for innsikt in innsikt_liste:
        assert innsikt["neste_steg"] not in grunnlag
    assert "Mulig neste steg" not in grunnlag and "**" not in grunnlag


def test_fingeravtrykk(forside):
    _, _, grunnlag = forside
    assert len(lb.fingeravtrykk(grunnlag)) == 12
    assert lb.fingeravtrykk(grunnlag) == lb.fingeravtrykk(grunnlag)
    assert lb.fingeravtrykk(grunnlag) != lb.fingeravtrykk(grunnlag + " ")


def test_instruksen_inneholder_reglene():
    for regel in ("bare tall", "Ingen tiltak", "spørsmål", "Sammenheng er ikke årsak",
                  str(lb.MAKS_ORD)):
        assert regel in lb.INSTRUKS, regel


# --- Den lagrede briefen ---------------------------------------------------------------------

def test_lagret_brief_folger_reglene(forside):
    """Briefen i data/ bygger på dagens tall og går gjennom alle kontrollene."""
    _, _, grunnlag = forside
    brief = lb.les_lederbrief()
    assert brief is not None, "data/lederbrief.json mangler"
    for felt in ("laget", "modell", "periode", "data_per", "fingeravtrykk", "grunnlag", "brief"):
        assert brief.get(felt), felt
    assert lb.status(brief, grunnlag) != "utdatert"
    assert brief["grunnlag"] == grunnlag
    assert lb.kontroller(brief["brief"], grunnlag) == []


def test_kontrollene_fanger_feil(forside):
    _, _, grunnlag = forside
    felt = lb.les_lederbrief()["brief"]

    def med(sammendrag):
        return lb.kontroller({**felt, "sammendrag": sammendrag}, grunnlag)

    assert any("tall som ikke står i grunnlaget" in p for p in med("Turnover er 99,9 %."))
    assert any("markedsføring" in p for p in med("Markedsføring sliter."))
    assert any("lang tankestrek" in p for p in med("Tall — og tekst."))
    assert any("a-ending" in p for p in med("Se «pila» i kortet."))
    assert any("minustegn" in p for p in med("Endring -6 dager."))
    assert any("tankestrek i intervall" in p for p in med("Mellom 10–15 %."))
    assert any("maks" in p for p in med("ord " * (lb.MAKS_ORD + 1)))
    assert any("mangler" in p for p in lb.kontroller({**felt, "forbehold": ""}, grunnlag))


def test_markdown_nedlasting():
    brief = lb.les_lederbrief()
    md = lb.som_markdown(brief)
    assert md.startswith("# Lederbrief: Fjordlys Tech AS")
    assert brief["brief"]["sammendrag"] in md and "## Følg med" in md
    assert "Skrevet av AI-modellen" in md


# --- Forsiden ---------------------------------------------------------------------------------

def test_forsiden_viser_briefen_bare_naar_den_er_godkjent_og_oppdatert(tmp_path, monkeypatch):
    brief = lb.les_lederbrief()
    sti = tmp_path / "lederbrief.json"
    monkeypatch.setattr(lb, "STI", sti)  # forsiden leser fra denne i stedet for data/

    def kjor_med(variant):
        if variant is None:
            sti.unlink(missing_ok=True)
        else:
            lb.lagre_lederbrief(variant, sti)
        at = kjor("app.py")
        return at, all_tekst(at)

    # Uten fil: ingenting om lederbrief på siden
    at, tekst = kjor_med(None)
    assert "Lederbrief" not in [s.value for s in at.subheader]
    assert "Skrevet av AI-modellen" not in tekst and "Lederbriefen lenger ned" not in tekst

    # Godkjent og oppdatert: vises med merking, og henvisningen under «Viktigste innsikter»
    godkjent = {**brief, "godkjent": "2026-10-20"}
    at, tekst = kjor_med(godkjent)
    assert "Lederbrief" in [s.value for s in at.subheader]
    assert "Skrevet av AI-modellen" in tekst
    assert "Lest og godkjent av HR-leder 20.10.2026" in tekst
    assert "Spørsmål til ledermøtet" in tekst and "Hva AI-modellen fikk" in [e.label for e in at.expander]
    assert "Lederbriefen lenger ned er skrevet av en AI-modell og er merket." in tekst

    # Laget, men ikke godkjent: bare en forklaring
    at, tekst = kjor_med({**brief, "godkjent": ""})
    assert "ikke lest og godkjent" in tekst and "Skrevet av AI-modellen" not in tekst

    # Godkjent, men tallene har endret seg (gammelt fingeravtrykk): bare en forklaring
    at, tekst = kjor_med({**godkjent, "fingeravtrykk": "000000000000"})
    assert "ikke oppdatert etter siste dataoppdatering" in tekst
    assert "Skrevet av AI-modellen" not in tekst


# --- Dashbordet trenger ikke pakken anthropic -----------------------------------------------

def test_dashbordet_importerer_ikke_anthropic():
    for fil in [*PROSJEKT.glob("*.py"), *PROSJEKT.glob("sider/*.py")]:
        if fil.name == "lag_lederbrief.py":
            continue
        assert "import anthropic" not in fil.read_text(encoding="utf-8"), fil.name
    krav = (PROSJEKT / "requirements.txt").read_text(encoding="utf-8")
    assert "anthropic" not in krav
    assert "anthropic" in (PROSJEKT / "requirements-dev.txt").read_text(encoding="utf-8")

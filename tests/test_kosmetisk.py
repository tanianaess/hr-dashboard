# Kosmetiske funn fra kodegjennomgangen: felles hjelpefunksjoner, verktøytips,
# sidestier på ett sted, ærlig status-regel og kontrollskript som bruker beregninger.py.

import re
import subprocess
import sys
from pathlib import Path

import beregninger as b
import innsikter as i
from filtre import SENSITIVE_SIDER, SIDER

PROSJEKT = Path(__file__).resolve().parent.parent
SIDEFILER = sorted((PROSJEKT / "sider").glob("*.py"))


def test_enps_tekst():
    assert b.enps_tekst(13.6) == "+14"
    assert b.enps_tekst(-13.5) == "−14"  # 5 rundes bort fra null, som i Excel
    assert b.enps_tekst(0.4) == "0"
    assert b.enps_tekst(None) == "–"


def test_endring_antall():
    assert b.endring_antall(2.5, "poeng") == "+3 poeng"
    assert b.endring_antall(-6.4, "dager", "dag") == "-6 dager"  # bindestrek: retning på pila
    assert b.endring_antall(1, "dager", "dag") == "+1 dag"
    assert b.endring_antall(0.4, "dager") == "±0 dager"
    assert b.endring_antall(None, "poeng") is None


def test_status_respekterer_ok_inkludert_for_enps():
    # eNPS: «+10 eller høyere» er OK (inkludert), 9 er «Følg med»
    assert i.status("eNPS", 10)[0] == i.OK
    assert i.status("eNPS", 9)[0] == i.FOLG_MED
    assert i.status("eNPS", -1)[0] == i.KRITISK


def test_sidestier_bare_ett_sted():
    assert all((PROSJEKT / fil).exists() for fil in SIDER.values())
    assert SENSITIVE_SIDER <= set(SIDER.values())
    # Ingen andre filer skriver sidestiene selv
    filer = [PROSJEKT / "app.py", PROSJEKT / "innsikter.py", *SIDEFILER]
    treff = [f.name for f in filer if re.search(r'["\']sider/\d_', f.read_text(encoding="utf-8"))]
    assert not treff, treff


def test_ingen_lokale_kopier_av_hjelpefunksjoner():
    for fil in [PROSJEKT / "innsikter.py", *SIDEFILER]:
        tekst = fil.read_text(encoding="utf-8")
        for navn in ["def enps_tekst", "def fortegn", "def med_fortegn", "def millioner",
                     'SKJULT = "', "@st.cache_data\ndef hent_ansatte"]:
            assert navn not in tekst, (fil.name, navn)


def test_ubrukt_kode_er_fjernet():
    assert not hasattr(b, "kvalitet_per_metode")
    assert not hasattr(i, "ALVOR")


def test_verktoytips_bruker_ferdig_tekst():
    # Ingen d3-format (desimalpunktum, JavaScript-avrunding) i verktøytipsene
    for fil in SIDEFILER:
        assert '"format": "' not in fil.read_text(encoding="utf-8"), fil.name


def test_ingen_mellomrom_foer_punktum_mellom_tekstbiter():
    # F.eks. «… **utvalget** " + ". Små grupper» ga «utvalget . Små»
    for fil in SIDEFILER:
        assert not re.search(r' "\s*\n\s*"\. ', fil.read_text(encoding="utf-8")), fil.name


def test_kontrollskript_virker_fra_annen_mappe_og_forklarer_avvik(tmp_path):
    svar = subprocess.run([sys.executable, str(PROSJEKT / "kontroller_mot_excel.py")],
                          cwd=tmp_path, capture_output=True, text=True, timeout=120)
    assert svar.returncode == 0, svar.stderr
    assert "Alle avvik er forklart." in svar.stdout


def test_kontrollskript_bruker_beregninger():
    tekst = (PROSJEKT / "kontroller_mot_excel.py").read_text(encoding="utf-8")
    assert "import beregninger as b" in tekst
    assert "b.turnover(" in tekst and "b.sykefravaer(" in tekst


def test_generator_bruker_sti_ved_siden_av_skriptet():
    tekst = (PROSJEKT / "lag_syntetiske_data.py").read_text(encoding="utf-8")
    assert 'DATAMAPPE = Path(__file__).parent / "data"' in tekst

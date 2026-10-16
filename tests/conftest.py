# Felles oppsett for testene: legger prosjektmappen til i Pythons søkesti og leser
# dataene én gang (fixtures = ferdige «inndata» som testene kan be om).

import sys
from pathlib import Path

import pytest

PROSJEKT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROSJEKT))

import beregninger as b  # noqa: E402  (må importeres etter at søkestien er satt)


@pytest.fixture(scope="session")
def ansatte():
    return b.les_ansatte()


@pytest.fixture(scope="session")
def fravaer(ansatte):
    return b.fravaer_med_avtalte(ansatte, b.les_fravaer())


@pytest.fixture(scope="session")
def engasjement():
    return b.les_engasjement()


@pytest.fixture(scope="session")
def plan():
    return b.les_bemanningsplan()


@pytest.fixture(scope="session")
def siste_12():
    return b.FASTE_PERIODER["Siste 12 mnd"]

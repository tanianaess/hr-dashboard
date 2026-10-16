# Kompetanseutvikling: opplæring, 1:1 med lederen og intern mobilitet (se CLAUDE.md).

from pathlib import Path

import pandas as pd
import pytest

import beregninger as b
import innsikter as i

PROSJEKT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def data():
    return b.les_opplaering(), b.les_en_til_en(), b.les_stillingsendringer()


def test_kompetansedata_kobles_til_ansatte(ansatte, data):
    opplaering, samtaler, endringer = data
    ids = set(ansatte["ansatt_id"])
    for tabell in data:
        assert set(tabell["ansatt_id"]) <= ids
    # Interne endringer skjer i personens eget team (ett team per person i datamodellen)
    lag = endringer.merge(ansatte[["ansatt_id", "team"]], on="ansatt_id", suffixes=("", "_ansatt"))
    assert (lag["team"] == lag["team_ansatt"]).all()
    assert set(endringer["type"]) <= {"forfremmelse", "intern overgang"}
    assert (endringer["utlysningsdato"] < endringer["dato"]).all()
    assert (opplaering["kostnad"] >= 0).all() and (opplaering["timer"] > 0).all()


def test_salg_har_minst_oppfolging(ansatte, data, siste_12):
    _, samtaler, _ = data
    andel = {t: b.en_til_en(ansatte[ansatte["team"] == t], samtaler, *siste_12) for t in b.TEAM}
    synlige = {t: s["andel_jevnlige"] for t, s in andel.items() if s}
    assert min(synlige, key=synlige.get) == "salg"
    assert andel["ledergruppen"] is None  # 4 personer: under femregelen


def test_jevnlige_1til1_bare_blant_dem_som_var_ansatt_hele_perioden(ansatte, data, siste_12):
    _, samtaler, _ = data
    s = b.en_til_en(ansatte, samtaler, *siste_12)
    # «Ansatt alle månedene» = ansatt minst én dag i hver måned i perioden
    forste_mnd_slutt = b.maanedsslutt(siste_12[0])
    siste_mnd_start = siste_12[1].replace(day=1)
    hele = ansatte[(ansatte["ansattdato"] <= forste_mnd_slutt)
                   & (ansatte["sluttdato"].isna() | (ansatte["sluttdato"] >= siste_mnd_start))]
    assert s["n"] == len(hele)
    assert 0 < s["andel_jevnlige"] < 1


def test_opplaering_femregel(ansatte, data, siste_12):
    opplaering, _, _ = data
    assert b.opplaering(ansatte[ansatte["team"] == "ledergruppen"], opplaering, *siste_12) is None
    o = b.opplaering(ansatte, opplaering, *siste_12)
    assert o["deltatt"] <= o["personer"]


@pytest.mark.parametrize("periode", list(b.FASTE_PERIODER))
def test_forfremmelser_skjules_under_5_interne_endringer(ansatte, data, periode):
    _, _, endringer = data
    for team in b.TEAM:
        m = b.intern_mobilitet(ansatte[ansatte["team"] == team], endringer, *b.FASTE_PERIODER[periode])
        if m["interne"] < b.MIN_GRUPPE or m["snitt_ansatte"] < b.MIN_GRUPPE:
            assert m["forfremmelser"] is None and m["forfremmelsesrate"] is None
        if m["besatte"] < b.MIN_GRUPPE:
            assert m["besettelsesgrad"] is None


@pytest.mark.parametrize("periode", b.alle_sammenligningsperioder(), ids=str)
def test_sekundar_prikking_forfremmelser(ansatte, data, periode):
    _, _, endringer = data
    utenfor = b.utenfor_forfremmelser(ansatte, endringer, b.TEAM)
    skjulte = {}
    for team in b.TEAM:
        m = b.intern_mobilitet(ansatte[ansatte["team"] == team], endringer, *periode)
        if m["forfremmelser"] is None:
            skjulte[team] = m["interne"]
    rest = sum(n for t, n in skjulte.items() if t not in utenfor)
    assert rest == 0 or rest >= b.MIN_GRUPPE, (periode, skjulte, utenfor)


def test_intern_besettelse_er_raskere_enn_ekstern(ansatte, data, siste_12):
    _, _, endringer = data
    m = b.intern_mobilitet(ansatte, endringer, *siste_12)
    assert m["median_dager_intern"] < b.rekruttering(ansatte, *siste_12)["median_dager"]
    assert 0.05 < m["besettelsesgrad"] < 0.5


def test_kompetanse_per_team_viser_aldri_smaa_team(ansatte, data, siste_12):
    rad = b.kompetanse_per_team(ansatte, *data, *siste_12).set_index("team").loc["ledergruppen"]
    for kolonne in ["timer_per_ansatt", "kostnad_per_ansatt", "andel_jevnlige", "forfremmelser"]:
        assert pd.isna(rad[kolonne]), kolonne


def test_innsikt_kobler_turnover_og_oppfolging_i_salg(ansatte, fravaer, engasjement, plan, data):
    _, samtaler, _ = data
    liste = i.innsikter(ansatte, fravaer, engasjement, plan, samtaler=samtaler)
    salg = [x for x in liste if x["tittel"].startswith("Salg")]
    assert salg and "lite oppfølging" in salg[0]["tittel"]
    assert ("Kompetanse", "salg") in salg[0]["lenker"]
    assert salg[0]["merknad"] == b.OPPFOLGING_TURNOVER_MERKNAD


def test_generatoren_endrer_ikke_de_andre_dataene():
    # Kompetansedataene bruker egen tilfeldighetsgenerator (FRO + 2)
    kilde = (PROSJEKT / "lag_syntetiske_data.py").read_text(encoding="utf-8")
    assert "random.Random(FRO + 2)" in kilde
    assert kilde.index("tilfeldig_kompetanse = random.Random(FRO + 2)") > kilde.index("plan_df = pd.DataFrame(")

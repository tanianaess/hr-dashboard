# Personvern: skjulte grupper skal ikke kunne regnes ut som «total minus de synlige».

import pytest

import beregninger as b


def _rest_er_trygg(skjulte_storrelser, utenfor):
    """Summen av skjulte team som IKKE holdes utenfor totalen, må være 0 eller minst 5."""
    rest = sum(n for team, n in skjulte_storrelser.items() if team not in utenfor)
    return rest == 0 or rest >= b.MIN_GRUPPE


@pytest.mark.parametrize("periode", b.alle_sammenligningsperioder(), ids=str)
def test_sekundar_prikking_turnoverfordeling(ansatte, periode):
    utenfor = b.utenfor_turnoverfordeling(ansatte, b.TEAM)
    skjulte = {}
    for team in b.TEAM:
        t = b.turnover(ansatte[ansatte["team"] == team], *periode)
        if t["snitt_ansatte"] < b.MIN_GRUPPE or t["avganger"] < b.MIN_GRUPPE:
            skjulte[team] = t["avganger"]
    assert _rest_er_trygg(skjulte, utenfor), (periode, skjulte, utenfor)


@pytest.mark.parametrize("periode", b.alle_sammenligningsperioder(), ids=str)
def test_sekundar_prikking_sykefravaer(ansatte, periode):
    utenfor = b.utenfor_sykefravaer(ansatte, b.TEAM)
    skjulte = {t: n for t in b.TEAM
               if (n := b.snitt_ansatte(ansatte[ansatte["team"] == t], *periode)) < b.MIN_GRUPPE}
    assert _rest_er_trygg(skjulte, utenfor), (periode, skjulte, utenfor)


def test_sekundar_prikking_enps(engasjement):
    utenfor = b.utenfor_enps(engasjement, b.TEAM)
    for kvartal, e in engasjement.groupby("kvartal"):
        skjulte = dict(zip(e.loc[e["antall_svar"] < b.MIN_GRUPPE, "team"],
                           e.loc[e["antall_svar"] < b.MIN_GRUPPE, "antall_svar"]))
        assert _rest_er_trygg(skjulte, utenfor), (kvartal, skjulte, utenfor)


def test_ett_team_prikkes_ikke_sekundaert(ansatte, engasjement):
    # Sekundær prikking gjelder totaler – ett team alene får vanlig femregel
    assert b.utenfor_turnoverfordeling(ansatte, ["salg"]) == []
    assert b.utenfor_sykefravaer(ansatte, ["kundesuksess"]) == []
    assert b.utenfor_enps(engasjement, ["kundesuksess"]) == []

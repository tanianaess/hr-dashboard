# Regnestykket på Turnover: hva er det verdt å redusere frivillig turnover? Ren aritmetikk
# med selskapets gjennomsnittlige erstatningskostnad per avgang, aldri lønn per team, og
# bare i den faste visningen for kostnader (hele selskapet, siste 12 mnd). Se CLAUDE.md.

import beregninger as b
from test_presentasjon import all_tekst, kjor

OVERSKRIFT = "Hva er det verdt å redusere frivillig turnover?"


def test_regnestykke_for_hele_selskapet_og_et_team(ansatte, siste_12):
    at = kjor("sider/1_Turnover.py", "Siste 12 mnd", "Hele selskapet")
    tekst = all_tekst(at)
    assert OVERSKRIFT in tekst and "færre avganger per år" in tekst

    # Salg: 20,7 % (8 av snitt 39). Ned til selskapets nivå (10 %) er (0,207 − 0,10) × 38,6,
    # altså ca. 4 færre avganger, ganget med snittkostnaden per avgang for hele selskapet.
    at.selectbox(key="regnestykke_team").set_value("salg").run()
    assert not at.exception, at.exception
    tekst = all_tekst(at)
    assert "**salg** er 20,7 % (8 av snitt 39 ansatte)" in tekst
    assert "4 færre avganger per år" in tekst
    t = b.turnover(ansatte, *siste_12)
    per_avgang = t["lønn_avganger"] / t["avganger"] * b.KOSTNADSANDEL_STANDARD
    assert f"{b.millioner(per_avgang)} per avgang" in tekst
    assert "ikke prognose" in tekst and "Lønn per team brukes ikke" in tekst


def test_regnestykke_bare_i_den_faste_visningen():
    # Ett team valgt i filteret: kostnader (og regnestykket) vises ikke, bare infoboksen
    at = kjor("sider/1_Turnover.py", "Siste 12 mnd", "salg")
    assert OVERSKRIFT not in all_tekst(at)
    # Forrige 12 mnd: samme regel som kostnaden
    at = kjor("sider/1_Turnover.py", "Forrige 12 mnd", "Hele selskapet")
    assert OVERSKRIFT not in all_tekst(at)


def test_regnestykket_tilbyr_bare_team_der_fordelingen_vises(ansatte, siste_12):
    at = kjor("sider/1_Turnover.py", "Siste 12 mnd", "Hele selskapet")
    valg = at.selectbox(key="regnestykke_team").options
    per_team = b.turnover_per_team(ansatte, *siste_12).set_index("team")
    for team in b.TEAM:
        vises = team in valg
        assert vises == bool(per_team.loc[team, "frivillig_rate"] == per_team.loc[team, "frivillig_rate"]), team

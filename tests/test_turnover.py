# Turnover: tallene skal følge definisjonene i CLAUDE.md.

import beregninger as b


def test_turnover_siste_12(ansatte, siste_12):
    t = b.turnover(ansatte, *siste_12)
    assert (t["avganger"], t["frivillig"], t["ufrivillig"], t["pensjon"]) == (32, 23, 7, 2)
    assert t["uønsket"] == 10
    assert t["kontrakt_utløpt"] == 4
    assert round(t["snitt_ansatte"], 4) == 223.0833
    assert b.prosent(t["total_rate"]) == "14,3 %"
    assert t["lønn_uønsket"] == 7_440_000


def test_kontrakt_utlopt_teller_ikke_i_turnover(ansatte, siste_12):
    t = b.turnover(ansatte, *siste_12)
    alle_avganger = len(b.sluttet_i_perioden(ansatte, *siste_12))
    assert t["avganger"] + t["kontrakt_utløpt"] == alle_avganger


def test_annualisering_ved_9_maaneder(ansatte):
    # Formelen støtter fortsatt andre perioder enn 12 mnd, selv om sidene bare bruker faste
    start, slutt = b.pd.Timestamp("2026-01-01"), b.pd.Timestamp("2026-09-30")
    t = b.turnover(ansatte, start, slutt)
    assert len(b.maanedsslutter(start, slutt)) == 9
    assert abs(t["total_rate"] - t["avganger"] / t["snitt_ansatte"] * 12 / 9) < 1e-12


def test_tomt_utvalg_gir_ingen_rate(ansatte, siste_12):
    t = b.turnover(ansatte.iloc[0:0], *siste_12)
    assert t["total_rate"] is None
    assert t["avganger"] == 0


def test_femregelen_per_team(ansatte, siste_12):
    per_team = b.turnover_per_team(ansatte, *siste_12).set_index("team")
    assert per_team.loc["ledergruppen", "skjult"] == "lite team"
    assert per_team.loc["produktutvikling", "skjult"] == "få avganger"
    assert per_team.loc["salg", "avganger"] == 8
    assert per_team.loc["salg", "uønsket"] == 6
    assert "lønn_uønsket" not in per_team.columns  # lønn vises aldri per team


def test_perioder():
    assert b.forrige_periode(b.pd.Timestamp("2026-01-01"), b.pd.Timestamp("2026-09-30")) == (
        b.pd.Timestamp("2025-04-01"), b.pd.Timestamp("2025-12-31"))

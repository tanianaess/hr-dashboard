# Sykefravær og eNPS.

import beregninger as b


def test_sykefravaer_uten_ledergruppen(fravaer, siste_12):
    s = b.sykefravaer(fravaer[fravaer["team"] != "ledergruppen"], *siste_12)
    assert b.prosent(s["total_rate"], 2) == "5,69 %"


def test_kundesuksess_langtid_stiger(fravaer):
    k = b.sykefravaer_per_maaned(fravaer[fravaer["team"] == "kundesuksess"],
                                 *b.FASTE_PERIODER["Siste 12 mnd"])
    assert k.loc["2026-09", "Langtid"] > 2 * k.loc["2026-03", "Langtid"]


def test_enps_kundesuksess_2026K3(engasjement):
    e = b.enps_samlet(engasjement[(engasjement["team"] == "kundesuksess")
                                  & (engasjement["kvartal"] == "2026-K3")])
    assert (b.avrund(e["enps"]), e["svar"], e["invitert"]) == (-14, 20, 44)
    assert b.prosent(e["svarandel"], 0) == "45 %"


def test_enps_ledergruppen_skjules(engasjement):
    e = engasjement[(engasjement["team"] == "ledergruppen") & (engasjement["kvartal"] == "2026-K3")]
    assert b.enps_samlet(e) is None  # 4 svar → under 5


def test_kvartaler():
    assert b.kvartaler_i_perioden(*b.FASTE_PERIODER["Siste 12 mnd"]) == [
        "2025-K4", "2026-K1", "2026-K2", "2026-K3"]
    assert b.kvartaler_i_perioden(b.pd.Timestamp("2025-11-01"), b.pd.Timestamp("2026-01-31")) == []
    assert b.kvartal_minus("2026-K1", 1) == "2025-K4"

# Rekruttering (kohorter for kvalitet) og bemanning.

import beregninger as b


def test_kvalitet_per_nivaa(ansatte):
    k = b.kvalitet_per_nivaa(ansatte, b.DATA_TIL).set_index("gruppe")
    u, s = k.loc["ustrukturert"], k.loc["strukturert intervju alene"]
    assert (u["tidlig_antall"], u["tidlig_n"]) == (5, 16)
    assert (u["provetid_bestatt"], u["provetid_n"]) == (22, 26)
    assert (s["tidlig_antall"], s["tidlig_n"]) == (1, 7)
    assert (s["provetid_bestatt"], s["provetid_n"]) == (15, 16)
    assert k.loc["strukturert + tillegg", "tidlig_n"] == 0


def test_tid_til_ansettelse(ansatte, siste_12):
    assert b.avrund(b.rekruttering(ansatte, *siste_12)["median_dager"]) == 36
    per_team = b.tid_til_ansettelse_per_team(ansatte, *siste_12).set_index("team")
    assert per_team.loc["teknologi", "median_dager"] == 59.5


def test_bemanning(ansatte, plan, siste_12):
    bt = b.bemanning_per_team(ansatte, plan, *siste_12)
    assert (bt["faktisk"].sum(), bt["plan"].sum()) == (226, 239)
    assert bt.set_index("team").loc["teknologi", "markert"]

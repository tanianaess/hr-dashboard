# Formatering og avrunding: tall skal vises som i Excel og med norsk tallformat.

import beregninger as b


def test_avrund_som_excel():
    assert b.avrund(31.25, 1) == 31.3      # 5 rundes opp (Python ville gitt 31,2)
    assert b.avrund(0.5) == 1
    assert b.avrund(2.5) == 3
    assert b.avrund(-0.25, 1) == -0.3      # bort fra null, som AVRUND
    assert b.avrund(14.45, 1) == 14.5      # regnerester fjernes først


def test_prosent():
    assert b.prosent(5 / 16) == "31,3 %"
    assert b.prosent(0.0565, 2) == "5,65 %"
    assert b.prosent(None) == "–"


def test_prosent_med_n():
    assert b.prosent_med_n(1, 8) == "12,5 % (1 av 8)"
    assert b.prosent_med_n(0, 0) == "–"


def test_endring_pp():
    assert b.endring_pp(0.143, 0.112) == "+3,1 pp"
    assert b.endring_pp(0.10049, 0.1) == "±0,0 pp"


def test_kroner():
    assert b.kroner(2_700_000) == "2 700 000 kr"


def test_fortegn_bruker_ekte_minustegn():
    assert b.fortegn(-14) == "−14"
    assert b.fortegn(2) == "+2"
    assert b.fortegn(0) == "0"

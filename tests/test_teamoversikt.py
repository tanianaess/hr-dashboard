# «Teamene på ett blikk»: rutenettet på forsiden bruker de samme tallene, tersklene og
# femregelen som detaljsidene, og viser aldri tall for grupper under fem. Menyen har alle
# sidene i seksjoner.

import beregninger as b
import innsikter as i
from filtre import SEKSJONER, SIDER
from test_presentasjon import kjor

SKJULT_GRUNNER = {"under 5 ansatte", "under 5 avganger", "under 5 svar", "under 5 ansettelser", "ingen plan"}


def rute(rader, team, signal):
    rad = next(r for r in rader if r["team"] == team)
    return rad["ruter"][i.SIGNALER.index(signal)]


def test_rutenettet_har_alle_team_og_signaler(ansatte, fravaer, engasjement, plan):
    rader = i.teamoversikt(ansatte, fravaer, engasjement, plan)
    assert [r["team"] for r in rader] == b.TEAM
    for r in rader:
        assert len(r["ruter"]) == len(i.SIGNALER)
        for x in r["ruter"]:
            assert x["status"] in (None, i.OK, i.FOLG_MED, i.KRITISK)
            if x["status"] is None:
                assert x["tekst"] in SKJULT_GRUNNER  # aldri et tall i en skjult rute


def test_ledergruppen_er_skjult_unntatt_bemanning(ansatte, fravaer, engasjement, plan):
    rader = i.teamoversikt(ansatte, fravaer, engasjement, plan)
    for signal in i.SIGNALER:
        x = rute(rader, "ledergruppen", signal)
        if signal == "Bemanning":
            assert x["status"] is not None  # antall ansatte er ikke sensitivt
        else:
            assert x["status"] is None and x["tekst"].startswith("under 5"), signal


def test_rutene_bruker_samme_tall_og_terskler_som_sidene(ansatte, fravaer, engasjement, plan, siste_12):
    rader = i.teamoversikt(ansatte, fravaer, engasjement, plan)
    # Kundesuksess: sykefravær 7,85 %, over det interne målet på 6 %
    x = rute(rader, "kundesuksess", "Sykefravær")
    assert x["tekst"] == "7,85 %" and x["status"] == i.KRITISK
    # Teknologi: 84 av 98 planlagte, mer enn 10 % under planen
    x = rute(rader, "teknologi", "Bemanning")
    assert x["tekst"] == "84 av 98" and x["status"] == i.KRITISK
    # Teknologi: 60 dager til ansettelse (12 ansettelser) er «46-60 dager»
    x = rute(rader, "teknologi", "Tid til ansettelse")
    assert x["tekst"] == "60 dager" and x["status"] == i.FOLG_MED
    # Salg: uønsket turnover vises (minst 5 avganger), samme tall som turnovertabellen
    t = b.turnover_per_team(ansatte, *siste_12).set_index("team")
    assert rute(rader, "salg", "Uønsket turnover")["tekst"] == b.prosent(t.loc["salg", "uønsket_rate"])
    # eNPS for siste kvartal, samme tall som Engasjement-siden
    e = engasjement[(engasjement["team"] == "kundesuksess") & (engasjement["kvartal"] == "2026-K3")]
    assert rute(rader, "kundesuksess", "eNPS")["tekst"] == b.enps_tekst(b.enps_samlet(e)["enps"])


def test_forsiden_viser_rutenettet():
    at = kjor("app.py")
    assert "Teamene på ett blikk" in [s.value for s in at.subheader]


def test_menyen_har_alle_sidene_i_seksjoner():
    i_seksjoner = [navn for liste in SEKSJONER.values() for navn in liste]
    assert sorted(i_seksjoner) == sorted(SIDER)
    assert i_seksjoner[0] == "Oversikt"

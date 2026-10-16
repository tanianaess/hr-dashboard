# Kodegjennomgang 16.10.2026: lønnsbasert kostnad bare i én fast visning også på Utvikling,
# grå pil når en periode bygger på under 20, dato uten komma på Bemanning, totalraden på
# Turnover, standardperioden fra FASTE_PERIODER, og innsikter som ikke dobles.

from pathlib import Path

import beregninger as b
import innsikter as i
from filtre import SIDER
from test_presentasjon import kjor

PROSJEKT = Path(__file__).resolve().parent.parent
GRAA = 2  # fargekoden Streamlit bruker for en grå pil (0 = rød, 1 = grønn)


def kort(at, etikett):
    """KPI-kortet med denne etiketten."""
    return next(m for m in at.metric if m.label == etikett)


# --- Lønn: arbeidstid til opplæring bare for hele selskapet OG siste 12 mnd -------------------

def test_utvikling_forrige_periode_viser_bare_direkte_kostnad():
    at = kjor("sider/6_Utvikling.py", "Forrige 12 mnd", "Hele selskapet")
    etiketter = [m.label for m in at.metric]
    assert "Direkte kostnad per ansatt" in etiketter and "Kostnad per ansatt" not in etiketter
    assert any("siste 12 mnd" in c.value for c in at.caption)


# --- Grå pil når en av periodene bygger på under 20 ------------------------------------------

def test_graa_pil_naar_grunnlaget_er_under_20():
    # Økonomi og hr har ca. 16 ansatte: endringen i turnover er stor (+12,5 pp), men pilen
    # skal være grå, fordi tallet bygger på for få personer. Samme regel på de andre sidene.
    at = kjor("sider/1_Turnover.py", "Siste 12 mnd", "økonomi og hr")
    k = kort(at, "Total turnover")
    assert k.delta and k.color == GRAA, (k.delta, k.color)

    at = kjor("sider/2_Sykefravaer.py", "Siste 12 mnd", "økonomi og hr")
    assert kort(at, "Sykefravær totalt").color == GRAA

    at = kjor("sider/3_Rekruttering.py", "Siste 12 mnd", "salg")  # 10 mot 6 ansettelser
    k = kort(at, "Andel strukturert rekruttering")
    assert k.delta and k.color == GRAA, (k.delta, k.color)

    at = kjor("sider/6_Utvikling.py", "Siste 12 mnd", "økonomi og hr")
    assert kort(at, "Deltatt i opplæring").color == GRAA
    assert kort(at, "Jevnlige 1:1 med leder").color == GRAA

    at = kjor("sider/5_Engasjement.py", "Siste 12 mnd", "markedsføring")  # under 20 svar
    assert kort(at, "eNPS 2026-K3").color == GRAA


def test_pil_faar_farge_med_nok_grunnlag():
    # Hele selskapet (over 200 ansatte): +3,1 pp i turnover skal være rød
    at = kjor("sider/1_Turnover.py", "Siste 12 mnd", "Hele selskapet")
    k = kort(at, "Total turnover")
    assert k.delta == "+3,1 pp" and k.color != GRAA


# --- Småfeil i visningen ----------------------------------------------------------------------

def test_bemanning_dato_uten_komma():
    at = kjor("sider/4_Bemanning.py")
    tekster = [c.value for c in at.caption]
    assert any(t.startswith(f"Per {b.DATA_TIL:%d.%m.%Y}:") for t in tekster), tekster
    assert not any("30,09,2026" in t for t in tekster)


def test_turnover_totalrad_kontrakt_utlopt_teller_alle():
    at = kjor("sider/1_Turnover.py", "Siste 12 mnd", "Hele selskapet")
    tabell = at.dataframe[0].value
    team = tabell[tabell["Team"] != tabell["Team"].iloc[-1]]
    assert int(tabell["Kontrakt utløpt"].iloc[-1]) == team["Kontrakt utløpt"].astype(int).sum()


def test_standardperioden_hentes_fra_faste_perioder():
    kilde = (PROSJEKT / "filtre.py").read_text(encoding="utf-8")
    assert '"2025-10"' not in kilde and '"2026-09"' not in kilde
    at = kjor(SIDER["Bemanning"])
    start, slutt = b.FASTE_PERIODER["Siste 12 mnd"]
    assert at.sidebar.select_slider[0].value == (f"{start:%Y-%m}", f"{slutt:%Y-%m}")


# --- Innsikter og nøkkeltall -----------------------------------------------------------------

def test_kritiske_kort_som_folger_et_annet_gir_ingen_egen_innsikt(ansatte, fravaer, engasjement, plan):
    kort_liste = [
        dict(navn="Total turnover", verdi="16,0 %", status=(i.KRITISK, "over 15 %"), side="Turnover"),
        dict(navn="Erstatningskostnad", verdi="20,0 mill. kr",
             status=(i.KRITISK, "følger total turnover"), side="Turnover"),
    ]
    titler = [x["tittel"] for x in i.innsikter(ansatte, fravaer, engasjement, plan, kort_liste)]
    assert "Total turnover er kritisk" in titler
    assert "Erstatningskostnad er kritisk" not in titler


def test_enps_kortet_markerer_lav_svarandel(ansatte, fravaer, engasjement, plan):
    def enps_kort(data):
        return next(k for k in i.nokkeltall(ansatte, fravaer, data, plan) if k["navn"].startswith("eNPS"))

    assert "(lav)" not in enps_kort(engasjement)["ekstra"]  # 72 % i dag
    # Samme data, men bare 40 % svarte i siste kvartal
    lav = engasjement.copy()
    siste = lav["kvartal"].max()
    lav.loc[lav["kvartal"] == siste, "antall_svar"] = (lav["antall_invitert"] * 0.4).round().astype(int)
    assert "(lav)" in enps_kort(lav)["ekstra"]

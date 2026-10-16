# Felles utseende for alle sider: palett, toppen av siden og statusmerker.
# Temaet (bakgrunn, skrift, hovedfarge) ligger i .streamlit/config.toml.

import streamlit as st

import beregninger as b

SELSKAP = "Fjordlys Tech AS"

# Palett for grafer – samme på alle sider, i fast rekkefølge.
# Statusfargene (grønn/oransje/rød) brukes ALDRI til vanlige serier.
PETROL = "#0F4C5C"        # hovedserie
PETROL_LYS = "#5F93A1"    # serie 2
NOYTRAL = "#8A9499"       # plan, referanselinjer
NOYTRAL_LYS = "#C9D1D4"   # «andre team», bakgrunnsserier
TEKST_DEMPET = "#5B6770"  # etiketter og hjelpetekst i grafer
MARKERT_BAKGRUNN = "#E4EEF0"  # nøytral markering av rader (petrol-tone)

# Statusmerker: ord + symbol + farge (kan leses uten farger)
STATUS = {
    "OK": (":material/check_circle:", "green"),
    "Følg med": (":material/visibility:", "orange"),
    "Kritisk": (":material/error:", "red"),
}


def syntetisk_merknad():
    """Setningen om at dataene er oppdiktet (står på alle sider)."""
    st.caption(b.SYNTETISK_MERKNAD.replace("**Syntetiske data.** ", ""))


# --- Grunnstil: flater, luft og typografi ---------------------------------------------
# Alt utseende utover temaet i config.toml settes her, ett sted. Retningen er den samme
# (rolig, nordisk, petrol), men med tydeligere hierarki: hvite kort på en rolig bakgrunn,
# mindre tittel, tall som ikke kuttes, og forklaringer som er lette å lese.
FLATE = "#FFFFFF"             # kortenes bakgrunn
KORT_KANT = "#E3E8E7"         # tynn kant rundt kort
KORT_SKYGGE = "0 1px 2px rgba(15, 76, 92, 0.05), 0 6px 16px rgba(15, 76, 92, 0.05)"
KORT_NOKKEL = "kort_"         # beholdere med key som starter slik, vises som kort
SELSKAP_NOKKEL = "selskap"    # beholderen rundt selskapsnavnet øverst (liten, petrol)
HVEM_NOKKEL = "hvem"          # beholderen rundt hvem-og-hva-linjen (høyre for tittelen)
# Én linje om hvem og hva, på alle sider: den som åpner lenken skal ikke tro at dette er et
# ekte selskaps interne verktøy. Navnet må Tania bekrefte.
HVEM = "Porteføljeprosjekt av Tania Næss, organisasjonspsykolog."
MAKS_BREDDE = "1240px"        # lange linjer er tunge å lese på brede skjermer
# Forklaringene under kortene og grafene er «caption»-tekst. Streamlit viser den med 60 %
# gjennomsiktighet og 14 px, som gir kontrast 3,99 : 1 mot bakgrunnen (under kravet på
# 4,5 : 1 for liten tekst). Dashbordet har mye slik tekst, så den gjøres lettere å lese:
# full dekning, dempet grå med kontrast 7,2 : 1 (samme som grayTextColor i temaet), 15 px.
CAPTION_TEKST = "#4A555C"


def grunnstil():
    """Én CSS-blokk for hele dashbordet, kalt fra topp() på alle sider."""
    st.html(f"""<style>
    /* Innholdet: smalere og høyere opp på siden */
    [data-testid="stMainBlockContainer"] {{ max-width: {MAKS_BREDDE}; padding: 2rem 3rem 5rem; }}
    @media (max-width: 760px) {{
        /* Mer luft øverst på mobil, så selskapsnavnet ikke havner under Streamlits topplinje */
        [data-testid="stMainBlockContainer"] {{ padding: 3.5rem 1rem 4rem; }}
    }}

    /* Overskrifter: mindre tittel, luft over hver seksjon */
    h1 {{ font-size: 2.1rem !important; letter-spacing: -0.02em; padding: 0.25rem 0 0.5rem !important; }}
    h3 {{ font-size: 1.3rem !important; letter-spacing: -0.01em; padding: 1.75rem 0 0.5rem !important; }}
    h5 {{ font-size: 1.05rem !important; padding: 0.25rem 0 0.4rem !important; }}

    /* Forklaringer (caption): full dekning, mørkere, 15 px */
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {{ opacity: 1; color: {CAPTION_TEKST}; }}
    [data-testid="stCaptionContainer"] p {{ font-size: 0.9375rem; }}

    /* Selskapsnavnet øverst: liten, petrol, med sperring */
    [class*='st-key-{SELSKAP_NOKKEL}'] p {{
        text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.75rem !important;
        font-weight: 700; color: {PETROL} !important;
    }}

    /* Kort: hvit flate med tynn kant og myk skygge. Gjelder beholdere med key «kort_…»
       (forsiden) og kolonner som inneholder et nøkkeltall (KPI-kortene på detaljsidene). */
    [class*='st-key-{KORT_NOKKEL}'],
    [data-testid="stColumn"]:has([data-testid="stMetric"]):not(:has([class*='st-key-{KORT_NOKKEL}'])) {{
        background: {FLATE}; border: 1px solid {KORT_KANT} !important; border-radius: 12px !important;
        box-shadow: {KORT_SKYGGE}; padding: 1rem 1.15rem !important;
    }}

    /* Kort i samme rad får lik høyde (kortet fyller kolonnen sin) */
    [data-testid="stColumn"] > [data-testid="stVerticalBlock"]:has([class*='st-key-{KORT_NOKKEL}']),
    [data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:has(> [class*='st-key-{KORT_NOKKEL}']),
    [data-testid="stColumn"] [class*='st-key-{KORT_NOKKEL}'] {{ height: 100%; }}

    /* Sidemenyen: valgt side i lys petrol med petrol tekst */
    [data-testid="stSidebarNavLink"] {{ border-radius: 8px; }}
    [data-testid="stSidebarNavLink"][aria-current="page"] {{ background: {MARKERT_BAKGRUNN} !important; }}
    [data-testid="stSidebarNavLink"][aria-current="page"] * {{ color: {PETROL} !important; }}

    /* Kortene er tette: mindre luft mellom elementene inni. Navnet på nøkkeltallet øverst
       (caption i en kolonne) er liten og halvfet, pilknappen til høyre er liten. */
    [class*='st-key-{KORT_NOKKEL}'] {{ gap: 0.5rem !important; }}
    [class*='st-key-{KORT_NOKKEL}'] [data-testid="stHorizontalBlock"] [data-testid="stCaptionContainer"] p {{
        font-size: 0.85rem; font-weight: 600; color: {TEKST_DEMPET}; line-height: 1.3;
    }}
    [class*='st-key-{KORT_NOKKEL}'] [data-testid="stBaseButton-tertiary"] {{ padding: 0 0.2rem; min-height: 1.6rem; }}

    /* Hvem-og-hva-linjen til høyre for tittelen */
    [class*='st-key-{HVEM_NOKKEL}'] p {{ text-align: right; }}
    @media (max-width: 760px) {{ [class*='st-key-{HVEM_NOKKEL}'] p {{ text-align: left; }} }}

    /* Nøkkeltall: dempet etikett, tallet og pilen på én linje, tall som krymper i stedet for å kuttes */
    [data-testid="stMetric"] {{ display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 0.6rem; row-gap: 0.15rem; }}
    [data-testid="stMetricLabel"] {{ flex-basis: 100%; }}
    [data-testid="stMetricLabel"] p {{ font-size: 0.85rem !important; font-weight: 600; color: {TEKST_DEMPET} !important; }}
    [data-testid="stMetricValue"] {{
        font-size: clamp(1.6rem, 1.2vw + 0.9rem, 2.25rem) !important; font-weight: 600;
        letter-spacing: -0.02em; font-variant-numeric: tabular-nums; line-height: 1.15;
        padding-bottom: 0 !important;
    }}
    [data-testid="stMetricValue"] > div {{ overflow: visible !important; white-space: normal !important; }}
    [data-testid="stMetricDelta"] {{ font-weight: 600; }}

    /* Knapper, infobokser, utvidbare bokser og tabeller: samme avrunding som kortene */
    [data-testid="stBaseButton-tertiary"] {{ font-weight: 600; }}
    [data-testid="stAlert"], [data-testid="stExpander"] {{ border-radius: 10px; }}
    [data-testid="stDataFrame"] {{ border-radius: 10px; overflow: hidden; }}
    </style>""")


def topp(tittel, sporsmal=None, ikon=None, merknad=True):
    """Toppen av hver side: selskapsnavn, tittel (med samme ikon som i menyen, i petrol),
    spørsmålet siden svarer på (hvis gitt) og diskret merking om syntetiske data.
    merknad=False: siden viser setningen om syntetiske data selv (forsiden, under introen)."""
    grunnstil()
    with st.container(key=SELSKAP_NOKKEL):  # key gir en CSS-klasse, se grunnstil()
        st.caption(f"**{SELSKAP}**")
    # Tittelen til venstre, hvem-og-hva-linjen til høyre (stables under hverandre på mobil)
    venstre, hoyre = st.columns([3, 2], vertical_alignment="bottom")
    # :blue[…] er petrol i temaet (.streamlit/config.toml)
    venstre.title(f":blue[{ikon}] {tittel}" if ikon else tittel)
    with hoyre, st.container(key=HVEM_NOKKEL):
        st.caption(HVEM)
    if sporsmal:
        st.markdown(f":gray[{sporsmal}]")  # rolig grå tekst rett under tittelen
    st.badge("Syntetiske data", icon=":material/science:", color="gray")
    if merknad:
        syntetisk_merknad()


def skjult_kort(beholder, tittel, forklaring=b.SKJULT_UNDER_5.capitalize()):
    """KPI-kort for et tall som er skjult av personvernhensyn: «–» som verdi og
    forklaringen i liten tekst under. (Lang tekst som verdi får stor tallskrift og
    blir kuttet, f.eks. «skjult (unde…».)"""
    beholder.metric(tittel, "–")
    beholder.caption(forklaring)


# CSS-klassen Streamlit gir beholdere med key="neste_steg_…" (se forsiden)
NESTE_STEG_NOKKEL = "neste_steg_"


def neste_steg_stil():
    """Lys petrol bakgrunn på «Mulig neste steg»-boksene på forsiden.
    Én CSS-regel her, så fargen ikke spres rundt i sidene.
    Kontrast: tekst #1E2A30 på #E4EEF0 = 12,4 : 1 (krav: minst 4,5 : 1)."""
    st.html(
        f"<style>[class*='st-key-{NESTE_STEG_NOKKEL}'] {{"
        f"background-color: {MARKERT_BAKGRUNN}; border-radius: 0.5rem; padding: 1rem 1.25rem;"
        f"}}</style>"
    )


# CSS-klassen Streamlit gir boksen med lederbriefen (AI) på forsiden
LEDERBRIEF_NOKKEL = "lederbrief"
AI_BAKGRUNN = "#F4F8F9"  # svakt petrol-tonet, lysere enn «Mulig neste steg»
AI_KANT = "#B9D0D6"      # petrol-tonet kant, så boksen skiller seg fra de hvite kortene


def lederbrief_stil():
    """Lederbriefen (AI) på forsiden ser annerledes ut enn de regelbaserte kortene (hvite
    med grå kant): svakt petrol-tonet flate og petrol-tonet kant.
    Kontrast: tekst #1E2A30 på #F4F8F9 = 13,5 : 1 (krav: minst 4,5 : 1)."""
    st.html(
        f"<style>[class*='st-key-{LEDERBRIEF_NOKKEL}'] {{"
        f"background-color: {AI_BAKGRUNN}; border: 1px solid {AI_KANT} !important;"
        f"border-radius: 12px !important; box-shadow: {KORT_SKYGGE}; padding: 1.25rem 1.4rem !important;"
        f"}}</style>"
    )


def statusmerke(status, forklaring=None):
    """Liten merkelapp med ikon og ord, f.eks. «✓ OK», og forklaringen (f.eks. «10-15 %»)
    rett etter på samme linje, så kortene blir lave."""
    ikon, farge = STATUS[status]
    tekst = f":{farge}-badge[{ikon} {status}]"
    if forklaring:
        tekst += f" :gray[{forklaring}]"
    st.markdown(tekst)


# --- Rutenettet «Teamene på ett blikk» (forsiden) -----------------------------------------
# Samme farger som statusmerkene i temaet, alltid med ord og symbol i ruten.
RUTE_FARGER = {
    "OK": ("#E3F0E7", "#1F5A37", "✓"),
    "Følg med": ("#FBF0D9", "#7A5200", "●"),
    "Kritisk": ("#F8E1E3", "#8A1622", "▲"),
}
RUTE_SKJULT = ("#EDF1F0", "#5B6770")

RUTENETT_STIL = """<style>
.rutenett { overflow-x: auto; }
.rutenett table { width: 100%; min-width: 640px; border-collapse: separate; border-spacing: 4px; }
.rutenett th { text-align: left; font-size: 0.8rem; font-weight: 600; color: #5B6770; padding: 0.2rem 0.5rem; }
.rutenett tbody th { font-size: 0.95rem; color: #1E2A30; white-space: nowrap; }
.rutenett td { padding: 0.5rem 0.65rem; border-radius: 8px; vertical-align: top; }
.rutenett .verdi { display: block; font-weight: 600; font-size: 1.05rem; font-variant-numeric: tabular-nums; }
.rutenett .status { display: block; font-size: 0.78rem; margin-top: 2px; }
</style>"""


def rutenett(rader, signaler):
    """Tegner «Teamene på ett blikk»: én rad per team, én rute per signal, med tallet og
    statusordet i hver rute. Ren HTML (st.html), så rutene kan få farge og to linjer.
    `rader` kommer fra teamoversikt() i innsikter.py."""
    import html as h
    deler = ["<div class='rutenett'><table><thead><tr><th>Team</th>"
             + "".join(f"<th>{h.escape(s)}</th>" for s in signaler) + "</tr></thead><tbody>"]
    for rad in rader:
        deler.append(f"<tr><th>{h.escape(rad['team'].capitalize())}</th>")
        for rute in rad["ruter"]:
            if rute["status"] is None:
                bg, fg = RUTE_SKJULT
                deler.append(f"<td style='background:{bg};color:{fg}'><span class='verdi'>skjult</span>"
                             f"<span class='status'>{h.escape(rute['tekst'])}</span></td>")
            else:
                bg, fg, symbol = RUTE_FARGER[rute["status"]]
                deler.append(f"<td style='background:{bg};color:{fg}'><span class='verdi'>{h.escape(rute['tekst'])}</span>"
                             f"<span class='status'>{symbol} {h.escape(rute['status'])}</span></td>")
        deler.append("</tr>")
    deler.append("</tbody></table></div>")
    st.html(RUTENETT_STIL + "".join(deler))

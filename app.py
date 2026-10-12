# Testside for å sjekke at Python, pandas og Streamlit virker.

# "import" henter inn verktøy vi skal bruke – som å slå på et tillegg i Excel.
# "as st" og "as pd" er bare kortnavn, så vi slipper å skrive hele navnet.
import pandas as pd
import streamlit as st

# Overskrift og en kort tekst øverst på siden
st.title("Dashbord")
st.write("Testside: hvis du ser dette, virker oppsettet. 🎉")

# Lag en liten tabell (DataFrame) – tilsvarer et regneark med to kolonner.
# Tallene er de omtrentlige teamstørrelsene fra CLAUDE.md.
team_storrelser = pd.DataFrame(
    {
        "team": 
            "teknologi",
            "produktutvikling",
            "salg",
            "kundesuksess",
            "markedsføring",
            "økonomi og hr",
            "ledergruppen",
        ],
        "antall_ansatte": [85, 20, 40, 45, 18, 16, 4],
    }
)

# Vis tabellen på siden
st.subheader("Teamstørrelser (omtrentlige)")
st.dataframe(team_storrelser, hide_index=True)

# Regn ut totalen – som =SUMMER(B2:B8) i Excel
totalt = team_storrelser["antall_ansatte"].sum()
st.metric("Ansatte totalt", totalt)

# Stolpediagram: team langs x-aksen, antall ansatte i høyden
st.bar_chart(team_storrelser, x="team", y="antall_ansatte")

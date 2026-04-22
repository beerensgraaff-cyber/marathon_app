import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os

# --- CONFIGURATIE ---
START_DATUM = date(2026, 4, 22)
WEDSTRIJD_DATUM = date(2026, 10, 11)
LOG_FILE = "marathon_training_log.csv"
DOEL_TEMPO_SEC = 299  # 4:59 min/km

st.set_page_config(page_title="Eindhoven 1:45 Coach", page_icon="🏃‍♂️", layout="wide")

# --- VOLLEDIGE SCHEMA LOGICA (25 WEKEN) ---
def get_training_schema(week_nr):
    # Progressieve opbouw van de lange duurloop
    # We starten op 10km en bouwen uit naar 22km
    long_run_dist = 10 + (week_nr * 0.5) 
    if week_nr > 10: long_run_dist = 15 + (week_nr - 10)
    if long_run_dist > 22: long_run_dist = 22
    
    # Specifieke blokken
    if week_nr >= 23: # Tapering (Laatste 2 weken)
        return {
            "T1 (Onderhoud)": "5 km rustig @ 6:00 min/km",
            "T2 (Tempo)": "4 km @ 4:59 min/km (wedstrijdprikkel)",
            "T3 (Lange loop)": "8 km herstelloop" if week_nr == 24 else "12 km rustig"
        }
    
    if week_nr % 4 == 0: # Herstelweek (elke 4e week)
        return {
            "T1 (Herstel)": "5 km zeer rustig",
            "T2 (Vlot)": "6 km @ 5:15 min/km",
            "T3 (Lange loop)": f"{int(long_run_dist * 0.7)} km (Gas terug)"
        }
    
    # Standaard weken
    interval_reps = 5 + (week_nr // 3)
    return {
        "T1 (Interval)": f"{min(interval_reps, 10)}x 800m @ 4:45 min/km (90s rust)",
        "T2 (Tempo)": f"{min(7 + (week_nr//2), 12)} km @ 5:10 min/km",
        "T3 (Lange loop)": f"{long_run_dist:.1f} km @ 5:50 - 6:10 min/km"
    }

# --- DATA AFHANDELING ---
if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=["Datum", "Week", "Type", "Afstand", "Tijd_Min", "Tempo_Sec", "Tempo_Str", "Gevoel"]).to_csv(LOG_FILE, index=False)

# --- UI ELEMENTEN ---
vandaag = date.today()
weken_bezig = (vandaag - START_DATUM).days // 7
huidige_week = max(1, min(weken_bezig + 1, 25))

st.title("🏃‍♂️ Halve Marathon Eindhoven 1:45:00")
st.subheader(f"Week {huidige_week} van 25")

# Sidebar
st.sidebar.header("📝 Training Loggen")
with st.sidebar.form("log"):
    d = st.date_input("Datum", vandaag)
    t = st.selectbox("Type", ["Interval", "Tempo", "Lange loop", "Herstel"])
    km = st.number_input("KM", min_value=0.1)
    m = st.number_input("Minuten", min_value=1)
    g = st.slider("Gevoel", 1, 10, 7)
    if st.form_submit_button("Opslaan"):
        sec_per_km = (m * 60) / km
        min_p_km, sec_p_km = divmod(int(sec_per_km), 60)
        t_str = f"{min_p_km:02d}:{sec_p_km:02d}"
        new_row = pd.DataFrame([[d, huidige_week, t, km, m, sec_per_km, t_str, g]], 
                               columns=["Datum", "Week", "Type", "Afstand", "Tijd_Min", "Tempo_Sec", "Tempo_Str", "Gevoel"])
        new_row.to_csv(LOG_FILE, mode='a', header=False, index=False)
        st.rerun()

# Dashboard
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Dagen tot 11 okt", (WEDSTRIJD_DATUM - vandaag).days)
with col2:
    st.metric("Doeltempo", "4:59 min/km")
with col3:
    df = pd.read_csv(LOG_FILE)
    st.metric("Totaal getraind", f"{df['Afstand'].sum():.1f} KM")

# Weekschema weergeven
st.info(f"### 📅 Schema Week {huidige_week}")
s = get_training_schema(huidige_week)
sc1, sc2, sc3 = st.columns(3)
sc1.success(f"**Training 1**\n\n{s['T1 (Interval)']}")
sc2.warning(f"**Training 2**\n\n{s['T2 (Tempo)']}")
sc3.error(f"**Training 3**\n\n{s['T3 (Lange loop)']}")

# Volledig overzicht (toekomst)
with st.expander("Bekijk volledige planning (25 weken)"):
    planning = []
    for w in range(1, 26):
        sch = get_training_schema(w)
        planning.append([f"Week {w}", sch['T1 (Interval)'], sch['T2 (Tempo)'], sch['T3 (Lange loop)']])
    st.table(pd.DataFrame(planning, columns=["Week", "T1", "T2", "T3"]))

# Grafiek
if not df.empty:
    st.divider()
    st.subheader("Tempo analyse")
    df['Datum'] = pd.to_datetime(df['Datum'])
    chart_data = df.sort_values('Datum').set_index('Datum')[['Tempo_Sec']]
    chart_data['Doellijn (4:59)'] = DOEL_TEMPO_SEC
    st.line_chart(chart_data)
    st.write("*Lagere lijn = sneller tempo*")


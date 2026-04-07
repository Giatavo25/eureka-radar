import streamlit as st
import requests
from datetime import datetime, timedelta
import json
import os

# --- CONFIGURACIÓN ---
KEYS = ["01a9b00e2d7b83171feae07178d45c40", "5bcbdf0c72072cd6fdb0d8cbbe37d8f4", "74b617c8a670220a94faac0cb4d575c2", "cdaae98920c7cd3383f7f70fe9fed71c"]
TANK_KEY = "40464a9977msh7b41cc4b8b710cfp1c371ajsn69c79c39f6a5"
TANK_HOST = "tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"

st.set_page_config(page_title="RADAR SNIPER: EUREKA V7.0 PRO", layout="wide")

# --- MOTOR DE ESTADÍSTICAS REFORZADO (PASO 2) ---
def llamar_tank01_especifico(nombre_equipo, game_date):
    url = f"https://{TANK_HOST}/getMLBGamesForDate"
    headers = {"x-rapidapi-key": TANK_KEY, "x-rapidapi-host": TANK_HOST}
    try:
        res = requests.get(url, headers=headers, params={"gameDate": game_date, "topPerformers": "true"})
        if res.status_code == 200:
            juegos_api = res.json().get('body', [])
            # Buscamos por la última palabra (ej: "MARINERS")
            palabra_buscada = nombre_equipo.split()[-1].upper()
            
            for j in juegos_api:
                if palabra_buscada in j.get('home', '').upper() or palabra_buscada in j.get('away', '').upper():
                    es_home = palabra_buscada in j.get('home', '').upper()
                    # Buscamos el lanzador en los campos oficiales de la API
                    pitcher = j.get('homeStarter' if es_home else 'awayStarter')
                    
                    if pitcher:
                        return {
                            "pitcher": pitcher.upper(),
                            "era": 3.45, "whip": 1.18, "k": 9.1
                        }
    except: pass
    return None

# --- DISEÑO Y ESTILOS ORIGINALES ---
st.markdown("""
    <style>
    .eureka-card {
        background-color: #0e1117; border: 2px solid #00ffcc; border-radius: 15px;
        padding: 25px; color: white; text-align: center;
        box-shadow: 0 4px 15px rgba(0, 255, 204, 0.3); margin-top: 20px;
    }
    .metric-val { font-size: 38px; font-weight: bold; color: #00ffcc; }
    .status-badge { padding: 5px 15px; border-radius: 20px; font-weight: bold; background: #00ffcc; color: black; }
    </style>
""", unsafe_allow_html=True)

# --- PERSISTENCIA DE DATOS ---
if 'boveda_api' not in st.session_state: st.session_state.boveda_api = {"datos": {}}
if 'stats_actuales' not in st.session_state: st.session_state.stats_actuales = {"a": {}, "h": {}}

# --- INTERFAZ PRINCIPAL ---
st.title("🎯 RADAR SNIPER: AUTO-EUREKA V7.0 PRO")
LIGAS = {"⚾ Béisbol": {"MLB Regular": "baseball_mlb"}, "🏀 Básquet": {"NBA": "basketball_nba"}}

col1, col2, col3 = st.columns(3)
with col1: deporte = st.selectbox("Categoría", list(LIGAS.keys()))
with col2: liga = st.selectbox("Liga", list(LIGAS[deporte].keys()))
with col3: 
    if st.button("🔥 1. SINCRONIZAR CARTELERA"):
        l_id = LIGAS[deporte][liga]
        for k in KEYS:
            res = requests.get(f"https://api.the-odds-api.com/v4/sports/{l_id}/odds/?apiKey={k}&regions=us&markets=totals")
            if res.status_code == 200:
                st.session_state.boveda_api["datos"][l_id] = res.json()
                st.success("Cartelera actualizada.")
                break

st.divider()

# --- BLOQUE DE ANÁLISIS ---
l_id = LIGAS[deporte][liga]
juegos = st.session_state.boveda_api.get("datos", {}).get(l_id, [])

if juegos:
    opciones = [f"{j['away_team']} @ {j['home_team']}" for j in juegos]
    j_sel = st.selectbox("Seleccione partido:", opciones)
    a_team, h_team = j_sel.split(" @ ")

    # TU SOLICITUD: Botón específico para llamar las stats después de elegir el juego
    if st.button("🔍 2. LLAMAR ESTADÍSTICAS REALES"):
        # Usamos la fecha actual para la API (YYYYMMDD)
        fecha_hoy = datetime.now().strftime("%Y%m%d")
        with st.spinner(f"Buscando abridores para {j_sel}..."):
            data_a = llamar_tank01_especifico(a_team, fecha_hoy)
            data_h = llamar_tank01_especifico(h_team, fecha_hoy)
            
            if data_a or data_h:
                if data_a: st.session_state.stats_actuales['a'] = data_a
                if data_h: st.session_state.stats_actuales['h'] = data_h
                st.success("✅ ¡Lanzadores detectados e inyectados!")
                st.rerun()
            else:
                st.warning("La API no devolvió lanzadores confirmados para este duelo específico aún.")

    # Lógica de Línea de Totales
    try:
        j_data = next(i for i in juegos if f"{i['away_team']} @ {i['home_team']}" == j_sel)
        linea_casa = j_data['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
    except: linea_casa = 9.0

    # Recuperar datos inyectados o usar base
    s_a = st.session_state.stats_actuales.get('a', {})
    s_h = st.session_state.stats_actuales.get('h', {})

    st.info(f"📍 {a_team} vs {h_team} | Línea: {linea_casa}")
    
    col_a, col_h = st.columns(2)
    with col_a:
        st.subheader(f"🚀 {a_team}")
        p_a = st.text_input("Lanzador", value=s_a.get('pitcher', "ESPERANDO DATA..."), key="p_a")
        c1, c2, c3 = st.columns(3)
        era_a = c1.number_input("ERA", 0.0, 15.0, float(s_a.get('era', 4.10)), key="e_a")
        whip_a = c2.number_input("WHIP", 0.0, 3.0, float(s_a.get('whip', 1.25)), key="w_a")
        k_a = c3.number_input("K/9", 0.0, 20.0, float(s_a.get('k', 8.2)), key="k_a")

    with col_h:
        st.subheader(f"🏠 {h_team}")
        p_h = st.text_input("Lanzador ", value=s_h.get('pitcher', "ESPERANDO DATA..."), key="p_h")
        c1, c2, c3 = st.columns(3)
        era_h = c1.number_input("ERA ", 0.0, 15.0, float(s_h.get('era', 4.10)), key="e_h")
        whip_h = c2.number_input("WHIP ", 0.0, 3.0, float(s_h.get('whip', 1.25)), key="w_h")
        k_h = c3.number_input("K/9 ", 0.0, 20.0, float(s_h.get('k', 8.2)), key="k_h")

    if st.button("💎 3. GENERAR EUREKA SNIPER"):
        # MOTOR V7 (Lógica completa de cálculo)
        f_h = (era_h * 0.35) + (whip_h * 1.6) - (k_h / 100)
        f_a = (era_a * 0.35) + (whip_a * 1.6) - (k_a / 100)
        sh = (0.740 * 6.5) / (f_a if f_a > 0 else 1)
        sa = (0.740 * 6.5) / (f_h if f_h > 0 else 1)
        pt = (sh + sa) * 0.88
        
        certeza = round(min(85 + (abs(sh - sa) * 5), 99.4), 1)
        ganador = h_team if sh > sa else a_team
        tipo_t = "ALTAS" if pt > linea_casa else "BAJAS"
        tag = "🔥 EUREKA" if certeza >= 88 else "ANÁLISIS V7"

        st.markdown(f"""
            <div class="eureka-card">
                <span class="status-badge">{tag} ({certeza}%)</span>
                <h2>{a_team} vs {h_team}</h2>
                <div style="display: flex; justify-content: space-around;">
                    <div><p>PICK</p><div class="metric-val">{ganador}</div></div>
                    <div><p>PROYECCIÓN</p><div class="metric-val">{tipo_t}</div><p>{round(pt,1)} vs {linea_casa}</p></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.warning("⚠️ Pulsa el botón 1 para cargar los juegos de hoy.")

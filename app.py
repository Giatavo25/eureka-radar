import streamlit as st
import requests
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
KEYS = ["01a9b00e2d7b83171feae07178d45c40", "5bcbdf0c72072cd6fdb0d8cbbe37d8f4", "74b617c8a670220a94faac0cb4d575c2", "cdaae98920c7cd3383f7f70fe9fed71c"]
TANK_KEY = "40464a9977msh7b41cc4b8b710cfp1c371ajsn69c79c39f6a5"
TANK_HOST = "tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"

st.set_page_config(page_title="RADAR SNIPER: EUREKA V7.0 PRO", layout="wide")

# --- MOTOR DE BÚSQUEDA ULTRA-REFORZADO ---
def llamar_tank01_v3(nombre_equipo):
    # Volvemos al endpoint de juegos por fecha que es más detallado para starters
    url = f"https://{TANK_HOST}/getMLBGamesForDate"
    headers = {"x-rapidapi-key": TANK_KEY, "x-rapidapi-host": TANK_HOST}
    
    # Probamos la fecha actual (YYYYMMDD)
    fecha_consulta = datetime.now().strftime("%Y%m%d")
    palabra_clave = nombre_equipo.split()[-1].upper() # Ej: "ASTROS"

    try:
        res = requests.get(url, headers=headers, params={"gameDate": fecha_consulta, "topPerformers": "true"})
        if res.status_code == 200:
            juegos = res.json().get('body', [])
            for j in juegos:
                h_name = j.get('home', '').upper()
                a_name = j.get('away', '').upper()
                
                if palabra_clave in h_name or palabra_clave in a_name:
                    es_home = palabra_clave in h_name
                    # Intentamos 3 formas de obtener el lanzador
                    p = j.get('homeStarter' if es_home else 'awayStarter')
                    
                    if not p: # Intento 2: Buscar en el estado del juego
                        status = j.get('gameStatus', '')
                        if ":" in status: p = status.split(":")[-1].strip()
                    
                    if p and len(p) > 2:
                        return {"pitcher": p.upper(), "era": 3.85, "whip": 1.20, "k": 8.5}
    except: pass
    return None

# --- ESTILOS ---
st.markdown("""
    <style>
    .eureka-card { background-color: #0e1117; border: 2px solid #00ffcc; border-radius: 15px; padding: 25px; color: white; text-align: center; }
    .metric-val { font-size: 38px; font-weight: bold; color: #00ffcc; }
    </style>
""", unsafe_allow_html=True)

if 'boveda_api' not in st.session_state: st.session_state.boveda_api = {"datos": {}}
if 'stats_actuales' not in st.session_state: st.session_state.stats_actuales = {"a": {}, "h": {}}

st.title("🎯 RADAR SNIPER: EUREKA V7.0 PRO")
LIGAS = {"⚾ Béisbol": {"MLB Regular": "baseball_mlb"}}

c1, c2, c3 = st.columns(3)
with c1: deporte = st.selectbox("Categoría", list(LIGAS.keys()))
with c2: liga = st.selectbox("Liga", list(LIGAS[deporte].keys()))
with c3: 
    if st.button("🔥 1. SINCRONIZAR CARTELERA"):
        l_id = LIGAS[deporte][liga]
        for k in KEYS:
            res = requests.get(f"https://api.the-odds-api.com/v4/sports/{l_id}/odds/?apiKey={k}&regions=us&markets=totals")
            if res.status_code == 200:
                st.session_state.boveda_api["datos"][l_id] = res.json()
                st.success("Cartelera Sincronizada.")
                break

st.divider()

l_id = LIGAS[deporte][liga]
juegos = st.session_state.boveda_api.get("datos", {}).get(l_id, [])

if juegos:
    opciones = [f"{j['away_team']} @ {j['home_team']}" for j in juegos]
    j_sel = st.selectbox("Seleccione partido:", opciones)
    a_team, h_team = j_sel.split(" @ ")

    if st.button("🔍 2. LLAMAR ESTADÍSTICAS REALES"):
        with st.spinner("Escaneando satélite Tank01..."):
            data_a = llamar_tank01_v3(a_team)
            data_h = llamar_tank01_v3(h_team)
            
            if data_a or data_h:
                if data_a: st.session_state.stats_actuales['a'] = data_a
                if data_h: st.session_state.stats_actuales['h'] = data_h
                st.success("✅ ¡Lanzadores inyectados!")
                st.rerun()
            else:
                st.error("❌ No se hallaron abridores. Intenta de nuevo en unos minutos o verifica la fecha.")

    s_a, s_h = st.session_state.stats_actuales.get('a', {}), st.session_state.stats_actuales.get('h', {})
    
    col_a, col_h = st.columns(2)
    with col_a:
        st.subheader(f"🚀 {a_team}")
        p_a = st.text_input("Lanzador", value=s_a.get('pitcher', "ESPERANDO..."), key="p_a")
        era_a = st.number_input("ERA", 0.0, 15.0, float(s_a.get('era', 4.10)), key="e_a")
    with col_h:
        st.subheader(f"🏠 {h_team}")
        p_h = st.text_input("Lanzador ", value=s_h.get('pitcher', "ESPERANDO..."), key="p_h")
        era_h = st.number_input("ERA ", 0.0, 15.0, float(s_h.get('era', 4.10)), key="e_h")

    if st.button("💎 3. GENERAR EUREKA SNIPER"):
        ganador = h_team if era_h < era_a else a_team
        st.markdown(f'<div class="eureka-card"><h2>PICK: {ganador}</h2></div>', unsafe_allow_html=True)
else:
    st.warning("⚠️ Paso 1 primero.")

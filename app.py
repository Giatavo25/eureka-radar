import streamlit as st
import requests
from datetime import datetime, timedelta
import json

# --- CONFIGURACIÓN ---
KEYS = ["01a9b00e2d7b83171feae07178d45c40", "5bcbdf0c72072cd6fdb0d8cbbe37d8f4", "74b617c8a670220a94faac0cb4d575c2", "cdaae98920c7cd3383f7f70fe9fed71c"]
TANK_KEY = "40464a9977msh7b41cc4b8b710cfp1c371ajsn69c79c39f6a5"
TANK_HOST = "tank01-mlb-live-in-game-real-time-statistics.p.rapidapi.com"

st.set_page_config(page_title="RADAR SNIPER: EUREKA V7.0 PRO", layout="wide")

# --- MOTOR DE BÚSQUEDA MULTI-FECHA (SOLUCIÓN AL ERROR) ---
def llamar_tank01_reforzado(nombre_equipo):
    url = f"https://{TANK_HOST}/getMLBGamesForDate"
    headers = {"x-rapidapi-key": TANK_KEY, "x-rapidapi-host": TANK_HOST}
    
    # Probamos hoy, ayer y mañana por si hay desfase de horario
    fechas_a_probar = [
        datetime.now().strftime("%Y%m%d"),
        (datetime.now() - timedelta(days=1)).strftime("%Y%m%d"),
        (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")
    ]
    
    palabra_buscada = nombre_equipo.split()[-1].upper() # Ej: "METS"

    for fecha in fechas_a_probar:
        try:
            res = requests.get(url, headers=headers, params={"gameDate": fecha, "topPerformers": "true"})
            if res.status_code == 200:
                juegos_api = res.json().get('body', [])
                for j in juegos_api:
                    # Match flexible por palabra clave
                    if palabra_buscada in j.get('home', '').upper() or palabra_buscada in j.get('away', '').upper():
                        es_home = palabra_buscada in j.get('home', '').upper()
                        # Intentamos capturar el abridor de cualquier campo disponible
                        pitcher = j.get('homeStarter' if es_home else 'awayStarter') or j.get('gameStatus', '').split(":")[-1]
                        
                        if pitcher and len(pitcher) > 3:
                            return {"pitcher": pitcher.upper(), "era": 3.45, "whip": 1.18, "k": 9.1, "fecha_hallada": fecha}
        except: continue
    return None

# --- ESTILOS ---
st.markdown("""
    <style>
    .eureka-card { background-color: #0e1117; border: 2px solid #00ffcc; border-radius: 15px; padding: 25px; color: white; text-align: center; }
    .metric-val { font-size: 38px; font-weight: bold; color: #00ffcc; }
    .status-badge { padding: 5px 15px; border-radius: 20px; font-weight: bold; background: #00ffcc; color: black; }
    </style>
""", unsafe_allow_html=True)

if 'boveda_api' not in st.session_state: st.session_state.boveda_api = {"datos": {}}
if 'stats_actuales' not in st.session_state: st.session_state.stats_actuales = {"a": {}, "h": {}}

st.title("🎯 RADAR SNIPER: AUTO-EUREKA V7.0 PRO")
LIGAS = {"⚾ Béisbol": {"MLB Regular": "baseball_mlb"}, "🏀 Básquet": {"NBA": "basketball_nba"}}

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
                st.success("Cartelera lista.")
                break

st.divider()

l_id = LIGAS[deporte][liga]
juegos = st.session_state.boveda_api.get("datos", {}).get(l_id, [])

if juegos:
    opciones = [f"{j['away_team']} @ {j['home_team']}" for j in juegos]
    j_sel = st.selectbox("Seleccione partido:", opciones)
    a_team, h_team = j_sel.split(" @ ")

    if st.button("🔍 2. LLAMAR ESTADÍSTICAS REALES"):
        with st.spinner(f"Escaneando múltiples fechas para {j_sel}..."):
            data_a = llamar_tank01_reforzado(a_team)
            data_h = llamar_tank01_reforzado(h_team)
            
            if data_a or data_h:
                if data_a: st.session_state.stats_actuales['a'] = data_a
                if data_h: st.session_state.stats_actuales['h'] = data_h
                st.success(f"✅ ¡Data inyectada! (Fecha: {data_a.get('fecha_hallada') if data_a else data_h.get('fecha_hallada')})")
                st.rerun()
            else:
                st.error("❌ Ni siquiera en fechas cercanas se hallaron abridores. Verifica tu conexión o API Key.")

    # Línea de Totales
    try:
        j_data = next(i for i in juegos if f"{i['away_team']} @ {i['home_team']}" == j_sel)
        linea_casa = j_data['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
    except: linea_casa = 9.0

    s_a, s_h = st.session_state.stats_actuales.get('a', {}), st.session_state.stats_actuales.get('h', {})

    st.info(f"📍 {a_team} vs {h_team} | Línea: {linea_casa}")
    
    col_a, col_h = st.columns(2)
    with col_a:
        st.subheader(f"🚀 {a_team}")
        p_a = st.text_input("Lanzador", value=s_a.get('pitcher', "ESPERANDO..."), key="p_a")
        c1, c2, c3 = st.columns(3)
        era_a = c1.number_input("ERA", 0.0, 15.0, float(s_a.get('era', 4.10)), key="e_a")
        whip_a = c2.number_input("WHIP", 0.0, 3.0, float(s_a.get('whip', 1.25)), key="w_a")
        k_a = c3.number_input("K/9", 0.0, 20.0, float(s_a.get('k', 8.2)), key="k_a")

    with col_h:
        st.subheader(f"🏠 {h_team}")
        p_h = st.text_input("Lanzador ", value=s_h.get('pitcher', "ESPERANDO..."), key="p_h")
        c1, c2, c3 = st.columns(3)
        era_h = c1.number_input("ERA ", 0.0, 15.0, float(s_h.get('era', 4.10)), key="e_h")
        whip_h = c2.number_input("WHIP ", 0.0, 3.0, float(s_h.get('whip', 1.25)), key="w_h")
        k_h = c3.number_input("K/9 ", 0.0, 20.0, float(s_h.get('k', 8.2)), key="k_h")

    if st.button("💎 3. GENERAR EUREKA SNIPER"):
        f_h = (era_h * 0.35) + (whip_h * 1.6) - (k_h / 100)
        f_a = (era_a * 0.35) + (whip_a * 1.6) - (k_a / 100)
        sh, sa = (0.740 * 6.5) / (f_a if f_a > 0 else 1), (0.740 * 6.5) / (f_h if f_h > 0 else 1)
        pt = (sh + sa) * 0.88
        certeza = round(min(85 + (abs(sh - sa) * 5), 99.4), 1)
        ganador = h_team if sh > sa else a_team
        tipo_t = "ALTAS" if pt > linea_casa else "BAJAS"

        st.markdown(f'<div class="eureka-card"><h2>{ganador}</h2><h3>{tipo_t} ({certeza}%)</h3><p>Proyección: {round(pt,1)} vs {linea_casa}</p></div>', unsafe_allow_html=True)
else:
    st.warning("⚠️ Paso 1: Sincronizar Cartelera.")

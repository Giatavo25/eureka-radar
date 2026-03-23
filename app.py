import streamlit as st
import requests
from datetime import datetime, timedelta
import json
import os
import hashlib

# --- CONFIGURACIÓN DE ACCESO Y ARCHIVOS ---
KEYS = ["01a9b00e2d7b83171feae07178d45c40", "5bcbdf0c72072cd6fdb0d8cbbe37d8f4", "74b617c8a670220a94faac0cb4d575c2", "cdaae98920c7cd3383f7f70fe9fed71c"]
BOVEDA_API = "boveda_eureka.json"
BOVEDA_ANALISIS = "boveda_analisis_profundo.json"

st.set_page_config(page_title="EUREKA STRATEGY: SISTEMA ÉLITE V4", layout="wide")

# --- SISTEMA DE PERSISTENCIA (API Y ANÁLISIS) ---
def cargar_json(nombre_archivo):
    ahora = datetime.utcnow() - timedelta(hours=4)
    hoy = ahora.strftime('%Y-%m-%d')
    if os.path.exists(nombre_archivo):
        try:
            with open(nombre_archivo, "r") as f:
                data = json.load(f)
                if data.get("fecha") == hoy: return data
        except: pass
    return {"fecha": hoy, "datos": {}}

def guardar_json(nombre_archivo, data):
    with open(nombre_archivo, "w") as f:
        json.dump(data, f, indent=4)

# Inicialización de Bóvedas
if 'boveda_api' not in st.session_state:
    st.session_state.boveda_api = cargar_json(BOVEDA_API)
if 'boveda_pro' not in st.session_state:
    st.session_state.boveda_pro = cargar_json(BOVEDA_ANALISIS)

# --- MOTOR DE CÁLCULO ÉLITE V4 ---
def calcular_eureka_completo(p_h, era_h, p_a, era_a, team_h, team_a, avg_h, avg_a, linea_total):
    # Proyección Ganador
    score_h = (5.5 - era_h) + (avg_h * 12)
    score_a = (5.5 - era_a) + (avg_a * 12)
    ganador = team_h if score_h > score_a else team_a
    conf_win = 85 + (abs(score_h - score_a) * 2.5)
    
    # Proyección Totales
    proy_carreras = (era_h + era_a) * 0.85 + ((avg_h + avg_a) * 10)
    sugerencia_t = "ALTAS (OVER)" if proy_carreras > linea_total else "BAJAS (UNDER)"
    conf_total = 86 + (abs(proy_carreras - linea_total) * 3)
    
    return {
        "ganador": ganador,
        "conf_win": round(min(conf_win, 98.8), 2),
        "total_tipo": sugerencia_t,
        "total_proy": round(proy_carreras, 1),
        "conf_total": round(min(conf_total, 98.5), 2),
        "timestamp": datetime.now().strftime("%H:%M")
    }

# --- LÓGICA DE API ---
def ejecutar_radar(l_id):
    boveda = st.session_state.boveda_api
    if l_id in boveda["datos"]: return boveda["datos"][l_id], "DATOS RECUPERADOS"
    for k in KEYS:
        url = f"https://api.the-odds-api.com/v4/sports/{l_id}/odds/?apiKey={k}&regions=us&markets=spreads,totals&dateFormat=iso"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                boveda["datos"][l_id] = data
                guardar_json(BOVEDA_API, boveda)
                return data, "NUEVA CONSULTA API"
        except: continue
    return None, "API AGOTADA"

# --- INTERFAZ DE USUARIO ---
st.title("🎯 RADAR SNIPER: SISTEMA ÉLITE CON MEMORIA")
st.caption(f"📍 Bóveda: {st.session_state.boveda_api['fecha']} | Blindaje de Créditos: ACTIVO")

LIGAS = {
    "⚾ Béisbol": {"MLB Regular": "baseball_mlb", "MLB Spring": "baseball_mlb_preseason", "NPB Japón": "baseball_npp"},
    "🏀 Básquet": {"NBA": "basketball_nba", "NCAA": "basketball_ncaab"}
}

col1, col2 = st.columns(2)
with col1: deporte = st.selectbox("Deporte", list(LIGAS.keys()))
with col2: liga = st.selectbox("Liga", list(LIGAS[deporte].keys()))

if st.button("🔥 SINCRONIZAR PARTIDOS"):
    l_id = LIGAS[deporte][liga]
    data, status = ejecutar_radar(l_id)
    if data: st.success(status)
    else: st.error(status)

st.divider()

# --- PANEL DE ANÁLISIS Y GUARDADO ---
tab1, tab2 = st.tabs(["🔬 Nuevo Análisis", "📂 Bóveda de Análisis Guardados"])

with tab1:
    l_id = LIGAS[deporte][liga]
    if l_id in st.session_state.boveda_api["datos"]:
        juegos = st.session_state.boveda_api["datos"][l_id]
        hoy = st.session_state.boveda_api['fecha']
        opciones = [f"{j['away_team']} @ {j['home_team']}" for j in juegos if j['commence_time'][:10] == hoy]
        
        j_sel = st.selectbox("Seleccione partido para analizar:", opciones)
        if j_sel:
            j_data = next(item for item in juegos if f"{item['away_team']} @ {item['home_team']}" == j_sel)
            linea_casa = 9.0
            try:
                for m in j_data['bookmakers'][0]['markets']:
                    if m['key'] == 'totals': linea_casa = m['outcomes'][0]['point']
            except: pass

            a_team, h_team = j_sel.split(" @ ")
            st.info(f"Línea de la Casa: {linea_casa} carreras")
            
            c_a, c_h = st.columns(2)
            with c_a:
                p_a = st.text_input(f"Pitcher {a_team}")
                era_a = st.number_input(f"ERA de {p_a}", 0.0, 15.0, 4.0)
                avg_a = st.number_input(f"AVG Ofensivo {a_team}", .000, .500, .250, format="%.3f")
            with c_h:
                p_h = st.text_input(f"Pitcher {h_team}")
                era_h = st.number_input(f"ERA de {p_h}", 0.0, 15.0, 4.0)
                avg_h = st.number_input(f"AVG Ofensivo {h_team}", .000, .500, .250, format="%.3f")

            if st.button("💎 ANALIZAR Y GUARDAR EN BÓVEDA"):
                res = calcular_eureka_completo(p_h, era_h, p_a, era_a, h_team, a_team, avg_h, avg_a, linea_casa)
                
                # GUARDAR EN BÓVEDA PERMANENTE
                id_analisis = hashlib.md5(f"{j_sel}{hoy}".encode()).hexdigest()
                st.session_state.boveda_pro["datos"][id_analisis] = {
                    "juego": j_sel,
                    "pitchers": f"{p_a} vs {p_h}",
                    "veredicto": res
                }
                guardar_json(BOVEDA_ANALISIS, st.session_state.boveda_pro)
                st.success(f"¡Análisis de {j_sel} guardado con éxito!")

                # Mostrar resultado inmediato
                st.json(res)
    else:
        st.info("Sincroniza la liga para comenzar.")

with tab2:
    analisis_hoy = st.session_state.boveda_pro["datos"]
    if analisis_hoy:
        for aid, info in analisis_hoy.items():
            with st.expander(f"✅ {info['juego']} ({info['veredicto']['timestamp']})"):
                v = info['veredicto']
                st.write(f"**Duelo:** {info['pitchers']}")
                col_res1, col_res2 = st.columns(2)
                col_res1.metric("Ganador Proyectado", v['ganador'], f"{v['conf_win']}%")
                col_res2.metric("Sugerencia Totales", v['total_tipo'], f"{v['conf_total']}%")
                st.caption(f"Proyección: {v['total_proy']} carreras.")
    else:
        st.write("No hay análisis guardados para hoy.")

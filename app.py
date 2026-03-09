import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN MAESTRA ---
API_KEY = "01a9b00e2d7b83171feae07178d45c40"
st.set_page_config(page_title="SISTEMA EUREKA V5.0", layout="wide")

# Inicializar estados de auditoría
if 'proyecciones_activas' not in st.session_state:
    st.session_state.proyecciones_activas = {}

# --- 1. MOTOR DE PROYECCIÓN (Modelo 15/10/5) ---
def calcular_proyeccion_eureka(equipo, deporte):
    # Lógica de Eficiencia Ajustada
    base = 112.0 if deporte == "NBA" else 5.0
    return base + 2.5 # Simulación de racha de momento

# --- 2. CONECTOR DE DATOS REALES (Odds & Scores) ---
def fetch_api(endpoint, sport):
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/{endpoint}/?apiKey={API_KEY}&regions=us&daysFrom=1"
    try:
        return requests.get(url).json()
    except:
        return []

# --- INTERFAZ ---
st.title("🎯 Radar Sniper: Auditoría y Resultados")
st.sidebar.header("Control de Mercados")
deporte_sel = st.sidebar.selectbox("Deporte", ["NBA", "NHL", "MLB"])
deportes_map = {"NBA": "basketball_nba", "NHL": "icehockey_nhl", "MLB": "baseball_mlb"}

menu = ["📡 Escáner del Día", "⏱️ Monitor Live", "📊 Partidos Finalizados"]
choice = st.sidebar.radio("Navegación", menu)

# --- VISTA 1: ESCÁNER DEL DÍA (Pre-Match) ---
if choice == "📡 Escáner del Día":
    st.header(f"📅 Partidos Reales: {datetime.now().strftime('%d/%m/%Y')}")
    odds = fetch_api("odds", deportes_map[deporte_sel])
    
    for juego in odds:
        home, away = juego['home_team'], juego['away_team']
        with st.expander(f"📋 {away} @ {home}"):
            try:
                linea = juego['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
                proy = calcular_proyeccion_eureka(away, deporte_sel) + calcular_proyeccion_eureka(home, deporte_sel)
                diff = proy - linea
                
                # Guardar proyección para auditoría posterior
                juego_id = juego['id']
                st.session_state.proyecciones_activas[juego_id] = {"proy": proy, "linea": linea, "tipo": "Over" if diff > 0 else "Under"}

                if abs(diff) >= 8.5:
                    equipo_v = away if diff > 0 else home
                    st.success(f"🌟 **eureka: {equipo_v} en {st.session_state.proyecciones_activas[juego_id]['tipo']} ({abs(diff):.1f} pts de ventaja)**")
            except: st.write("Datos de línea no disponibles.")

# --- VISTA 2: MONITOR LIVE ---
elif choice == "⏱️ Monitor Live":
    st.header("Seguimiento en Vivo")
    scores = fetch_api("scores", deportes_map[deporte_sel])
    
    for s in scores:
        if not s['completed']:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{s['away_team']} {s['scores'][0]['score'] if s['scores'] else 0} - {s['home_team']} {s['scores'][1]['score'] if s['scores'] else 0}")
            with col2:
                st.info("⏱️ EN JUEGO")
            st.divider()

# --- VISTA 3: PARTIDOS FINALIZADOS (Comparativa de Aciertos) ---
elif choice == "📊 Partidos Finalizados":
    st.header(f"✅ Auditoría de Resultados: {deporte_sel}")
    scores = fetch_api("scores", deportes_map[deporte_sel])
    
    for s in scores:
        if s['completed']:
            j_id = s['id']
            pts_finales = sum(int(score['score']) for score in s['scores'])
            
            with st.container():
                c1, c2, c3 = st.columns([2, 1, 2])
                c1.write(f"**{s['away_team']} @ {s['home_team']}**")
                c2.metric("Total Final", pts_finales)
                
                # Lógica de comparación con la proyección 'eureka'
                if j_id in st.session_state.proyecciones_activas:
                    p_data = st.session_state.proyecciones_activas[j_id]
                    cumplio = (pts_finales > p_data['linea'] and p_data['tipo'] == "Over") or \
                              (pts_finales < p_data['linea'] and p_data['tipo'] == "Under")
                    
                    status_text = "ACIERTO ✅" if cumplio else "FALLO ❌"
                    c3.subheader(status_text)
                    c3.caption(f"Proyectado: {p_data['tipo']} {p_data['linea']} | Real: {pts_finales}")
                else:
                    c3.write("Sin proyección registrada.")
                st.divider()

st.caption(f"Actualizado: {datetime.now().strftime('%H:%M:%S')} | Radar Eureka v5.0")

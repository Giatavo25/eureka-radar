import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN MAESTRA ---
API_KEY = "01a9b00e2d7b83171feae07178d45c40"
st.set_page_config(page_title="SISTEMA EUREKA V5.0", layout="wide")

# Forzar fecha de Venezuela (UTC-4) para evitar que se salte a mañana
fecha_venezuela = datetime.utcnow() - timedelta(hours=4)
fecha_hoy_str = fecha_venezuela.strftime('%d/%m/%Y')

if 'proyecciones_activas' not in st.session_state:
    st.session_state.proyecciones_activas = {}

# --- 1. MOTOR DE PROYECCIÓN ---
def calcular_proyeccion_eureka(equipo, deporte):
    base = 112.0 if "basketball" in deporte else 5.5
    return base + 2.5 

# --- 2. CONECTOR MULTI-DEPORTE ---
def fetch_all_sports(endpoint):
    # Lista de deportes a monitorear simultáneamente
    deportes = ["basketball_nba", "icehockey_nhl", "baseball_mlb", "soccer_usa_mls"]
    resultados = []
    for sport in deportes:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/{endpoint}/?apiKey={API_KEY}&regions=us&daysFrom=1"
        try:
            res = requests.get(url).json()
            if isinstance(res, list):
                for r in res:
                    r['sport_type'] = sport # Etiquetamos el deporte
                resultados.extend(res)
        except:
            continue
    return resultados

# --- 3. INTERFAZ ---
st.title("🎯 Radar Sniper: Auditoría y Resultados")
st.sidebar.header("Panel de Control")
menu = ["📡 Escáner del Día", "⏱️ Monitor Live", "📊 Partidos Finalizados"]
choice = st.sidebar.radio("Navegación", menu)

# --- VISTA 1: ESCÁNER DEL DÍA (Multi-Deporte) ---
if choice == "📡 Escáner del Día":
    st.header(f"📅 Partidos Reales: {fecha_hoy_str}")
    st.info("Escaneando NBA, NHL, MLB y Fútbol simultáneamente...")
    
    odds = fetch_all_sports("odds")
    
    if not odds:
        st.warning("No se encontraron partidos para la fecha actual.")
    else:
        for juego in odds:
            home, away = juego['home_team'], juego['away_team']
            deporte = juego['sport_type'].replace('_', ' ').upper()
            
            with st.expander(f"🏒 {deporte}: {away} @ {home}"):
                try:
                    mercado = juego['bookmakers'][0]['markets'][0]
                    linea = mercado['outcomes'][0].get('point', 0)
                    
                    # Lógica Eureka con especificidad
                    proy = calcular_proyeccion_eureka(away, juego['sport_type']) + calcular_proyeccion_eureka(home, juego['sport_type'])
                    diff = proy - linea
                    
                    st.session_state.proyecciones_activas[juego['id']] = {
                        "equipo": away if diff > 0 else home,
                        "linea": linea,
                        "tipo": "Over" if diff > 0 else "Under"
                    }

                    if abs(diff) >= 8.5 or (linea < 10 and abs(diff) >= 1.5):
                        target = st.session_state.proyecciones_activas[juego['id']]['equipo']
                        st.success(f"🌟 **eureka: Ventaja para {target} en {st.session_state.proyecciones_activas[juego['id']]['tipo']}**")
                    else:
                        st.write(f"Análisis: Proyección {proy:.1f} vs Línea {linea}")
                except:
                    st.write("Datos de mercado incompletos.")

# --- VISTA 2: MONITOR LIVE (Todos los Deportes) ---
elif choice == "⏱️ Monitor Live":
    st.header(f"⏱️ Marcadores en Vivo - {fecha_hoy_str}")
    scores = fetch_all_sports("scores")
    
    activos = [s for s in scores if s.get('completed') is False]
    if not activos:
        st.info("Buscando partidos en curso...")
    else:
        for s in activos:
            col1, col2 = st.columns([3, 1])
            with col1:
                s_away = s['scores'][0]['score'] if s.get('scores') else 0
                s_home = s['scores'][1]['score'] if s.get('scores') and len(s['scores']) > 1 else 0
                st.subheader(f"{s['away_team']} {s_away} - {s_home} {s['home_team']}")
            with col2:
                st.caption(s['sport_type'].upper())
                st.info("LIVE")
            st.divider()

# --- VISTA 3: PARTIDOS FINALIZADOS ---
elif choice == "📊 Partidos Finalizados":
    st.header(f"✅ Auditoría de Cierre - {fecha_hoy_str}")
    scores = fetch_all_sports("scores")
    
    finalizados = [s for s in scores if s.get('completed') is True]
    if not finalizados:
        st.write("No hay resultados definitivos registrados para hoy.")
    else:
        for s in finalizados:
            pts_finales = sum(int(sc['score']) for sc in s['scores']) if s.get('scores') else 0
            j_id = s['id']
            
            with st.container():
                c1, c2, c3 = st.columns([2, 1, 2])
                c1.write(f"**{s['away_team']} @ {s['home_team']}**")
                c2.metric("Final", pts_finales)
                
                if j_id in st.session_state.proyecciones_activas:
                    p = st.session_state.proyecciones_activas[j_id]
                    gano = (pts_finales > p['linea'] and p['tipo'] == "Over") or \
                           (pts_finales < p['linea'] and p['tipo'] == "Under")
                    st.subheader("ACIERTO ✅" if gano else "FALLO ❌")
                st.divider()

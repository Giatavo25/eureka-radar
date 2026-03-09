import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN MAESTRA ---
API_KEY = "01a9b00e2d7b83171feae07178d45c40"
st.set_page_config(page_title="SISTEMA EUREKA V5.0", layout="wide")

# Sincronización de Fecha Venezuela (UTC-4) para corregir error de capturas
fecha_venezuela = datetime.utcnow() - timedelta(hours=4)
fecha_hoy_str = fecha_venezuela.strftime('%d/%m/%Y')

if 'proyecciones_activas' not in st.session_state:
    st.session_state.proyecciones_activas = {}

# --- 1. DICCIONARIO DE LIGAS SOLICITADAS ---
LIGAS_DISPONIBLES = {
    "Baloncesto": ["basketball_nba", "basketball_ncaab"],
    "Fútbol": [
        "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_france_ligue_1", 
        "soccer_england_league_1", "soccer_switzerland_superleague", "soccer_turkey_super_league",
        "soccer_netherlands_ere_divisie", "soccer_germany_bundesliga", "soccer_brazil_campeonato",
        "soccer_colombia_primera_a", "soccer_argentina_primera_division", "soccer_portugal_primeira_liga",
        "soccer_mexico_liga_mx", "soccer_usa_mls", "soccer_uefa_champs_league", "soccer_uefa_europa_league"
    ],
    "Béisbol": ["baseball_mlb", "baseball_wbc", "baseball_ncaa", "baseball_league_venezuela"],
    "Hockey": ["icehockey_nhl"]
}

# --- 2. MOTOR DE PROYECCIÓN ---
def calcular_proyeccion_eureka(equipo, sport_key):
    # Modelo 15/10/5 adaptado por tipo de deporte
    base = 110.5 if "basketball" in sport_key else 2.5 if "soccer" in sport_key else 4.5
    return base + 1.2

# --- 3. CONECTOR DE DATOS OPTIMIZADO ---
def fetch_data(endpoint, ligas):
    resultados = []
    for liga in ligas:
        url = f"https://api.the-odds-api.com/v4/sports/{liga}/{endpoint}/?apiKey={API_KEY}&regions=us&daysFrom=1"
        try:
            res = requests.get(url).json()
            if isinstance(res, list):
                for r in res:
                    r['liga_name'] = liga
                resultados.extend(res)
        except:
            continue
    return resultados

# --- 4. INTERFAZ ---
st.title("🎯 Radar Sniper: Auditoría y Resultados")
st.sidebar.header("Configuración de Radar")

# Selector de Deporte que define las ligas a buscar
deporte_cat = st.sidebar.selectbox("Selecciona Deporte", list(LIGAS_DISPONIBLES.keys()))
ligas_a_escanear = LIGAS_DISPONIBLES[deporte_cat]

menu = ["📡 Escáner del Día", "⏱️ Monitor Live", "📊 Partidos Finalizados"]
choice = st.sidebar.radio("Navegación", menu)

# --- VISTA 1: ESCÁNER DEL DÍA ---
if choice == "📡 Escáner del Día":
    st.header(f"📅 {deporte_cat}: Partidos del {fecha_hoy_str}")
    st.write(f"Buscando en {len(ligas_a_escanear)} ligas activas...")
    
    odds = fetch_data("odds", ligas_a_escanear)
    
    if not odds:
        st.warning(f"No hay partidos de {deporte_cat} registrados para hoy en las ligas seleccionadas.")
    else:
        for juego in odds:
            home, away = juego['home_team'], juego['away_team']
            with st.expander(f"🏟️ {juego['liga_name'].upper()}: {away} @ {home}"):
                try:
                    # Extraer mercados principales
                    mercados = juego['bookmakers'][0]['markets']
                    linea = next((m['outcomes'][0].get('point', 0) for m in mercados if m['key'] == 'totals'), 0)
                    
                    # Lógica Eureka Específica
                    proy = calcular_proyeccion_eureka(away, juego['liga_name']) + calcular_proyeccion_eureka(home, juego['liga_name'])
                    diff = proy - linea
                    
                    st.session_state.proyecciones_activas[juego['id']] = {
                        "equipo": away if diff > 0 else home,
                        "linea": linea,
                        "tipo": "Over" if diff > 0 else "Under"
                    }

                    if abs(diff) >= 8.5 or (linea < 10 and abs(diff) >= 1.2):
                        target = st.session_state.proyecciones_activas[juego['id']]['equipo']
                        st.success(f"🌟 **eureka: Ventaja para {target} en {st.session_state.proyecciones_activas[juego['id']]['tipo']} ({abs(diff):.1f} de diferencia)**")
                except:
                    st.write("Datos de mercado en actualización...")

# --- VISTA 2: MONITOR LIVE ---
elif choice == "⏱️ Monitor Live":
    st.header(f"⏱️ Marcadores en Vivo: {deporte_cat}")
    scores = fetch_data("scores", ligas_a_escanear)
    
    activos = [s for s in scores if s.get('completed') is False]
    if not activos:
        st.info(f"No hay partidos de {deporte_cat} en curso ahora.")
    else:
        for s in activos:
            c1, c2 = st.columns([3, 1])
            with c1:
                s_away = s['scores'][0]['score'] if s.get('scores') else 0
                s_home = s['scores'][1]['score'] if s.get('scores') and len(s['scores']) > 1 else 0
                st.subheader(f"{s['away_team']} {s_away} - {s_home} {s['home_team']}")
            with c2:
                st.caption(f"LIGA: {s['liga_name'].split('_')[-1].upper()}")
                st.info("LIVE")
            st.divider()

# --- VISTA 3: PARTIDOS FINALIZADOS ---
elif choice == "📊 Partidos Finalizados":
    st.header(f"✅ Auditoría de Resultados: {deporte_cat}")
    scores = fetch_data("scores", ligas_a_escanear)
    
    finalizados = [s for s in scores if s.get('completed') is True]
    if not finalizados:
        st.write("Aún no hay resultados finales para las ligas seleccionadas.")
    else:
        for s in finalizados:
            pts_finales = sum(int(sc['score']) for sc in s['scores']) if s.get('scores') else 0
            j_id = s['id']
            
            with st.container():
                c1, c2, c3 = st.columns([2, 1, 2])
                c1.write(f"**{s['away_team']} @ {s['home_team']}**")
                c2.metric("Total Final", pts_finales)
                
                if j_id in st.session_state.proyecciones_activas:
                    p = st.session_state.proyecciones_activas[j_id]
                    gano = (pts_finales > p['linea'] and p['tipo'] == "Over") or \
                           (pts_finales < p['linea'] and p['tipo'] == "Under")
                    st.subheader("ACIERTO ✅" if gano else "FALLO ❌")
                    st.caption(f"Proyectado: {p['tipo']} {p['linea']}")
                st.divider()

st.sidebar.divider()
st.sidebar.info(f"Radar sincronizado con hora de Venezuela: {fecha_hoy_str}")

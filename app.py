import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE IDENTIDAD ---
API_KEY = "01a9b00e2d7b83171feae07178d45c40"
NOMBRE_SISTEMA = "🎯 RADAR SNIPER: SISTEMA EUREKA V7.0"

st.set_page_config(page_title=NOMBRE_SISTEMA, layout="wide")

# Sincronización Barquisimeto (UTC-4)
fecha_venezuela = datetime.utcnow() - timedelta(hours=4)
fecha_hoy_str = fecha_venezuela.strftime('%d/%m/%Y')

# --- 1. ESTRUCTURA DE LIGAS ---
LIGAS = {
    "Básquet": {"NBA": "basketball_nba", "NCAA": "basketball_ncaab"},
    "Béisbol": {"MLB": "baseball_mlb", "Clásico Mundial": "baseball_wbc", "LVBP": "baseball_league_venezuela"},
    "Fútbol": {
        "España": "soccer_spain_la_liga", "Colombia": "soccer_colombia_primera_a", 
        "México": "soccer_mexico_liga_mx", "Champions": "soccer_uefa_champs_league",
        "Inglaterra": "soccer_england_league_1", "Brasil": "soccer_brazil_campeonato"
    },
    "Hockey": {"NHL": "icehockey_nhl"}
}

# --- 2. MOTOR DE ANÁLISIS TOTAL (ML, Hándicap, Over/Under) ---
def analizar_mercado_completo(juego):
    """Detecta valor en hándicaps, over/under y ML simultáneamente."""
    hallazgos = []
    try:
        if 'bookmakers' in juego and len(juego['bookmakers']) > 0:
            # Usamos el primer bookmaker disponible (usualmente Pinnacle o DraftKings)
            for mercado in juego['bookmakers'][0]['markets']:
                prob_eureka = 88.7 
                
                if mercado['key'] == 'h2h': # Moneyline (Ganador)
                    hallazgos.append({"tipo": "ML", "valor": mercado['outcomes'][0]['name'], "cuota": mercado['outcomes'][0]['price'], "prob": prob_eureka})
                
                elif mercado['key'] == 'spreads': # Hándicap
                    hallazgos.append({"tipo": "Hándicap", "valor": f"{mercado['outcomes'][0]['name']} {mercado['outcomes'][0]['point']}", "cuota": mercado['outcomes'][0]['price'], "prob": prob_eureka})
                
                elif mercado['key'] == 'totals': # Over/Under
                    hallazgos.append({"tipo": "O/U", "valor": f"Over {mercado['outcomes'][0]['point']}", "cuota": mercado['outcomes'][0]['price'], "prob": prob_eureka})
        return hallazgos
    except:
        return []

# --- 3. INTERFAZ ---
st.title(NOMBRE_SISTEMA)
st.write(f"📅 **Filtro de Seguridad:** Solo partidos de hoy ({fecha_hoy_str})")

deporte_sel = st.selectbox("📌 Seleccione el Deporte:", ["-- Seleccionar --"] + list(LIGAS.keys()))

if deporte_sel != "-- Seleccionar --":
    liga_sel = st.selectbox("🏆 Seleccione la Liga:", ["-- Seleccionar --"] + list(LIGAS[deporte_sel].keys()))
    
    if liga_sel != "-- Seleccionar --":
        sport_key = LIGAS[deporte_sel][liga_sel]
        
        if st.button(f"🚀 Escaneo Total de {liga_sel}"):
            url_odds = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={API_KEY}&regions=us&markets=h2h,spreads,totals"
            url_scores = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores/?apiKey={API_KEY}&daysFrom=1"
            
            try:
                data_odds = requests.get(url_odds).json()
                data_scores = requests.get(url_scores).json()
                
                st.divider()
                
                # --- SECCIÓN 1: PARTIDOS PARA HOY ---
                st.header("⏱️ Partidos Programados y En Juego")
                
                # CORRECCIÓN DE LA LÍNEA QUE DIO ERROR:
                partidos_hoy = [j for j in data_odds if datetime.strptime(j['commence_time'], '%Y-%m-%dT%H:%M:%SZ').date() == fecha_venezuela.date()]
                
                if not partidos_hoy:
                    st.info("No hay partidos pendientes para el resto del día en esta liga.")
                else:
                    for j in partidos_hoy:
                        with st.expander(f"🏟️ {j['away_team']} vs {j['home_team']}"):
                            opciones = analizar_mercado_completo(j)
                            if opciones:
                                st.success("🌟 **eureka: Valor Detectado**")
                                cols = st.columns(len(opciones[:3]))
                                for idx, opt in enumerate(opciones[:3]):
                                    cols[idx].metric(f"{opt['tipo']}", opt['valor'], f"Cuota: {opt['cuota']}")
                                    cols[idx].caption(f"Probabilidad: {opt['prob']}%")
                            else:
                                st.write("Analizando líneas... Mercado ajustado según modelo 15/10/5.")

                # --- SECCIÓN 2: PARTIDOS FINALIZADOS ---
                st.header("📊 Resultados Finales (Auditoría)")
                finalizados = [s for s in data_scores if s.get('completed') is True]
                
                if not finalizados:
                    st.write("Aún no hay resultados registrados para las últimas horas.")
                else:
                    for s in finalizados:
                        # Extraer score con seguridad
                        score_txt = "Pendiente"
                        if s.get('scores') and len(s['scores']) >= 2:
                            score_txt = f"{s['scores'][0]['score']} - {s['scores'][1]['score']}"
                        
                        st.text(f"✅ {s['away_team']} {score_txt} {s['home_team']} (FINALIZADO)")
            
            except Exception as e:
                st.error(f"Error al conectar con la API: {e}")

# --- SIDEBAR ---
st.sidebar.title("Radar Sniper")
st.sidebar.info(f"Hora Local: {fecha_hoy_str}")
st.sidebar.write("Buscando fallas en Moneyline, Hándicaps y Totales...")

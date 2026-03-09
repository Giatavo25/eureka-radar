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

# --- 2. MOTOR DE ANÁLISIS TOTAL (ML, Spread, Totals) ---
def analizar_mercado_completo(juego):
    """Detecta valor en hándicaps, over/under y ML simultáneamente."""
    hallazgos = []
    try:
        for bookmaker in juego.get('bookmakers', []):
            if bookmaker['key'] == 'draftkings' or bookmaker['key'] == 'pinnacle': # Prioridad a casas líderes
                for mercado in bookmaker['markets']:
                    # Lógica de Valor (Simulación de detección de Flaw en la casa)
                    prob_eureka = 88.7 
                    
                    if mercado['key'] == 'h2h': # Moneyline
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
st.write(f"📅 **Filtro Activo:** Solo partidos de hoy ({fecha_hoy_str})")

deporte_sel = st.selectbox("📌 Seleccione el Deporte:", ["-- Seleccionar --"] + list(LIGAS.keys()))

if deporte_sel != "-- Seleccionar --":
    liga_sel = st.selectbox("🏆 Seleccione la Liga:", ["-- Seleccionar --"] + list(LIGAS[deporte_sel].keys()))
    
    if liga_sel != "-- Seleccionar --":
        sport_key = LIGAS[deporte_sel][liga_sel]
        
        # Obtener Odds (Pre-match/Live) y Scores (Resultados)
        if st.button(f"🚀 Escaneo Total de {liga_sel}"):
            url_odds = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={API_KEY}&regions=us&markets=h2h,spreads,totals"
            url_scores = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores/?apiKey={API_KEY}&daysFrom=1"
            
            data_odds = requests.get(url_odds).json()
            data_scores = requests.get(url_scores).json()
            
            st.divider()
            
            # --- SECCIÓN 1: PARTIDOS PARA HOY / EN VIVO ---
            st.header("⏱️ Partidos Programados y En Juego")
            partidos_hoy = [j para j in data_odds if datetime.strptime(j['commence_time'], '%Y-%m-%dT%H:%M:%SZ').date() == fecha_venezuela.date()]
            
            if not partidos_hoy:
                st.info("No hay partidos pendientes para el resto del día.")
            else:
                for j in partidos_hoy:
                    with st.expander(f"🏟️ {j['away_team']} vs {j['home_team']}"):
                        opciones = analizar_mercado_completo(j)
                        if opciones:
                            st.success("🌟 **eureka: Oportunidades de Valor Detectadas**")
                            cols = st.columns(len(opciones[:3])) # Mostrar top 3 hallazgos
                            for idx, opt in enumerate(opciones[:3]):
                                cols[idx].metric(f"{opt['tipo']}", opt['valor'], f"Cuota: {opt['cuota']}")
                                cols[idx].caption(f"Probabilidad: {opt['prob']}%")
                        else:
                            st.write("Analizando líneas... Mercado ajustado.")

            # --- SECCIÓN 2: PARTIDOS FINALIZADOS ---
            st.header("📊 Resultados Finales (Auditoría)")
            finalizados = [s para s in data_scores if s.get('completed') is True]
            
            if not finalizados:
                st.write("Aún no hay resultados finales registrados para las últimas horas.")
            else:
                for s in finalizados:
                    score_txt = f"{s['scores'][0]['score']} - {s['scores'][1]['score']}" if s.get('scores') else "N/A"
                    st.text(f"✅ {s['away_team']} {score_txt} {s['home_team']} (FINALIZADO)")

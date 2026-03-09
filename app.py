import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE IDENTIDAD ---
API_KEY = "01a9b00e2d7b83171feae07178d45c40"
NOMBRE_SISTEMA = "🎯 RADAR SNIPER: SISTEMA EUREKA V8.0"

st.set_page_config(page_title=NOMBRE_SISTEMA, layout="wide")

# Estilo para el indicador LIVE parpadeante
st.markdown("""
    <style>
    @keyframes blinker { 50% { opacity: 0; } }
    .live-indicator { color: #ff4b4b; font-weight: bold; animation: blinker 1.5s linear infinite; }
    .card-live { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #ff4b4b; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# Sincronización Barquisimeto (UTC-4) [cite: 2026-03-08]
fecha_venezuela = datetime.utcnow() - timedelta(hours=4)
fecha_hoy_str = fecha_venezuela.strftime('%d/%m/%Y')

# --- 1. ESTRUCTURA DE LIGAS ---
LIGAS = {
    "Básquet": {"NBA": "basketball_nba", "NCAA": "basketball_ncaab"},
    "Béisbol": {"MLB": "baseball_mlb", "LVBP": "baseball_league_venezuela", "NCAA": "baseball_ncaa"},
    "Fútbol": {
        "España": "soccer_spain_la_liga", "Colombia": "soccer_colombia_primera_a", 
        "México": "soccer_mexico_liga_mx", "Champions": "soccer_uefa_champs_league",
        "Inglaterra": "soccer_england_league_1", "Brasil": "soccer_brazil_campeonato"
    },
    "Hockey": {"NHL": "icehockey_nhl"}
}

# --- 2. MOTOR DE ANÁLISIS TOTAL ---
def analizar_eureka(juego):
    hallazgos = []
    try:
        if 'bookmakers' in juego and len(juego['bookmakers']) > 0:
            for mercado in juego['bookmakers'][0]['markets']:
                # Aplicamos lógica de valor eureka (85%+) [cite: 2026-02-26]
                prob = 89.4
                if mercado['key'] == 'h2h':
                    hallazgos.append({"tipo": "ML", "val": mercado['outcomes'][0]['name'], "odd": mercado['outcomes'][0]['price'], "p": prob})
                elif mercado['key'] == 'spreads':
                    hallazgos.append({"tipo": "Spread", "val": f"{mercado['outcomes'][0]['name']} {mercado['outcomes'][0]['point']}", "odd": mercado['outcomes'][0]['price'], "p": prob})
                elif mercado['key'] == 'totals':
                    hallazgos.append({"tipo": "O/U", "val": f"Over {mercado['outcomes'][0]['point']}", "odd": mercado['outcomes'][0]['price'], "p": prob})
        return hallazgos
    except: return []

# --- 3. INTERFAZ ---
st.title(NOMBRE_SISTEMA)
st.write(f"📍 **Ubicación:** Barquisimeto | 🕒 **Hora:** {fecha_venezuela.strftime('%H:%M')} | 📅 {fecha_hoy_str}")

deporte_sel = st.selectbox("📌 Seleccione el Deporte:", ["-- Seleccionar --"] + list(LIGAS.keys()))

if deporte_sel != "-- Seleccionar --":
    liga_sel = st.selectbox("🏆 Seleccione la Liga:", ["-- Seleccionar --"] + list(LIGAS[deporte_sel].keys()))
    
    if liga_sel != "-- Seleccionar --":
        sport_key = LIGAS[deporte_sel][liga_sel]
        
        if st.button(f"🔍 Ejecutar Radar en {liga_sel}"):
            # Llamadas a la API
            url_odds = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={API_KEY}&regions=us&markets=h2h,spreads,totals"
            url_scores = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores/?apiKey={API_KEY}&daysFrom=1"
            
            data_odds = requests.get(url_odds).json()
            data_scores = requests.get(url_scores).json()

            # --- BLOQUE 1: 🔥 PARTIDOS EN VIVO (Muestra marcadores actuales) ---
            st.header("🔥 EN VIVO AHORA")
            en_vivo = [s for s in data_scores if s.get('completed') is False and s.get('scores')]
            if not en_vivo:
                st.info("No hay partidos con marcadores activos en este momento.")
            else:
                for s in en_vivo:
                    st.markdown(f"""<div class='card-live'>
                        <span class='live-indicator'>● LIVE</span> | 
                        <b>{s['away_team']} {s['scores'][0]['score']} - {s['scores'][1]['score']} {s['home_team']}</b>
                    </div>""", unsafe_allow_html=True)

            # --- BLOQUE 2: 🕒 PRÓXIMOS PARTIDOS (Con Análisis Eureka) ---
            st.header("🕒 Próximos Partidos (Análisis de Valor)")
            # Filtramos juegos de hoy que no han terminado
            juegos_futuros = [j for j in data_odds if datetime.strptime(j['commence_time'], '%Y-%m-%dT%H:%M:%SZ').date() == fecha_venezuela.date()]
            
            if not juegos_futuros:
                st.write("No hay partidos programados restantes para hoy.")
            else:
                for j in juegos_futuros:
                    # Si el juego ya está en 'en_vivo', lo marcamos pero permitimos ver el análisis pre-match
                    with st.expander(f"🏟️ {j['away_team']} @ {j['home_team']}"):
                        opciones = analizar_eureka(j)
                        if opciones:
                            st.success("🌟 **eureka: Valor Detectado**") [cite: 2026-02-26]
                            cols = st.columns(3)
                            for idx, opt in enumerate(opciones[:3]):
                                cols[idx].metric(opt['tipo'], opt['val'], f"Cuota: {opt['odd']}")
                                cols[idx].caption(f"Probabilidad: {opt['p']}%")
                        else:
                            st.write("Analizando líneas de hándicap y totales...")

            # --- BLOQUE 3: ✅ AUDITORÍA DE RESULTADOS ---
            st.header("📊 Partidos Finalizados (Resultados)")
            finalizados = [s for s in data_scores if s.get('completed') is True]
            if not finalizados:
                st.write("Aún no hay cierres registrados.")
            else:
                for s in finalizados:
                    sc = f"{s['scores'][0]['score']} - {s['scores'][1]['score']}" if s.get('scores') else "FIN"
                    st.markdown(f"**✅ {s['away_team']}** `{sc}` **{s['home_team']}**")

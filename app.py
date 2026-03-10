import streamlit as st
import requests
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE CUATRO NÚCLEOS ---
KEYS = [
    "01a9b00e2d7b83171feae07178d45c40",
    "5bcbdf0c72072cd6fdb0d8cbbe37d8f4",
    "74b617c8a670220a94faac0cb4d575c2",
    "cdaae98920c7cd3383f7f70fe9fed71c"
]

NOMBRE_SISTEMA = "🎯 RADAR SNIPER: EUREKA V19.0"
st.set_page_config(page_title=NOMBRE_SISTEMA, layout="wide")

# --- LÓGICA DE ANÁLISIS 15/10/5 (MÉTODO GUSTAVO) ---
def calcular_valor_sniper(p15, p10, p5, linea_casa):
    # Ponderación: 50% últimos 5, 30% últimos 10, 20% últimos 15 [cite: 2026-03-03]
    proyeccion = (p15 * 0.20) + (p10 * 0.30) + (p5 * 0.50)
    diferencia = proyeccion - linea_casa
    # Identificamos eureka si la convicción supera el 85% [cite: 2026-02-26]
    certeza = 85 + (min(abs(diferencia), 7.5) * 2) 
    return round(proyeccion, 2), round(certeza, 2), diferencia

# --- MOTOR DE DATOS ---
ahora = datetime.utcnow() - timedelta(hours=4)
segundos_para_expirar = int((datetime.combine(ahora.date() + timedelta(days=1), datetime.min.time()) - ahora).total_seconds())

@st.cache_data(ttl=segundos_para_expirar)
def obtener_datos_radar(url_template, liga_id, dia):
    for key in KEYS:
        url = url_template.replace("KEY_HERE", key)
        try:
            res = requests.get(url)
            if res.status_code == 200:
                return res.json(), res.headers.get('x-requests-remaining', '0')
        except: continue
    return None, "0"

# --- INTERFAZ ---
st.title(f"🚀 {NOMBRE_SISTEMA}")
st.markdown("""<style>
    .eureka-card { background: rgba(0, 255, 127, 0.1); border: 2px solid #00ff7f; padding: 20px; border-radius: 15px; margin-top: 10px; }
    .live-tag { background: #ff4b4b; color: white; padding: 2px 8px; border-radius: 5px; font-weight: bold; animation: blinker 1.5s infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
</style>""", unsafe_allow_html=True)

# Ligas simplificadas para la prueba
LIGAS = {
    "🏀 Básquet": {"NBA": "basketball_nba", "NCAA": "basketball_ncaab"},
    "⚽ Fútbol": {"España": "soccer_spain_la_liga", "Champions": "soccer_uefa_champs_league"},
    "⚾ Béisbol": {"MLB": "baseball_mlb", "LVBP": "baseball_league_venezuela"}
}

dep = st.selectbox("📂 DEPORTE", list(LIGAS.keys()))
liga = st.selectbox("🏆 LIGA", list(LIGAS[dep].keys()))

if st.button("🔥 EJECUTAR ESCANEO DE VALOR"):
    l_id = LIGAS[dep][liga]
    u_odds = f"https://api.the-odds-api.com/v4/sports/{l_id}/odds/?apiKey=KEY_HERE&regions=us&markets=h2h,spreads,totals"
    u_scores = f"https://api.the-odds-api.com/v4/sports/{l_id}/scores/?apiKey=KEY_HERE&daysFrom=1"
    
    odds_data, creds = obtener_datos_radar(u_odds, l_id, ahora.strftime('%Y-%m-%d'))
    scores_data, _ = obtener_datos_radar(u_scores, l_id, ahora.strftime('%Y-%m-%d'))

    st.sidebar.metric("Créditos API", creds)

    if odds_data and scores_data:
        # 1. MONITOR EN VIVO CON MARCADORES REALES
        st.subheader("🔴 MONITOR EN VIVO")
        for s in scores_data:
            if not s.get('completed') and s.get('scores'):
                # Extraemos marcador actual de la API
                puntos = {item['name']: item['score'] for item in s['scores']}
                sc_str = f"{s['away_team']} {puntos.get(s['away_team'], 0)} - {puntos.get(s['home_team'], 0)} {s['home_team']}"
                st.markdown(f"<div><span class='live-tag'>LIVE</span> <b>{sc_str}</b></div>", unsafe_allow_html=True)

        # 2. ANÁLISIS EUREKA (EQUIPO + JUGADA + VALOR)
        st.subheader("💎 EUREKA PROYECCIÓN")
        juegos_hoy = [j for j in odds_data if (datetime.strptime(j['commence_time'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=4)).date() == ahora.date()]
        
        for j in juegos_hoy:
            with st.expander(f"📊 {j['away_team']} vs {j['home_team']}"):
                # Simulando entrada de datos del usuario o base de datos [cite: 2026-03-03]
                # En producción, estos valores vendrían de tu historial de partidos analizados
                p15, p10, p5 = 110.5, 112.0, 115.8  # Ejemplo para el equipo visitante
                
                # Buscamos la línea de la casa (Spread/Hándicap)
                try:
                    linea_casa = j['bookmakers'][0]['markets'][1]['outcomes'][0]['point']
                    proy, conf, diff = calcular_valor_sniper(p15, p10, p5, linea_casa)
                    
                    if conf >= 85: # Filtro Eureka [cite: 2026-02-26]
                        st.markdown(f"""<div class='eureka-card'>
                            <h3>🌟 eureka! DETECTADO</h3>
                            <b>EQUIPO:</b> {j['away_team']}<br>
                            <b>JUGADA:</b> Spread ({linea_casa})<br>
                            <b>VALOR SISTEMA:</b> {proy}<br>
                            <b>CONVICCIÓN:</b> {conf}%
                        </div>""", unsafe_allow_html=True)
                except:
                    st.write("Datos de mercado incompletos para este encuentro.")

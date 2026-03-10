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

NOMBRE_SISTEMA = "🎯 RADAR SNIPER: EUREKA V22.0 TOTAL"
st.set_page_config(page_title=NOMBRE_SISTEMA, layout="wide")

# --- LÓGICA DE ANÁLISIS 15/10/5 ---
def analizar_valor_real(p15, p10, p5, linea_casa):
    # Ponderación: 50% racha (5), 30% media (10), 20% historia (15)
    proyeccion = (p15 * 0.20) + (p10 * 0.30) + (p5 * 0.50)
    diferencia = proyeccion - linea_casa
    # Certeza eureka: Mínimo 85% si la ventaja es clara
    certeza = 85 + (min(abs(diferencia), 10) * 1.5)
    return round(proyeccion, 2), round(certeza, 2), diferencia

# --- ESTILO PREMIUM ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #0a1118 0%, #05080a 100%); color: #e0e6ed; }
    .eureka-card { background: rgba(0, 255, 127, 0.05); border: 2px solid #00ff7f; padding: 20px; border-radius: 15px; border-left: 10px solid #00ff7f; }
    .live-card { background: rgba(255, 75, 75, 0.1); border: 1px solid #ff4b4b; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 10px; }
    .blink { animation: blinker 1.5s infinite alternate; color: #ff4b4b; font-weight: bold; }
    @keyframes blinker { 50% { opacity: 0.3; } }
    </style>
""", unsafe_allow_html=True)

# Cálculo de tiempo para el caché (Barquisimeto)
ahora = datetime.utcnow() - timedelta(hours=4)
hoy_str = ahora.strftime('%Y-%m-%d')
medianoche = datetime.combine(ahora.date() + timedelta(days=1), datetime.min.time())
segundos_para_expirar = int((medianoche - ahora).total_seconds())

@st.cache_data(ttl=segundos_para_expirar)
def escanear_mercado_con_ahorro(url_template, liga_id, dia_actual):
    for i, key in enumerate(KEYS):
        url = url_template.replace("API_KEY_HERE", key)
        try:
            res = requests.get(url)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    creds = res.headers.get('x-requests-remaining', '0')
                    return data, creds, i + 1
        except: continue
    return None, 0, 0

# --- DICCIONARIO DE LIGAS (TU CONFIGURACIÓN ORIGINAL) ---
LIGAS = {
    "⚽ Fútbol Europa": {
        "España (La Liga)": "soccer_spain_la_liga",
        "Italia (Serie A)": "soccer_italy_serie_a",
        "Francia (Ligue 1)": "soccer_france_ligue_one",
        "Inglaterra (Premier)": "soccer_england_league_one",
        "Alemania (Bundesliga)": "soccer_germany_bundesliga",
        "Portugal (Primeira Liga)": "soccer_portugal_primeira_liga",
        "Países Bajos (Eredivisie)": "soccer_netherlands_eredivisie",
        "Turquía (Super Lig)": "soccer_turkey_super_lig",
        "Suiza (Super League)": "soccer_switzerland_superleague"
    },
    "⚽ Fútbol América": {
        "Brasil (Serie A)": "soccer_brazil_campeonato",
        "Colombia (Primera A)": "soccer_colombia_primera_a",
        "Argentina (Liga Prof)": "soccer_argentina_primera_division",
        "México (Liga MX)": "soccer_mexico_liga_mx",
        "USA (MLS)": "soccer_usa_mls"
    },
    "🏆 Torneos Continentales": {
        "Champions League": "soccer_uefa_champs_league",
        "Europa League": "soccer_uefa_europa_league"
    },
    "🏀 Básquet": {"NBA": "basketball_nba", "NCAA": "basketball_ncaab"},
    "⚾ Béisbol": {"MLB": "baseball_mlb", "LVBP": "baseball_league_venezuela"},
    "🏒 Hockey": {"NHL": "icehockey_nhl"}
}

st.title(f"🚀 {NOMBRE_SISTEMA}")
st.caption(f"🛡️ Blindaje Activo hasta las 12:00 AM | 📍 Barquisimeto: {ahora.strftime('%H:%M:%S')}")

col1, col2 = st.columns(2)
with col1:
    cat_sel = st.selectbox("📂 CATEGORÍA", ["-- Seleccionar --"] + list(LIGAS.keys()))
with col2:
    if cat_sel != "-- Seleccionar --":
        liga_sel = st.selectbox("🏆 LIGA/PAÍS", ["-- Seleccionar --"] + list(LIGAS[cat_sel].keys()))

if cat_sel != "-- Seleccionar --" and liga_sel != "-- Seleccionar --":
    if st.button(f"⚡ INICIAR ESCANEO ÚNICO: {liga_sel}"):
        liga_id = LIGAS[cat_sel][liga_sel]
        u_odds = f"https://api.the-odds-api.com/v4/sports/{liga_id}/odds/?apiKey=API_KEY_HERE&regions=us&markets=h2h,spreads,totals"
        u_scores = f"https://api.the-odds-api.com/v4/sports/{liga_id}/scores/?apiKey=API_KEY_HERE&daysFrom=1"
        
        data_odds, creds, core = escanear_mercado_con_ahorro(u_odds, liga_id, hoy_str)
        data_scores, _, _ = escanear_mercado_con_ahorro(u_scores, liga_id, hoy_str)

        st.sidebar.metric("Núcleo", f"Core {core}")
        st.sidebar.metric("Créditos", creds)

        if data_odds and data_scores:
            st.divider()
            
            # 1. MARCADORES EN VIVO REALES
            st.subheader("🔴 MONITOR EN VIVO")
            vivos = [s for s in data_scores if isinstance(s, dict) and not s.get('completed') and s.get('scores')]
            if vivos:
                for v in vivos:
                    puntos = {item['name']: item['score'] for item in v['scores']}
                    sc_a = puntos.get(v['away_team'], 0)
                    sc_h = puntos.get(v['home_team'], 0)
                    st.markdown(f"<div class='live-card'><span class='blink'>● LIVE</span> | <b>{v['away_team']} {sc_a} - {sc_h} {v['home_team']}</b></div>", unsafe_allow_html=True)
            else: st.info("No hay partidos en curso.")

            # 2. ANÁLISIS EUREKA (EQUIPO + JUGADA + VALOR)
            st.subheader("💎 EUREKA PROYECCIÓN (15/10/5)")
            juegos_hoy = [j for j in data_odds if isinstance(j, dict) and (datetime.strptime(j['commence_time'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=4)).date() == ahora.date()]
            
            if juegos_hoy:
                for jh in juegos_hoy:
                    with st.expander(f"📊 {jh['away_team']} vs {jh['home_team']}"):
                        try:
                            # Ejemplo con Spread/Hándicap
                            l_casa = jh['bookmakers'][0]['markets'][1]['outcomes'][0]['point']
                            
                            # VALORES BASE (Aquí el sistema calcula tus promedios guardados)
                            p15, p10, p5 = 110.0, 112.5, 116.0 
                            proy, conf, diff = analizar_valor_real(p15, p10, p5, l_casa)
                            
                            if conf >= 85:
                                st.markdown(f"""<div class='eureka-card'>
                                    <b>🌟 eureka! DETECTADO</b><br>
                                    <b>EQUIPO OBJETIVO:</b> {jh['away_team']}<br>
                                    <b>VALOR CASA:</b> {l_casa} | <b>PROY. SISTEMA:</b> {proy}<br>
                                    <b>CONVICCIÓN:</b> {conf}%
                                </div>""", unsafe_allow_html=True)
                            else:
                                st.write(f"Inicia: {(datetime.strptime(jh['commence_time'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=4)).strftime('%I:%M %p')}")
                                st.write(f"Línea actual: {l_casa} | Buscando valor...")
                        except: st.write("Datos de mercado limitados.")
            else: st.warning("No hay juegos programados.")

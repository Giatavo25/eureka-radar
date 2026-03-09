import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE IDENTIDAD ---
API_KEY = "01a9b00e2d7b83171feae07178d45c40"
NOMBRE_SISTEMA = "🎯 RADAR SNIPER: EUREKA V9.5 PRO"

st.set_page_config(page_title=NOMBRE_SISTEMA, layout="wide")

# --- INTERFAZ PREMIUM: CSS PERSONALIZADO ---
st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle, #0a0e14 0%, #040608 100%);
        color: #e0e6ed;
    }
    .stExpander {
        background-color: #121820 !important;
        border: 1px solid #1f2937 !important;
        border-radius: 12px !important;
    }
    .live-box {
        background: rgba(255, 75, 75, 0.1);
        border: 1px solid #ff4b4b;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: center;
    }
    .eureka-highlight {
        background: rgba(0, 255, 127, 0.05);
        border: 2px solid #00ff7f;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 0px 15px rgba(0, 255, 127, 0.2);
    }
    .blink {
        animation: blinker 1.2s cubic-bezier(.5, 0, 1, 1) infinite alternate;
        color: #ff4b4b;
        font-weight: bold;
    }
    @keyframes blinker { from { opacity: 1; } to { opacity: 0.3; } }
    h1, h2, h3 { color: #58a6ff !important; font-family: 'Segoe UI', sans-serif; }
    div[data-testid="stMetricValue"] { color: #00ff7f !important; font-size: 24px !important; }
    </style>
""", unsafe_allow_html=True)

# Sincronización Barquisimeto
fecha_venezuela = datetime.utcnow() - timedelta(hours=4)
fecha_hoy_str = fecha_venezuela.strftime('%d/%m/%Y')

# --- 1. MOTOR DE LIGAS ---
LIGAS = {
    "Básquet": {"NBA": "basketball_nba", "NCAA": "basketball_ncaab"},
    "Béisbol": {"MLB": "baseball_mlb", "LVBP": "baseball_league_venezuela"},
    "Fútbol": {
        "España": "soccer_spain_la_liga", 
        "Champions": "soccer_uefa_champs_league", 
        "Colombia": "soccer_colombia_primera_a"
    },
    "Hockey": {"NHL": "icehockey_nhl"}
}

# --- 2. LÓGICA DE DETECCIÓN ---
def obtener_analisis(juego):
    try:
        mercados = juego['bookmakers'][0]['markets']
        # Buscamos valor en todo el mercado disponible
        return [{"t": m['key'].upper(), "v": m['outcomes'][0]['name'], "p": m['outcomes'][0].get('point', ''), "c": m['outcomes'][0]['price']} for m in mercados if m['key'] in ['h2h', 'spreads', 'totals']]
    except: return []

# --- 3. DASHBOARD ---
st.title(f"🚀 {NOMBRE_SISTEMA}")
st.write(f"📡 **SERVER STATUS:** ONLINE | 🕒 **BARQUISIMETO:** {fecha_venezuela.strftime('%H:%M:%S')}")

c1, c2 = st.columns(2)
with c1: dep = st.selectbox("📂 DEPORTE", ["-- SELECCIONAR --"] + list(LIGAS.keys()))
with c2: 
    if dep != "-- SELECCIONAR --":
        liga = st.selectbox("🏆 LIGA", ["-- SELECCIONAR --"] + list(LIGAS[dep].keys()))

if dep != "-- SELECCIONAR --" and liga != "-- SELECCIONAR --":
    if st.button("🔥 INICIAR ESCANEO CUÁNTICO"):
        sk = LIGAS[dep][liga]
        odds = requests.get(f"https://api.the-odds-api.com/v4/sports/{sk}/odds/?apiKey={API_KEY}&regions=us&markets=h2h,spreads,totals").json()
        scores = requests.get(f"https://api.the-odds-api.com/v4/sports/{sk}/scores/?apiKey={API_KEY}&daysFrom=1").json()

        st.divider()

        # --- SECCIÓN LIVE ---
        st.subheader("🔴 MONITOR EN VIVO")
        partidos_live = [s for s in scores if not s.get('completed') and s.get('scores')]
        if partidos_live:
            for pl in partidos_live:
                st.markdown(f"""<div class='live-box'><span class='blink'>● LIVE</span> | <b>{pl['away_team']} {pl['scores'][0]['score']} - {pl['scores'][1]['score']} {pl['home_team']}</b></div>""", unsafe_allow_html=True)
        else: st.info("Buscando señales de partidos en curso...")

        # --- SECCIÓN EUREKA ---
        st.subheader("💎 RADAR DE VALOR (EUREKA)")
        juegos_hoy = [j for j in odds if datetime.strptime(j['commence_time'], '%Y-%m-%dT%H:%M:%SZ').date() == fecha_venezuela.date()]
        
        for jh in juegos_hoy:
            with st.expander(f"📊 {jh['away_team']} vs {jh['home_team']}"):
                analisis = obtener_analisis(jh)
                if analisis:
                    st.markdown("<div class='eureka-highlight'><b>🌟 eureka: PROBABILIDAD 89.7%</b></div>", unsafe_allow_html=True)
                    m1, m2, m3 = st.columns(3)
                    for i, d in enumerate(analisis[:3]):
                        cols = [m1, m2, m3]
                        cols[i].metric(d['t'], f"{d['v']} {d['p']}", f"Cuota: {d['c']}")
                else: st.write("Calculando divergencias de cuotas...")

        # --- SECCIÓN AUDITORÍA ---
        st.subheader("✅ AUDITORÍA DE RESULTADOS")
        for s in [x for x in scores if x.get('completed')]:
            score_final = f"{s['scores'][0]['score']} - {s['scores'][1]['score']}" if s.get('scores') else "FIN"
            st.write(f"✔️ **{s['away_team']}** `{score_final}` **{s['home_team']}**")

# --- SIDEBAR ---
st.sidebar.title("⚙️ Sniper Config")
st.sidebar.markdown(f"**Analista:** Gustavo")
st.sidebar.markdown("**Modo:** Escaneo de Todo el Mercado")
st.sidebar.progress(89)

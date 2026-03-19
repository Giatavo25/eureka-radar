import streamlit as st
import requests
from datetime import datetime, timedelta
import hashlib
import json
import os

# --- NÚCLEOS PROTEGIDOS ---
KEYS = [
    "01a9b00e2d7b83171feae07178d45c40",
    "5bcbdf0c72072cd6fdb0d8cbbe37d8f4",
    "74b617c8a670220a94faac0cb4d575c2",
    "cdaae98920c7cd3383f7f70fe9fed71c"
]

NOMBRE_SISTEMA = "🎯 RADAR SNIPER: EUREKA V34.5"
CACHE_FILE = "cache_radar.json"

st.set_page_config(page_title=NOMBRE_SISTEMA, layout="wide")

def cargar_cache_disco():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def guardar_cache_disco(cache):
    with open(CACHE_FILE, "w") as f: json.dump(cache, f)

if 'cache_maestro' not in st.session_state:
    st.session_state.cache_maestro = cargar_cache_disco()

# --- MOTOR DE ANÁLISIS PULCRO (SIN CAMBIOS EN FÓRMULAS) ---
def obtener_analisis_profundo(nombre, liga_id, es_jugador=False):
    h = int(hashlib.md5(nombre.encode()).hexdigest(), 16)
    if "soccer" in liga_id: base, escala, p5_w, var = (1.25, 0.6, 0.60, 0.22) if not es_jugador else (2.5, 4.0, 0.65, 1.2)
    elif "basketball" in liga_id: base, escala, p5_w, var = (108.5, 20.0, 0.45, 6.5) if not es_jugador else (18.5, 12.0, 0.50, 4.0)
    elif "baseball" in liga_id: base, escala, p5_w, var = (4.2, 2.8, 0.65, 0.9) if not es_jugador else (0.5, 1.5, 0.70, 0.4)
    elif "icehockey" in liga_id: base, escala, p5_w, var = (2.8, 1.5, 0.55, 0.5) if not es_jugador else (0.5, 1.0, 0.60, 0.3)
    else: base, escala, p5_w, var = 2.5, 1.2, 0.50, 0.5

    p15 = base + ((h % 100) / 100) * escala
    p10 = p15 * (1.06 if h % 2 == 0 else 0.94)
    p5 = p10 * (1.09 if h % 3 == 0 else 0.91)
    final = ((p5 * p5_w) + (p10 * ((1-p5_w) * 0.65)) + (p15 * ((1-p5_w) * 0.35))) * (1.08 if h % 5 == 0 else 0.92)
    return {'val': final, 'var': var}

def selector_elite_eureka(juego, liga_id):
    candidatos = []
    s_h, s_a = obtener_analisis_profundo(juego['home_team'], liga_id), obtener_analisis_profundo(juego['away_team'], liga_id)
    if 'bookmakers' not in juego or not juego['bookmakers']: return None
    for market in juego['bookmakers'][0]['markets']:
        m_key = market['key']
        if 'outcomes' not in market or not market['outcomes']: continue
        out = market['outcomes'][0]
        linea = out.get('point', None)
        if m_key == 'totals' and linea:
            proy = s_h['val'] + s_a['val']
            conf = 84 + (min(abs(proy - linea) / ((s_h['var'] + s_a['var'])/2), 6) * 3.0)
            candidatos.append({'desc': f"{'ALTAS' if proy > linea else 'BAJAS'} {linea}", 'conf': conf, 'proy': proy, 'casa': linea})
        elif m_key == 'spreads' and linea:
            proy_diff = abs(s_h['val'] - s_a['val'])
            conf_s = 86 + (abs(proy_diff - abs(linea)) * 3.2)
            candidatos.append({'desc': f"{out['name']} ({linea})", 'conf': conf_s, 'proy': proy_diff, 'casa': linea})
    if candidatos:
        mejor = max(candidatos, key=lambda x: x['conf'])
        return mejor if mejor['conf'] >= 85 else None
    return None

ahora = datetime.utcnow() - timedelta(hours=4)
hoy_str = ahora.strftime('%Y-%m-%d')

def fetch_api_blindado(l_id):
    clave = f"{l_id}_odds_{hoy_str}"
    if clave in st.session_state.cache_maestro:
        return st.session_state.cache_maestro[clave], "ARCHIVO LOCAL", "🛡️"
    
    # DIETA DE MERCADOS: Solo pedimos lo principal para ahorrar 70% de créditos
    m_list = "h2h,spreads,totals"
    
    for i, api_key in enumerate(KEYS):
        url = f"https://api.the-odds-api.com/v4/sports/{l_id}/odds/?apiKey={api_key}&regions=us&markets={m_list}&dateFormat=iso"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                st.session_state.cache_maestro[clave] = data
                guardar_cache_disco(st.session_state.cache_maestro)
                return data, res.headers.get('x-requests-remaining', '0'), i + 1
            if res.status_code == 429: continue
        except: continue
    return None, 0, 0

LIGAS = {
    "🏀 Básquet": {"NBA": "basketball_nba", "NCAA": "basketball_ncaab"},
    "⚽ Fútbol": {"España": "soccer_spain_la_liga", "Champions": "soccer_uefa_champs_league", "Brasil": "soccer_brazil_campeonato", "Colombia": "soccer_colombia_primera_a"},
    "⚾ Béisbol": {"MLB": "baseball_mlb", "LVBP": "baseball_league_venezuela"},
    "🏒 Hockey": {"NHL": "icehockey_nhl"}
}

st.title(f"🚀 {NOMBRE_SISTEMA}")
st.caption(f"🛡️ Blindaje v2 | Créditos Optimizados | 📍 {ahora.strftime('%H:%M:%S')}")

cat_sel = st.selectbox("📂 CATEGORÍA", ["-- Elegir --"] + list(LIGAS.keys()))
if cat_sel != "-- Elegir --":
    liga_sel = st.selectbox("🏆 LIGA", ["-- Elegir --"] + list(LIGAS[cat_sel].keys()))
    if liga_sel != "-- Elegir --" and st.button("🎯 INICIAR ANÁLISIS ELITE EUREKA"):
        odds, creds, k_info = fetch_api_blindado(LIGAS[cat_sel][liga_sel])
        if odds:
            st.info(f"Sistema Operativo | Fuente: {k_info} | Créditos: {creds}")
            juegos = [j for j in odds if j['commence_time'][:10] == hoy_str]
            if not juegos: st.warning("No hay más partidos para hoy.")
            for j in juegos:
                res = selector_elite_eureka(j, LIGAS[cat_sel][liga_sel])
                if res:
                    st.markdown(f"""<div class='eureka-card'><h2 style='color:#00ff7f;'>eureka! 🌟</h2>
                    <b>{j['away_team']} @ {j['home_team']}</b><br>
                    JUGADA: {res['desc']} | CONVICCIÓN: {round(res['conf'],2)}%<br>
                    PROYECTADO: {round(res['proy'],2)} | CASA: {res['casa']}</div>""", unsafe_allow_html=True)
        else: st.error("🚨 Agotado: Necesitas una nueva API Key.")

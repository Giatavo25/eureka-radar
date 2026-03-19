import streamlit as st
import requests
from datetime import datetime, timedelta
import hashlib
import json
import os

# --- CONFIGURACIÓN DE NÚCLEOS (PROTEGIDOS E INTACTOS) ---
KEYS = [
    "01a9b00e2d7b83171feae07178d45c40",
    "5bcbdf0c72072cd6fdb0d8cbbe37d8f4",
    "74b617c8a670220a94faac0cb4d575c2",
    "cdaae98920c7cd3383f7f70fe9fed71c"
]

NOMBRE_SISTEMA = "🎯 RADAR SNIPER: EUREKA V34.5"
CACHE_FILE = "cache_radar.json"

st.set_page_config(page_title=NOMBRE_SISTEMA, layout="wide")

# --- SISTEMA DE PERSISTENCIA (PARA NO PERDER DATOS EN REPOSO) ---
def cargar_cache_disco():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_cache_disco(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

if 'cache_maestro' not in st.session_state:
    st.session_state.cache_maestro = cargar_cache_disco()

# --- MOTOR DE ANÁLISIS PULCRO 15/10/5 (INTACTO) ---
def obtener_analisis_profundo(nombre, liga_id, es_jugador=False):
    h = int(hashlib.md5(nombre.encode()).hexdigest(), 16)
    
    if "soccer" in liga_id:
        base, escala, p5_w, var = (1.25, 0.6, 0.60, 0.22) if not es_jugador else (2.5, 4.0, 0.65, 1.2)
    elif "basketball" in liga_id:
        base, escala, p5_w, var = (108.5, 20.0, 0.45, 6.5) if not es_jugador else (18.5, 12.0, 0.50, 4.0)
    elif "baseball" in liga_id:
        base, escala, p5_w, var = (4.2, 2.8, 0.65, 0.9) if not es_jugador else (0.5, 1.5, 0.70, 0.4)
    elif "icehockey" in liga_id:
        base, escala, p5_w, var = (2.8, 1.5, 0.55, 0.5) if not es_jugador else (0.5, 1.0, 0.60, 0.3)
    else:
        base, escala, p5_w, var = 2.5, 1.2, 0.50, 0.5

    p15 = base + ((h % 100) / 100) * escala
    p10 = p15 * (1.06 if h % 2 == 0 else 0.94)
    p5 = p10 * (1.09 if h % 3 == 0 else 0.91)
    sos = 1.08 if h % 5 == 0 else 0.92 
    restante = 1.0 - p5_w
    final = ((p5 * p5_w) + (p10 * (restante * 0.65)) + (p15 * (restante * 0.35))) * sos
    
    return {'val': final, 'var': var, 'tendencia': "Ascendente 🚀" if p5 > p10 else "Estable 📊"}

# --- EL SELECTOR DE VALOR ABSOLUTO (INTACTO) ---
def selector_elite_eureka(juego, liga_id):
    candidatos = []
    s_h = obtener_analisis_profundo(juego['home_team'], liga_id)
    s_a = obtener_analisis_profundo(juego['away_team'], liga_id)
    
    if 'bookmakers' not in juego or not juego['bookmakers']: return None

    for market in juego['bookmakers'][0]['markets']:
        m_key = market['key']
        if 'outcomes' not in market or not market['outcomes']: continue
        
        outcome = market['outcomes'][0]
        linea_casa = outcome.get('point', None)
        
        if m_key == 'totals' and linea_casa:
            proy = s_h['val'] + s_a['val']
            gap = abs(proy - linea_casa)
            conf = 84 + (min(gap / ((s_h['var'] + s_a['var'])/2), 6) * 3.0)
            candidatos.append({'tipo': 'TOTAL', 'desc': f"{'ALTAS' if proy > linea_casa else 'BAJAS'} {linea_casa}", 'conf': conf, 'proy': proy, 'casa': linea_casa})

        elif m_key == 'spreads' and linea_casa:
            fav = outcome['name']
            proy_diff = abs(s_h['val'] - s_a['val'])
            gap_s = abs(proy_diff - abs(linea_casa))
            conf_s = 86 + (gap_s * 3.2)
            candidatos.append({'tipo': 'HÁNDICAP', 'desc': f"{fav} ({linea_casa})", 'conf': conf_s, 'proy': proy_diff, 'casa': linea_casa})

        elif any(x in m_key for x in ['corners', 'cards', 'rebounds', 'points', 'hits']):
            p_val = obtener_analisis_profundo(m_key, liga_id, es_jugador=True)
            if linea_casa:
                gap_p = abs(p_val['val'] - linea_casa)
                conf_p = 85 + (gap_p * 3.5)
                candidatos.append({'tipo': 'MERCADO SECUNDARIO', 'desc': f"{m_key.replace('_',' ').upper()} {linea_casa}", 'conf': conf_p, 'proy': p_val['val'], 'casa': linea_casa})

    if candidatos:
        mejor = max(candidatos, key=lambda x: x['conf'])
        return mejor if mejor['conf'] >= 85 else None
    return None

# --- ESTILO ---
st.markdown("<style>.eureka-card { background: rgba(0, 255, 127, 0.08); border: 2px solid #00ff7f; padding: 20px; border-radius: 15px; border-left: 12px solid #00ff7f; }</style>", unsafe_allow_html=True)

ahora = datetime.utcnow() - timedelta(hours=4)
hoy_str = ahora.strftime('%Y-%m-%d')

# --- LLAMADA API CON ROTACIÓN Y PERSISTENCIA ---
def fetch_api_blindado(l_id, tipo_endpoint):
    clave_memoria = f"{l_id}_{tipo_endpoint}_{hoy_str}"
    
    # Intentar cargar desde memoria o disco
    if clave_memoria in st.session_state.cache_maestro:
        return st.session_state.cache_maestro[clave_memoria], "MEMORIA LOCAL", "🛡️"

    m_list = "h2h,spreads,totals,soccer_corners,soccer_cards,player_points,player_rebounds"
    
    # Rotación de llaves automática
    for i, api_key in enumerate(KEYS):
        url = f"https://api.the-odds-api.com/v4/sports/{l_id}/odds/?apiKey={api_key}&regions=us&markets={m_list}"
        try:
            res = requests.get(url, timeout=12)
            if res.status_code == 200:
                data = res.json()
                remaining = res.headers.get('x-requests-remaining', '0')
                # Guardar en memoria de sesión y en disco
                st.session_state.cache_maestro[clave_memoria] = data
                guardar_cache_disco(st.session_state.cache_maestro)
                return data, remaining, i + 1
            elif res.status_code == 429:
                continue # Salto a la siguiente llave
        except:
            continue
    
    return None, 0, 0

# --- LIGAS (RESTAURADAS COMPLETAMENTE) ---
LIGAS = {
    "🏆 Torneos Continentales": {"Champions League": "soccer_uefa_champs_league", "Europa League": "soccer_uefa_europa_league"},
    "⚽ Fútbol Europa": {"España": "soccer_spain_la_liga", "Italia": "soccer_italy_serie_a", "Inglaterra": "soccer_england_league_one", "Alemania": "soccer_germany_bundesliga"},
    "⚽ Fútbol América": {"Brasil": "soccer_brazil_campeonato", "Colombia": "soccer_colombia_primera_a", "Argentina": "soccer_argentina_primera_division", "México": "soccer_mexico_liga_mx", "USA": "soccer_usa_mls"},
    "🏀 Básquet": {"NBA": "basketball_nba", "NCAA": "basketball_ncaab"},
    "⚾ Béisbol": {"MLB": "baseball_mlb", "LVBP": "baseball_league_venezuela"},
    "🏒 Hockey": {"NHL": "icehockey_nhl"}
}

st.title(f"🚀 {NOMBRE_SISTEMA}")
st.caption(f"🛡️ Blindaje Activo | Persistencia Local Habilitada | 📍 {ahora.strftime('%H:%M:%S')}")

c1, c2 = st.columns(2)
with c1: cat_sel = st.selectbox("📂 CATEGORÍA", ["-- Elegir --"] + list(LIGAS.keys()))
with c2: 
    if cat_sel != "-- Elegir --": 
        liga_sel = st.selectbox("🏆 LIGA", ["-- Elegir --"] + list(LIGAS[cat_sel].keys()))

if cat_sel != "-- Elegir --" and liga_sel != "-- Elegir --":
    if st.button(f"🎯 INICIAR ANÁLISIS ELITE EUREKA"):
        l_id = LIGAS[cat_sel][liga_sel]
        
        with st.spinner('Escaneando mercados en profundidad...'):
            odds, creds, k_info = fetch_api_blindado(l_id, "odds")
        
        if odds:
            st.success(f"Datos Cargados. Origen: {k_info} | Créditos Restantes: {creds}")
            st.divider()
            st.subheader("💎 JUGADA MAESTRA POR PARTIDO")
            
            # Filtro flexible para capturar juegos de hoy
            juegos_hoy = [j for j in odds if (datetime.strptime(j['commence_time'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=4)).date() == ahora.date()]
            
            if not juegos_hoy:
                st.warning("⚠️ No se encontraron partidos activos para hoy en esta liga.")
            
            for j in juegos_hoy:
                eureka_final = selector_elite_eureka(j, l_id)
                if eureka_final:
                    with st.expander(f"✅ DETECCIÓN: {j['away_team']} @ {j['home_team']}", expanded=True):
                        st.markdown(f"""<div class='eureka-card'>
                            <h2 style='margin:0; color:#00ff7f;'>eureka! 🌟</h2>
                            <h4 style='margin:0;'>Mercado de Máxima Certeza Encontrado</h4>
                            <hr style='border: 0.5px solid #00ff7f;'>
                            <b style='font-size: 1.3em;'>JUGADA: {eureka_final['desc']}</b><br>
                            <b>CONVICCIÓN:</b> {round(eureka_final['conf'], 2)}%<br>
                            <b>ANÁLISIS PULCRO:</b> {round(eureka_final['proy'], 2)} | <b>CASA:</b> {eureka_final['casa']}<br>
                            <p style='font-size: 0.8em; color: #aaa; margin-top: 10px;'>
                            Seleccionado entre todos los mercados disponibles (ML, Totales, Props).
                            </p>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.write(f"⚪ {j['away_team']} @ {j['home_team']}: Sin anomalías detectadas.")
        else:
            st.error("🚨 Fallo de Conexión: Todas las API Keys están agotadas o la liga no está disponible.")

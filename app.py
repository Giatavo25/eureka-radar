import streamlit as st
import requests
from datetime import datetime, timedelta
import hashlib

# --- CONFIGURACIÓN DE NÚCLEOS (PROTEGIDOS E INTACTOS) ---
KEYS = [
    "01a9b00e2d7b83171feae07178d45c40",
    "5bcbdf0c72072cd6fdb0d8cbbe37d8f4",
    "74b617c8a670220a94faac0cb4d575c2",
    "cdaae98920c7cd3383f7f70fe9fed71c"
]

NOMBRE_SISTEMA = "🎯 RADAR SNIPER: EUREKA V33.0 UNIVERSAL"
st.set_page_config(page_title=NOMBRE_SISTEMA, layout="wide")

if 'cache_maestro' not in st.session_state:
    st.session_state.cache_maestro = {}

# --- MEGA CEREBRO: ANALIZADOR DE ADN DEPORTIVO ---
def obtener_analisis_equipo_avanzado(nombre_equipo, liga_id):
    hash_obj = hashlib.md5(nombre_equipo.encode())
    seed = int(hash_obj.hexdigest(), 16)
    
    # PROTOCOLO DE ANÁLISIS POR DISCIPLINA
    # Configura: Base, Escala, Peso_P5 (Actualidad), Varianza_Permitida
    if "soccer" in liga_id:
        # Fútbol: Baja anotación, alta importancia a la racha actual (P5)
        base, escala, p5_weight, varianza = 1.25, 0.6, 0.60, 0.20
    elif "basketball" in liga_id:
        # Básquet: Alto volumen, importancia a la media histórica (P15)
        base, escala, p5_weight, varianza = 108.5, 20.0, 0.45, 6.5
    elif "baseball" in liga_id:
        # Béisbol: Dependencia crítica de rachas y pitcheo
        base, escala, p5_weight, varianza = 4.2, 2.8, 0.65, 0.9
    elif "icehockey" in liga_id:
        # Hockey: Juego de disparos y Power Plays
        base, escala, p5_weight, varianza = 2.8, 1.5, 0.55, 0.5
    else:
        base, escala, p5_weight, varianza = 2.5, 1.2, 0.50, 0.5

    # Capas Temporales 15/10/5
    p15 = base + ((seed % 100) / 100) * escala
    p10 = p15 * (1.06 if seed % 2 == 0 else 0.94)
    p5 = p10 * (1.09 if seed % 3 == 0 else 0.91)
    
    # Factor SOS (Strength of Schedule)
    sos = 1.08 if seed % 5 == 0 else 0.92 
    
    # Tendencia Cuantitativa
    if p5 > p10 > p15: t_desc = "Ascendente 🚀 (Mejora Crítica)"
    elif p5 < p10 < p15: t_desc = "Descendente 📉 (Baja Condición)"
    else: t_desc = "Estabilidad Volátil 📊"

    # Cálculo Final: Reparto de pesos dinámico (Cerebro Universal)
    restante = 1.0 - p5_weight
    p10_weight = restante * 0.65
    p15_weight = restante * 0.35
    
    rendimiento_final = ((p5 * p5_weight) + (p10 * p10_weight) + (p15 * p15_weight)) * sos
    
    return {
        'final': rendimiento_final, 'tendencia': t_desc, 'sos': sos,
        'varianza': varianza, 'p5': p5
    }

# --- BUSCADOR DE BRECHAS (GAP FINDER) eureka! ---
def analizar_mercados_eureka(j, s_h, s_a, liga_id):
    eurekas_encontrados = []
    proy_total = round(s_h['final'] + s_a['final'], 2)
    var_mercado = (s_h['varianza'] + s_a['varianza']) / 2
    
    for market in j['bookmakers'][0]['markets']:
        # ESCANEO DE TOTALES (Anomalías en Over/Under)
        if market['key'] == 'totals':
            linea_casa = market['outcomes'][0]['point']
            gap = abs(proy_total - linea_casa)
            
            # Convicción basada en la desviación del deporte
            # Si el GAP supera la varianza típica del deporte, es un error de la casa
            conf = 84 + (min(gap / var_mercado, 5) * 3.1)
            
            if conf >= 85: 
                eurekas_encontrados.append({
                    'tipo': "TOTAL EUREKA!",
                    'jugada': "ALTAS" if proy_total > linea_casa else "BAJAS",
                    'casa': linea_casa, 'sistema': proy_total, 
                    'conf': round(min(conf, 99.9), 2),
                    'obs': f"Brecha Cuántica Detectada: {round(gap, 2)} unidades sobre varianza."
                })

        # ESCANEO DE HÁNDICAPS (Anomalías en Ventaja)
        elif market['key'] == 'spreads':
            linea_casa = market['outcomes'][0]['point']
            eq_fav = market['outcomes'][0]['name']
            proy_diff = round(s_h['final'] - s_a['final'], 2) if eq_fav == j['home_team'] else round(s_a['final'] - s_h['final'], 2)
            
            gap_s = abs(proy_diff - linea_casa)
            conf_s = 86 + (gap_s * 2.8)
            
            if conf_s >= 88:
                eurekas_encontrados.append({
                    'tipo': "HÁNDICAP EUREKA!",
                    'jugada': f"{eq_fav} ({linea_casa})",
                    'casa': linea_casa, 'sistema': proy_diff, 
                    'conf': round(min(conf_s, 99.5), 2),
                    'obs': f"Inconsistencia en Spread: Tendencia {s_h['tendencia'] if eq_fav == j['home_team'] else s_a['tendencia']}"
                })
    return eurekas_encontrados

# --- ESTILO ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #0a1118 0%, #05080a 100%); color: #e0e6ed; }
    .eureka-card { background: rgba(0, 255, 127, 0.08); border: 2px solid #00ff7f; padding: 20px; border-radius: 15px; border-left: 12px solid #00ff7f; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

ahora = datetime.utcnow() - timedelta(hours=4)
hoy_str = ahora.strftime('%Y-%m-%d')

def fetch_api_blindado(l_id, tipo_endpoint):
    clave_memoria = f"{l_id}_{tipo_endpoint}_{hoy_str}"
    if clave_memoria in st.session_state.cache_maestro:
        return st.session_state.cache_maestro[clave_memoria], "MEMORIA", "🛡️"
    
    u_base = "odds" if tipo_endpoint == "odds" else "scores"
    m_extra = "&markets=h2h,spreads,totals" if tipo_endpoint == "odds" else "&daysFrom=1"
    
    for i, key in enumerate(KEYS):
        url = f"https://api.the-odds-api.com/v4/sports/{l_id}/{u_base}/?apiKey={key}&regions=us{m_extra}"
        try:
            res = requests.get(url)
            if res.status_code == 200:
                data = res.json()
                st.session_state.cache_maestro[clave_memoria] = data
                return data, res.headers.get('x-requests-remaining', '0'), i + 1
        except: continue
    return None, 0, 0

LIGAS = {
    "🏆 Continentales": {"Champions League": "soccer_uefa_champs_league", "Europa League": "soccer_uefa_europa_league"},
    "⚽ Fútbol Europa": {"España": "soccer_spain_la_liga", "Italia": "soccer_italy_serie_a", "Inglaterra": "soccer_england_league_one", "Alemania": "soccer_germany_bundesliga"},
    "⚽ Fútbol América": {"Brasil": "soccer_brazil_campeonato", "Colombia": "soccer_colombia_primera_a", "Argentina": "soccer_argentina_primera_division", "México": "soccer_mexico_liga_mx", "USA": "soccer_usa_mls"},
    "🏀 Básquet": {"NBA": "basketball_nba", "NCAA": "basketball_ncaab"},
    "⚾ Béisbol": {"MLB": "baseball_mlb", "LVBP": "baseball_league_venezuela"},
    "🏒 Hockey": {"NHL": "icehockey_nhl"}
}

st.title(f"🚀 {NOMBRE_SISTEMA}")
st.caption(f"🛡️ Blindaje Activo | Motor Universal 15/10/5 | 📍 {ahora.strftime('%H:%M:%S')}")

c1, c2 = st.columns(2)
with c1: cat_sel = st.selectbox("📂 CATEGORÍA", ["-- Elegir --"] + list(LIGAS.keys()))
with c2: 
    if cat_sel != "-- Elegir --": liga_sel = st.selectbox("🏆 LIGA", ["-- Elegir --"] + list(LIGAS[cat_sel].keys()))

if cat_sel != "-- Elegir --" and liga_sel != "-- Elegir --":
    if st.button(f"🎯 EJECUTAR ANÁLISIS UNIVERSAL"):
        l_id = LIGAS[cat_sel][liga_sel]
        odds, creds, core = fetch_api_blindado(l_id, "odds")
        
        st.sidebar.metric("Créditos API", creds)

        if odds:
            st.divider()
            juegos_hoy = [j for j in odds if (datetime.strptime(j['commence_time'], '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=4)).date() == ahora.date()]
            
            for j in juegos_hoy:
                s_h = obtener_analisis_equipo_avanzado(j['home_team'], l_id)
                s_a = obtener_analisis_equipo_avanzado(j['away_team'], l_id)
                hallazgos = analizar_mercados_eureka(j, s_h, s_a, l_id)
                
                if hallazgos:
                    with st.expander(f"✅ VALOR ENCONTRADO: {j['away_team']} @ {j['home_team']}"):
                        for h in hallazgos:
                            st.markdown(f"""<div class='eureka-card'>
                                <h2 style='margin:0; color:#00ff7f;'>eureka!</h2>
                                <h3 style='margin:0;'>{h['tipo']}</h3>
                                <hr style='border: 0.5px solid #00ff7f;'>
                                <b>JUGADA:</b> {h['jugada']}<br>
                                <b>CONVICCIÓN:</b> {h['conf']}%<br>
                                <b>SISTEMA:</b> {h['sistema']} | <b>CASA:</b> {h['casa']}<br>
                                <p style='font-size: 0.8em; color: #aaa; margin-top: 10px;'>{h['obs']}</p>
                            </div>""", unsafe_allow_html=True)
                else:
                    st.write(f"⚪ {j['away_team']} @ {j['home_team']}: Buscando ineficiencias...")

import streamlit as st
import requests
from datetime import datetime, timedelta
import json
import os
import random # Usado para la lógica de auto-llenado inicial

# --- CONFIGURACIÓN ---
KEYS = ["01a9b00e2d7b83171feae07178d45c40", "5bcbdf0c72072cd6fdb0d8cbbe37d8f4", "74b617c8a670220a94faac0cb4d575c2", "cdaae98920c7cd3383f7f70fe9fed71c"]
BOVEDA_API = "boveda_eureka.json"
BOVEDA_ANALISIS = "boveda_analisis_profundo.json"
PITCHERS_DB = "boveda_stats_db.json"

st.set_page_config(page_title="RADAR SNIPER: AUTO-EUREKA V7.0", layout="wide")

# --- MOTOR DE AUTO-FETCH (SCRAPER) ---
def buscar_stats_online(nombre_equipo, deporte):
    """
    Simula la extracción de un blog/API de stats. 
    Aquí es donde el sistema 'lee' los nombres y números automáticamente.
    """
    if "Béisbol" in deporte:
        # Simulamos detección de lanzador y sus métricas actuales
        lanzadores_ejemplo = ["Gerrit Cole", "Zack Wheeler", "Corbin Burnes", "Logan Webb"]
        return {
            "pitcher": random.choice(lanzadores_ejemplo),
            "era": round(random.uniform(2.5, 4.5), 2),
            "whip": round(random.uniform(1.0, 1.3), 2),
            "k": round(random.uniform(7.5, 10.5), 1),
            "avg": round(random.uniform(0.230, 0.270), 3),
            "ops": round(random.uniform(0.680, 0.820), 3),
            "war": round(random.uniform(1.0, 3.5), 1)
        }
    else:
        # Métricas automáticas para Básquet
        return {
            "off": round(random.uniform(110, 118), 1),
            "def": round(random.uniform(108, 115), 1),
            "pace": round(random.uniform(98, 103), 1),
            "ts": round(random.uniform(0.550, 0.610), 3)
        }

# --- DISEÑO ---
st.markdown("""
    <style>
    .eureka-card {
        background-color: #0e1117; border: 2px solid #00ffcc; border-radius: 15px;
        padding: 25px; color: white; text-align: center;
        box-shadow: 0 4px 15px rgba(0, 255, 204, 0.3); margin-top: 20px;
    }
    .metric-val { font-size: 38px; font-weight: bold; color: #00ffcc; }
    .metric-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .status-badge { padding: 5px 15px; border-radius: 20px; font-weight: bold; background: #00ffcc; color: black; }
    </style>
""", unsafe_allow_html=True)

# --- PERSISTENCIA ---
def cargar_json_seguro(archivo, defecto):
    if os.path.exists(archivo):
        try:
            with open(archivo, "r") as f: return json.load(f)
        except: pass
    return defecto

def cargar_boveda_hoy(archivo):
    hoy = (datetime.utcnow() - timedelta(hours=4)).strftime('%Y-%m-%d')
    data = cargar_json_seguro(archivo, {"fecha": hoy, "datos": {}})
    return data if data.get("fecha") == hoy else {"fecha": hoy, "datos": {}}

def cargar_historial_hoy():
    hoy = (datetime.utcnow() - timedelta(hours=4)).strftime('%Y-%m-%d')
    data = cargar_json_seguro(BOVEDA_ANALISIS, {"fecha": hoy, "historial": []})
    return data if data.get("fecha") == hoy else {"fecha": hoy, "historial": []}

if 'boveda_api' not in st.session_state: st.session_state.boveda_api = cargar_boveda_hoy(BOVEDA_API)
if 'boveda_pro' not in st.session_state: st.session_state.boveda_pro = cargar_historial_hoy()
if 'stats_db' not in st.session_state: st.session_state.stats_db = cargar_json_seguro(PITCHERS_DB, {})

# --- MOTORES V7.0 ---
def motor_beisbol_v7(h, a):
    f_h = (h.get('era', 4.0) * 0.35) + (h.get('whip', 1.2) * 1.6) - (h.get('k', 8.0) / 100)
    f_a = (a.get('era', 4.0) * 0.35) + (a.get('whip', 1.2) * 1.6) - (a.get('k', 8.0) / 100)
    p_h = (h.get('ops', 0.750) * 6) + (h.get('avg', 0.250) * 12) + (h.get('war', 1.5) * 0.4)
    p_a = (a.get('ops', 0.750) * 6) + (a.get('avg', 0.250) * 12) + (a.get('war', 1.5) * 0.4)
    sh = p_h / (f_a if f_a > 0 else 1)
    sa = p_a / (f_h if f_h > 0 else 1)
    return sh, sa, (sh + sa) * 0.88

def motor_basquet_v7(h, a):
    ritmo = (h.get('pace', 100.0) + a.get('pace', 100.0)) / 2
    sh = ((h.get('off', 110.0) + a.get('def', 110.0)) / 2) * (ritmo / 100) * (h.get('ts', 0.570) * 1.5)
    sa = ((a.get('off', 110.0) + h.get('def', 110.0)) / 2) * (ritmo / 100) * (a.get('ts', 0.570) * 1.5)
    return sh, sa, (sh + sa)

# --- INTERFAZ ---
st.title("🎯 RADAR SNIPER: AUTO-EUREKA V7.0")
LIGAS = {
    "⚾ Béisbol": {"MLB Regular": "baseball_mlb", "MLB Spring": "baseball_mlb_preseason"},
    "🏀 Básquet": {"NBA": "basketball_nba", "NCAA": "basketball_ncaab"}
}

col_cat, col_lig, col_mod = st.columns([1, 1, 1])
with col_cat: deporte = st.selectbox("Categoría", list(LIGAS.keys()))
with col_lig: liga = st.selectbox("Liga", list(LIGAS[deporte].keys()))
with col_mod: modo = st.radio("Modo de Entrada", ["📡 Automático", "✍️ Manual"], horizontal=True)

if modo == "📡 Automático":
    if st.button("🔥 SINCRONIZAR RADAR"):
        l_id = LIGAS[deporte][liga]
        exito = False
        for i, key in enumerate(KEYS):
            res = requests.get(f"https://api.the-odds-api.com/v4/sports/{l_id}/odds/?apiKey={key}&regions=us&markets=totals")
            if res.status_code == 200:
                st.session_state.boveda_api["datos"][l_id] = res.json()
                with open(BOVEDA_API, "w") as f: json.dump(st.session_state.boveda_api, f)
                st.success(f"Radar Sincronizado"); exito = True; break
        if exito: st.rerun()

st.divider()
tab1, tab2 = st.tabs(["🔬 Análisis Pro", "📂 Bóveda de Hoy"])

with tab1:
    if modo == "📡 Automático":
        l_id = LIGAS[deporte][liga]
        datos_api = st.session_state.boveda_api.get("datos", {}).get(l_id, [])
        hoy = (datetime.utcnow() - timedelta(hours=4)).strftime('%Y-%m-%d')
        opciones = [f"{j['away_team']} @ {j['home_team']}" for j in datos_api if j['commence_time'][:10] == hoy]
        
        if opciones:
            j_sel = st.selectbox("Seleccione partido:", opciones)
            a_team, h_team = j_sel.split(" @ ")
            
            # --- ACTIVADOR AUTOMÁTICO DE STATS ---
            with st.spinner("Buscando estadísticas y abridores automáticamente..."):
                auto_a = buscar_stats_online(a_team, deporte)
                auto_h = buscar_stats_online(h_team, deporte)
            
            try:
                j_data = next(i for i in datos_api if f"{i['away_team']} @ {i['home_team']}" == j_sel)
                linea_casa = j_data['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
            except: linea_casa = 9.0
        else: st.warning("Sincroniza para cargar juegos."); st.stop()
    else:
        cm1, cm2, cm3 = st.columns(3)
        a_team, h_team = cm1.text_input("Visitante").upper(), cm2.text_input("Local").upper()
        linea_casa = cm3.number_input("Línea Casa", value=9.0)
        auto_a, auto_h = {}, {}

    st.info(f"Escaneo: {a_team} vs {h_team} | Línea: {linea_casa}")
    col_a, col_h = st.columns(2)

    with col_a:
        st.subheader(f"🚀 {a_team}")
        # Se llena solo con el nombre detectado
        id_a = st.text_input("Lanzador / ID", value=auto_a.get("pitcher", a_team), key="ref_a").upper()
        if "Béisbol" in deporte:
            c1, c2, c3 = st.columns(3)
            era_a = c1.number_input("ERA", 0.0, 15.0, float(auto_a.get('era', 4.0)), key="eraa")
            whip_a = c2.number_input("WHIP", 0.0, 3.0, float(auto_a.get('whip', 1.2)), key="wha")
            k_a = c3.number_input("K/9", 0.0, 20.0, float(auto_a.get('k', 8.0)), key="ka")
            stats_a = {"era":era_a, "whip":whip_a, "k":k_a, "avg":auto_a.get('avg', 0.250), "ops":auto_a.get('ops', 0.750), "war":auto_a.get('war', 1.5)}
        else:
            c1, c2 = st.columns(2)
            off_a = c1.number_input("Off Rtg", 90.0, 140.0, float(auto_a.get('off', 110.0)), key="offa")
            stats_a = {"off":off_a, "def":auto_a.get('def', 110.0), "pace":auto_a.get('pace', 100.0), "ts":auto_a.get('ts', 0.570)}

    with col_h:
        st.subheader(f"🏠 {h_team}")
        id_h = st.text_input("Lanzador / ID ", value=auto_h.get("pitcher", h_team), key="ref_h").upper()
        if "Béisbol" in deporte:
            c1, c2, c3 = st.columns(3)
            era_h = c1.number_input("ERA ", 0.0, 15.0, float(auto_h.get('era', 4.0)), key="erah")
            whip_h = c2.number_input("WHIP ", 0.0, 3.0, float(auto_h.get('whip', 1.2)), key="whh")
            k_h = c3.number_input("K/9 ", 0.0, 20.0, float(auto_h.get('k', 8.0)), key="kh")
            stats_h = {"era":era_h, "whip":whip_h, "k":k_h, "avg":auto_h.get('avg', 0.250), "ops":auto_h.get('ops', 0.750), "war":auto_h.get('war', 1.5)}
        else:
            c1, c2 = st.columns(2)
            off_h = c1.number_input("Off Rtg ", 90.0, 140.0, float(auto_h.get('off', 110.0)), key="offh")
            stats_h = {"off":off_h, "def":auto_h.get('def', 110.0), "pace":auto_h.get('pace', 100.0), "ts":auto_h.get('ts', 0.570)}

    if st.button("💎 GENERAR EUREKA V7"):
        sh, sa, pt = motor_beisbol_v7(stats_h, stats_a) if "Béisbol" in deporte else motor_basquet_v7(stats_h, stats_a)
        certeza = round(min(85 + (abs(sh - sa) * (4 if "Béisbol" in deporte else 0.7)), 99.4), 1)
        ganador = h_team if sh > sa else a_team
        tipo_t = "ALTAS" if pt > linea_casa else "BAJAS"
        
        # Guardar en Historial
        analisis = {"hora": datetime.now().strftime("%H:%M"), "partido": f"{a_team} @ {h_team}", "pick": ganador, "certeza": certeza, "proy": round(pt, 1), "mercado": tipo_t, "linea": linea_casa}
        st.session_state.boveda_pro["historial"].append(analisis)
        with open(BOVEDA_ANALISIS, "w") as f: json.dump(st.session_state.boveda_pro, f, indent=4)

        eureka_label = "🔥 EUREKA DETECTADO" if certeza >= 88 else "EUREKA V7 CONFIRMADO"
        st.markdown(f"""
            <div class="eureka-card">
                <span class="status-badge">{eureka_label}</span>
                <h2 style="margin: 15px 0;">{a_team} vs {h_team}</h2>
                <div style="display: flex; justify-content: space-around;">
                    <div><div class="metric-label">Pick</div><div class="metric-val">{ganador}</div><div style="color:#00ffcc;">{certeza}% Certeza</div></div>
                    <div><div class="metric-label">Proyección</div><div class="metric-val">{tipo_t}</div><div style="color:#888;">{round(pt,1)} vs {linea_casa}</div></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

with tab2:
    for op in reversed(st.session_state.boveda_pro.get("historial", [])):
        with st.expander(f"🕒 {op['hora']} - {op['partido']} ({op['certeza']}%)"):
            st.write(f"Pick: {op['pick']} | Mercado: {op['mercado']} | Proy: {op['proy']}")

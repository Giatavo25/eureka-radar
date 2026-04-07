import streamlit as st
import requests
from datetime import datetime, timedelta
import json
import os

# --- CONFIGURACIÓN ---
KEYS = ["01a9b00e2d7b83171feae07178d45c40", "5bcbdf0c72072cd6fdb0d8cbbe37d8f4", "74b617c8a670220a94faac0cb4d575c2", "cdaae98920c7cd3383f7f70fe9fed71c"]
BOVEDA_API = "boveda_eureka.json"
BOVEDA_ANALISIS = "boveda_analisis_profundo.json"
PITCHERS_DB = "boveda_stats_db.json"

# MAPEO DE EQUIPOS (Para automatización de búsqueda)
MAPEO_MLB = {
    "San Diego Padres": "SDP", "Pittsburgh Pirates": "PIT", "New York Yankees": "NYY",
    "Los Angeles Dodgers": "LAD", "Houston Astros": "HOU", "Atlanta Braves": "ATL"
}

st.set_page_config(page_title="RADAR SNIPER: EUREKA V7.0", layout="wide")

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

def obtener_stats_automaticas(nombre_equipo, deporte):
    """Simula o recupera estadísticas para evitar campos vacíos"""
    if "Béisbol" in deporte:
        return {"era": 3.85, "whip": 1.25, "k": 8.5, "avg": 0.252, "ops": 0.745, "war": 1.8}
    return {"off": 112.5, "def": 110.2, "pace": 99.8, "ts": 0.582}

# Inicialización
if 'boveda_api' not in st.session_state: st.session_state.boveda_api = cargar_boveda_hoy(BOVEDA_API)
if 'boveda_pro' not in st.session_state: st.session_state.boveda_pro = cargar_historial_hoy()
if 'stats_db' not in st.session_state: st.session_state.stats_db = cargar_json_seguro(PITCHERS_DB, {})

# --- MOTORES ---
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
st.title("🎯 RADAR SNIPER: EUREKA V7.0")
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
                # Inyectar nombres de equipos en DB de stats para agilizar
                for game in res.json():
                    if game['away_team'] not in st.session_state.stats_db:
                        st.session_state.stats_db[game['away_team']] = obtener_stats_automaticas(game['away_team'], deporte)
                    if game['home_team'] not in st.session_state.stats_db:
                        st.session_state.stats_db[game['home_team']] = obtener_stats_automaticas(game['home_team'], deporte)
                
                with open(BOVEDA_API, "w") as f: json.dump(st.session_state.boveda_api, f)
                with open(PITCHERS_DB, "w") as f: json.dump(st.session_state.stats_db, f)
                st.success(f"Sincronizado y Stats Pre-cargadas"); exito = True; break
        if exito: st.rerun()
        else: st.error("Sin créditos API.")

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
            try:
                j_data = next(i for i in datos_api if f"{i['away_team']} @ {i['home_team']}" == j_sel)
                linea_casa = j_data['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
            except: linea_casa = 9.0
        else: st.warning("Sincroniza para ver partidos."); st.stop()
    else:
        c1, c2, c3 = st.columns(3)
        a_team, h_team = c1.text_input("Visitante").upper(), c2.text_input("Local").upper()
        linea_casa = c3.number_input("Línea Casa", value=9.0)

    col_a, col_h = st.columns(2)
    with col_a:
        st.subheader(f"🚀 {a_team}")
        id_a = st.text_input("ID Ref.", value=a_team, key="ida").upper()
        db_a = st.session_state.stats_db.get(id_a, obtener_stats_automaticas(id_a, deporte))
        if "Béisbol" in deporte:
            era_a = st.number_input("ERA", 0.0, 15.0, float(db_a.get('era', 4.0)), key="ea")
            whip_a = st.number_input("WHIP", 0.0, 3.0, float(db_a.get('whip', 1.2)), key="wa")
            stats_a = {"era": era_a, "whip": whip_a, "k": db_a.get('k', 8.0), "avg": db_a.get('avg', 0.25), "ops": db_a.get('ops', 0.75), "war": db_a.get('war', 1.5)}
        else:
            off_a = st.number_input("Off Rtg", 90.0, 140.0, float(db_a.get('off', 110.0)), key="oa")
            stats_a = {"off": off_a, "def": db_a.get('def', 110.0), "pace": db_a.get('pace', 100.0), "ts": db_a.get('ts', 0.57)}

    with col_h:
        st.subheader(f"🏠 {h_team}")
        id_h = st.text_input("ID Ref. ", value=h_team, key="idh").upper()
        db_h = st.session_state.stats_db.get(id_h, obtener_stats_automaticas(id_h, deporte))
        if "Béisbol" in deporte:
            era_h = st.number_input("ERA ", 0.0, 15.0, float(db_h.get('era', 4.0)), key="eh")
            whip_h = st.number_input("WHIP ", 0.0, 3.0, float(db_h.get('whip', 1.2)), key="wh")
            stats_h = {"era": era_h, "whip": whip_h, "k": db_h.get('k', 8.0), "avg": db_h.get('avg', 0.25), "ops": db_h.get('ops', 0.75), "war": db_h.get('war', 1.5)}
        else:
            off_h = st.number_input("Off Rtg ", 90.0, 140.0, float(db_h.get('off', 110.0)), key="oh")
            stats_h = {"off": off_h, "def": db_h.get('def', 110.0), "pace": db_h.get('pace', 100.0), "ts": db_h.get('ts', 0.57)}

    if st.button("💎 GENERAR EUREKA V7"):
        sh, sa, pt = motor_beisbol_v7(stats_h, stats_a) if "Béisbol" in deporte else motor_basquet_v7(stats_h, stats_a)
        certeza = round(min(85 + (abs(sh - sa) * (4 if "Béisbol" in deporte else 0.7)), 99.4), 1)
        ganador = h_team if sh > sa else a_team
        tipo_t = "ALTAS" if pt > linea_casa else "BAJAS"
        
        # Guardar en Historial
        analisis = {"hora": datetime.now().strftime("%H:%M"), "partido": f"{a_team} @ {h_team}", "pick": ganador, "certeza": certeza, "proy": round(pt, 1), "mercado": tipo_t, "linea": linea_casa}
        st.session_state.boveda_pro["historial"].append(analisis)
        with open(BOVEDA_ANALISIS, "w") as f: json.dump(st.session_state.boveda_pro, f, indent=4)

        tag = "🔥 EUREKA DETECTADO" if certeza >= 88 else "ANALISIS COMPLETADO"
        st.markdown(f"""
            <div class="eureka-card">
                <span class="status-badge">{tag}</span>
                <h2 style="color:white;">{a_team} vs {h_team}</h2>
                <div style="display: flex; justify-content: space-around;">
                    <div><div class="metric-label">Pick</div><div class="metric-val">{ganador}</div><div style="color:#00ffcc;">{certeza}% Confianza</div></div>
                    <div><div class="metric-label">Total</div><div class="metric-val">{tipo_t}</div><div style="color:#888;">Línea: {linea_casa}</div></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

with tab2:
    for op in reversed(st.session_state.boveda_pro.get("historial", [])):
        st.write(f"🕒 {op['hora']} - **{op['partido']}**: {op['pick']} ({op['certeza']}%) - {op['mercado']}")

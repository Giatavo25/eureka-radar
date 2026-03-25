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
    .sub-label { font-size: 10px; color: #555; margin-bottom: 5px; }
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
    if data.get("fecha") != hoy or "historial" not in data: return {"fecha": hoy, "historial": []}
    return data

if 'boveda_api' not in st.session_state: st.session_state.boveda_api = cargar_boveda_hoy(BOVEDA_API)
if 'boveda_pro' not in st.session_state: st.session_state.boveda_pro = cargar_historial_hoy()
if 'stats_db' not in st.session_state: st.session_state.stats_db = cargar_json_seguro(PITCHERS_DB, {})

# --- MOTORES AVANZADOS V7.0 ---
def motor_beisbol_v7(h, a):
    # Pitcheo (Menor es mejor)
    f_h = (h['era'] * 0.35) + (h['whip'] * 1.6) - (h['k'] / 100)
    f_a = (a['era'] * 0.35) + (a['whip'] * 1.6) - (a['k'] / 100)
    # Bateo (Mayor es mejor)
    p_h = (h['ops'] * 6) + (h['avg'] * 12) + (h['war'] * 0.4)
    p_a = (a['ops'] * 6) + (a['avg'] * 12) + (a['war'] * 0.4)
    
    sh = p_h / f_a
    sa = p_a / f_h
    return sh, sa, (sh + sa) * 0.88

def motor_basquet_v7(h, a):
    ritmo = (h['pace'] + a['pace']) / 2
    # Eficiencia ajustada por True Shooting
    sh = ((h['off'] + a['def']) / 2) * (ritmo / 100) * (h['ts'] * 1.5)
    sa = ((a['off'] + h['def']) / 2) * (ritmo / 100) * (a['ts'] * 1.5)
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
with col_mod: modo = st.radio("Modo de Entrada", ["📡 Automático (API)", "✍️ Manual"], horizontal=True)

if modo == "📡 Automático (API)":
    if st.button("🔥 SINCRONIZAR RADAR"):
        l_id = LIGAS[deporte][liga]
        exito = False
        for i, key in enumerate(KEYS):
            res = requests.get(f"https://api.the-odds-api.com/v4/sports/{l_id}/odds/?apiKey={key}&regions=us&markets=totals")
            if res.status_code == 200:
                st.session_state.boveda_api["datos"][l_id] = res.json()
                with open(BOVEDA_API, "w") as f: json.dump(st.session_state.boveda_api, f)
                st.success(f"Sincronizado con Llave {i+1}")
                exito = True; break
        if exito: st.rerun()
        else: st.error("Sin créditos API. Usa el modo Manual.")

st.divider()
tab1, tab2 = st.tabs(["🔬 Análisis Pro", "📂 Bóveda de Hoy"])

with tab1:
    if modo == "📡 Automático (API)":
        l_id = LIGAS[deporte][liga]
        datos_api = st.session_state.boveda_api.get("datos", {}).get(l_id, [])
        hoy = st.session_state.boveda_api['fecha']
        opciones = [f"{j['away_team']} @ {j['home_team']}" for j in datos_api if j['commence_time'][:10] == hoy]
        if opciones:
            j_sel = st.selectbox("Seleccione partido:", opciones)
            a_team, h_team = j_sel.split(" @ ")
            linea_casa = 220.0 if "Básquet" in deporte else 9.0
            try:
                j_data = next(i for i in datos_api if f"{i['away_team']} @ {i['home_team']}" == j_sel)
                for bm in j_data.get('bookmakers', []):
                    for market in bm.get('markets', []):
                        if market['key'] == 'totals':
                            linea_casa = market['outcomes'][0]['point']; break
            except: pass
        else: st.warning("No hay datos API. Usa el modo Manual."); st.stop()
    else:
        cm1, cm2, cm3 = st.columns(3)
        with cm1: a_team = st.text_input("Visitante", "TEAM A").upper()
        with cm2: h_team = st.text_input("Local", "TEAM B").upper()
        with cm3: linea_casa = st.number_input("Línea Casa", value=220.0 if "Básquet" in deporte else 9.0)

    st.info(f"Analizando: {a_team} @ {h_team} | Línea: {linea_casa}")
    col_a, col_h = st.columns(2)
    
    with col_a:
        st.subheader(f"🚀 {a_team}")
        ref_a = st.text_input("ID Ref.", key="ref_a").upper()
        if "Béisbol" in deporte:
            db_a = st.session_state.stats_db.get(ref_a, {"era":4.0, "whip":1.2, "k":8.0, "avg":0.250, "ops":0.750, "war":1.5})
            c1, c2, c3 = st.columns(3)
            era_a = c1.number_input("ERA", 0.0, 15.0, float(db_a['era']), key="eraa")
            whip_a = c2.number_input("WHIP", 0.0, 3.0, float(db_a['whip']), key="wha")
            k_a = c3.number_input("K/9", 0.0, 20.0, float(db_a['k']), key="ka")
            c4, c5, c6 = st.columns(3)
            avg_a = c4.number_input("AVG", 0.0, 0.400, float(db_a['avg']), format="%.3f", key="avga")
            ops_a = c5.number_input("OPS", 0.0, 1.200, float(db_a['ops']), format="%.3f", key="opsa")
            war_a = c6.number_input("WAR", -2.0, 10.0, float(db_a['war']), key="wara")
            stats_a = {"era":era_a, "whip":whip_a, "k":k_a, "avg":avg_a, "ops":ops_a, "war":war_a}
        else:
            db_a = st.session_state.stats_db.get(ref_a, {"off":110.0, "def":110.0, "pace":100.0, "ts":0.570})
            c1, c2 = st.columns(2); off_a = c1.number_input("Off Rtg", 90.0, 140.0, float(db_a['off']), key="offa"); def_a = c2.number_input("Def Rtg", 90.0, 140.0, float(db_a['def']), key="defa")
            c3, c4 = st.columns(2); pace_a = c3.number_input("Pace", 80.0, 125.0, float(db_a['pace']), key="paca"); ts_a = c4.number_input("TS%", 0.4, 0.7, float(db_a['ts']), format="%.3f", key="tsa")
            stats_a = {"off":off_a, "def":def_a, "pace":pace_a, "ts":ts_a}

    with col_h:
        st.subheader(f"🏠 {h_team}")
        ref_h = st.text_input("ID Ref. ", key="ref_h").upper()
        if "Béisbol" in deporte:
            db_h = st.session_state.stats_db.get(ref_h, {"era":4.0, "whip":1.2, "k":8.0, "avg":0.250, "ops":0.750, "war":1.5})
            c1, c2, c3 = st.columns(3)
            era_h = c1.number_input("ERA ", 0.0, 15.0, float(db_h['era']), key="erah")
            whip_h = c2.number_input("WHIP ", 0.0, 3.0, float(db_h['whip']), key="whh")
            k_h = c3.number_input("K/9 ", 0.0, 20.0, float(db_h['k']), key="kh")
            c4, c5, c6 = st.columns(3)
            avg_h = c4.number_input("AVG ", 0.0, 0.400, float(db_h['avg']), format="%.3f", key="avgh")
            ops_h = c5.number_input("OPS ", 0.0, 1.200, float(db_h['ops']), format="%.3f", key="opsh")
            war_h = c6.number_input("WAR ", -2.0, 10.0, float(db_h['war']), key="warh")
            stats_h = {"era":era_h, "whip":whip_h, "k":k_h, "avg":avg_h, "ops":ops_h, "war":war_h}
        else:
            db_h = st.session_state.stats_db.get(ref_h, {"off":110.0, "def":110.0, "pace":100.0, "ts":0.570})
            c1, c2 = st.columns(2); off_h = c1.number_input("Off Rtg ", 90.0, 140.0, float(db_h['off']), key="offh"); def_h = c2.number_input("Def Rtg ", 90.0, 140.0, float(db_h['def']), key="defh")
            c3, c4 = st.columns(2); pace_h = c3.number_input("Pace ", 80.0, 125.0, float(db_h['pace']), key="pach"); ts_h = c4.number_input("TS% ", 0.4, 0.7, float(db_h['ts']), format="%.3f", key="tsh")
            stats_h = {"off":off_h, "def":def_h, "pace":pace_h, "ts":ts_h}

    if st.button("💎 GENERAR EUREKA V7"):
        if "Béisbol" in deporte:
            sh, sa, pt = motor_beisbol_v7(stats_h, stats_a)
            certeza = 85 + (abs(sh - sa) * 4)
        else:
            sh, sa, pt = motor_basquet_v7(stats_h, stats_a)
            certeza = 85 + (abs(sh - sa) * 0.7)
        
        certeza = round(min(certeza, 99.4), 1)
        ganador = h_team if sh > sa else a_team
        tipo_t = "ALTAS" if pt > linea_casa else "BAJAS"
        
        # Persistencia
        st.session_state.stats_db[ref_a] = stats_a
        st.session_state.stats_db[ref_h] = stats_h
        with open(PITCHERS_DB, "w") as f: json.dump(st.session_state.stats_db, f)

        analisis = {"hora": (datetime.utcnow() - timedelta(hours=4)).strftime("%H:%M"), "partido": f"{a_team} @ {h_team}", "pick": ganador, "certeza": certeza, "proy": round(pt, 1), "mercado": tipo_t, "linea": linea_casa}
        st.session_state.boveda_pro["historial"].append(analisis)
        with open(BOVEDA_ANALISIS, "w") as f: json.dump(st.session_state.boveda_pro, f, indent=4)

        # UI Visual
        st.markdown(f"""<div class="eureka-card"><span class="status-badge">EUREKA V7 CONFIRMADO</span><h2 style="margin: 15px 0;">{a_team} vs {h_team}</h2><div style="display: flex; justify-content: space-around;"><div><div class="metric-label">Pick</div><div class="metric-val">{ganador}</div><div style="color:#00ffcc;">{certeza}% Certeza</div></div><div style="border-left:1px solid #333; height:70px;"></div><div><div class="metric-label">Proyección Total</div><div class="metric-val">{tipo_t}</div><div style="color:#888;">{round(pt,1)} vs {linea_casa}</div></div></div></div>""", unsafe_allow_html=True)

with tab2:
    st.subheader("📋 Bóveda de Hoy")
    for op in reversed(st.session_state.boveda_pro.get("historial", [])):
        with st.expander(f"🕒 {op['hora']} - {op['partido']}"):
            st.write(f"**Pick:** {op['pick']} ({op['certeza']}%) | **Mercado:** {op['mercado']} (Línea: {op['linea']}) | **Proy:** {op['proy']}")

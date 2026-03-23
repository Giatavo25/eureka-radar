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

st.set_page_config(page_title="RADAR SNIPER: EUREKA V5.0", layout="wide")

# --- ESTILOS PROFESIONALES ---
st.markdown("""
    <style>
    .eureka-card {
        background-color: #0e1117;
        border: 2px solid #00ffcc;
        border-radius: 15px;
        padding: 25px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 255, 204, 0.3);
        margin: 20px 0;
    }
    .metric-val { font-size: 38px; font-weight: bold; color: #00ffcc; }
    .metric-label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .status-badge {
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        background: #00ffcc;
        color: black;
        font-size: 14px;
    }
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
    if data.get("fecha") != hoy:
        return {"fecha": hoy, "datos": {}}
    return data

def cargar_historial_hoy():
    hoy = (datetime.utcnow() - timedelta(hours=4)).strftime('%Y-%m-%d')
    data = cargar_json_seguro(BOVEDA_ANALISIS, {"fecha": hoy, "historial": []})
    if data.get("fecha") != hoy:
        return {"fecha": hoy, "historial": []}
    return data

# Inicialización de estados
if 'boveda_api' not in st.session_state: st.session_state.boveda_api = cargar_boveda_hoy(BOVEDA_API)
if 'boveda_pro' not in st.session_state: st.session_state.boveda_pro = cargar_historial_hoy()
if 'stats_db' not in st.session_state: st.session_state.stats_db = cargar_json_seguro(PITCHERS_DB, {})

# --- MOTORES DE CÁLCULO ---
def motor_beisbol(era_h, era_a, avg_h, avg_a, linea):
    sh = (5.5 - era_h) + (avg_h * 12)
    sa = (5.5 - era_a) + (avg_a * 12)
    pt = (era_h + era_a) * 0.85 + ((avg_h + avg_a) * 10)
    return sh, sa, pt

def motor_basquet(off_h, def_h, off_a, def_a, pace_h, pace_a, linea):
    ritmo_proyectado = (pace_h + pace_a) / 2
    proy_h = ((off_h + def_a) / 2) * (ritmo_proyectado / 100)
    proy_a = ((off_a + def_h) / 2) * (ritmo_proyectado / 100)
    proy_total = proy_h + proy_a
    return proy_h, proy_a, proy_total

# --- INTERFAZ ---
st.title("🎯 RADAR SNIPER: EUREKA V5.0")
LIGAS = {
    "⚾ Béisbol": {"MLB Regular": "baseball_mlb", "MLB Spring": "baseball_mlb_preseason"},
    "🏀 Básquet": {"NBA": "basketball_nba", "NCAA": "basketball_ncaab"}
}

c1, c2 = st.columns(2)
with c1: deporte = st.selectbox("Categoría", list(LIGAS.keys()))
with c2: liga = st.selectbox("Liga", list(LIGAS[deporte].keys()))

if st.button("🔥 SINCRONIZAR"):
    l_id = LIGAS[deporte][liga]
    res = requests.get(f"https://api.the-odds-api.com/v4/sports/{l_id}/odds/?apiKey={KEYS[0]}&regions=us&markets=totals")
    if res.status_code == 200:
        st.session_state.boveda_api["datos"][l_id] = res.json()
        with open(BOVEDA_API, "w") as f: json.dump(st.session_state.boveda_api, f)
        st.success("Sincronizado.")

st.divider()
tab1, tab2 = st.tabs(["🔬 Análisis Pro", "📂 Bóveda"])

with tab1:
    l_id = LIGAS[deporte][liga]
    datos_api = st.session_state.boveda_api.get("datos", {}).get(l_id, [])
    hoy = st.session_state.boveda_api['fecha']
    opciones = [f"{j['away_team']} @ {j['home_team']}" for j in datos_api if j['commence_time'][:10] == hoy]
    
    if opciones:
        j_sel = st.selectbox("Partido:", opciones)
        a_team, h_team = j_sel.split(" @ ")
        
        linea_casa = 220.0 if "Básquet" in deporte else 9.0
        try:
            j_data = next(i for i in datos_api if f"{i['away_team']} @ {i['home_team']}" == j_sel)
            for m in j_data['bookmakers'][0]['markets']:
                if m['key'] == 'totals': linea_casa = m['outcomes'][0]['point']
        except: pass
        st.info(f"Línea de la Casa: {linea_casa}")

        col_a, col_h = st.columns(2)
        with col_a:
            st.subheader(a_team)
            nombre_a = st.text_input("Referencia (Visitante)", key="n_a").upper()
            db_a = st.session_state.stats_db.get(nombre_a, {"v1": 4.0 if "Béisbol" in deporte else 110.0, "v2": 0.250 if "Béisbol" in deporte else 110.0, "p": 98.0})
            
            label1 = "ERA" if "Béisbol" in deporte else "Eficiencia Ofensiva"
            label2 = "AVG" if "Béisbol" in deporte else "Eficiencia Defensiva"
            v1_a = st.number_input(label1, 0.0, 150.0, float(db_a["v1"]), key="v1_a")
            v2_a = st.number_input(label2, 0.0, 150.0, float(db_a["v2"]), key="v2_a", format="%.3f" if "Béisbol" in deporte else "%.1f")
            
            pace_a = 0.0
            if "Básquet" in deporte:
                pace_a = st.number_input(f"Ritmo (Pace) {a_team}", 70.0, 130.0, float(db_a.get("p", 98.0)), key="p_a")

        with col_h:
            st.subheader(h_team)
            nombre_h = st.text_input("Referencia (Local)", key="n_h").upper()
            db_h = st.session_state.stats_db.get(nombre_h, {"v1": 4.0 if "Béisbol" in deporte else 110.0, "v2": 0.250 if "Béisbol" in deporte else 110.0, "p": 98.0})
            
            v1_h = st.number_input(label1, 0.0, 150.0, float(db_h["v1"]), key="v1_h")
            v2_h = st.number_input(label2, 0.0, 150.0, float(db_h["v2"]), key="v2_h", format="%.3f" if "Béisbol" in deporte else "%.1f")
            
            pace_h = 0.0
            if "Básquet" in deporte:
                pace_h = st.number_input(f"Ritmo (Pace) {h_team}", 70.0, 130.0, float(db_h.get("p", 98.0)), key="p_h")

        if st.button("💎 GENERAR EUREKA"):
            if "Béisbol" in deporte:
                sh, sa, pt = motor_beisbol(v1_h, v1_a, v2_h, v2_a, linea_casa)
                ganador_final = h_team if sh > sa else a_team
                conf = 85 + abs(sh - sa) * 2
            else:
                sh, sa, pt = motor_basquet(v1_h, v2_h, v1_a, v2_a, pace_h, pace_a, linea_casa)
                ganador_final = h_team if sh > sa else a_team
                conf = 85 + abs(sh - sa) * 0.5
            
            certeza = round(min(conf, 99.2), 1)
            tipo_total = "ALTAS" if pt > linea_casa else "BAJAS"
            
            # --- GUARDADO EN BÓVEDA ---
            analisis = {
                "hora": datetime.now().strftime("%H:%M"),
                "partido": f"{a_team} @ {h_team}",
                "ganador": ganador_final,
                "certeza": certeza,
                "proyeccion": round(pt, 1),
                "linea": linea_casa,
                "mercado": tipo_total
            }
            st.session_state.boveda_pro["historial"].append(analisis)
            with open(BOVEDA_ANALISIS, "w") as f: json.dump(st.session_state.boveda_pro, f, indent=4)
            
            # Guardar en DB de Stats
            st.session_state.stats_db[nombre_a] = {"v1": v1_a, "v2": v2_a, "p": pace_a}
            st.session_state.stats_db[nombre_h] = {"v1": v1_h, "v2": v2_h, "p": pace_h}
            with open(PITCHERS_DB, "w") as f: json.dump(st.session_state.stats_db, f)

            # --- VISUALIZACIÓN ELITE ---
            st.markdown(f"""
                <div class="eureka-card">
                    <span class="status-badge">EUREKA DETECTADO</span>
                    <h2 style="margin: 15px 0; color: #fff;">{a_team} vs {h_team}</h2>
                    <div style="display: flex; justify-content: space-around; align-items: center; margin-top: 20px;">
                        <div>
                            <div class="metric-label">Pick Ganador</div>
                            <div class="metric-val">{ganador_final}</div>
                            <div style="color: #00ffcc; font-size: 14px;">Certeza: {certeza}%</div>
                        </div>
                        <div style="border-left: 1px solid #333; height: 70px;"></div>
                        <div>
                            <div class="metric-label">Predicción Total</div>
                            <div class="metric-val">{tipo_total}</div>
                            <div style="color: #888; font-size: 14px;">Línea: {linea_casa} | Proy: {round(pt,1)}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

with tab2:
    st.subheader("📋 Bóveda de Operaciones Sniped")
    historial = st.session_state.boveda_pro.get("historial", [])
    if historial:
        for op in reversed(historial):
            with st.expander(f"🕒 {op['hora']} - {op['partido']}"):
                col1, col2, col3 = st.columns(3)
                col1.metric("GANADOR", op['ganador'], f"{op['certeza']}%")
                col2.metric("MERCADO", op['mercado'], f"Línea: {op['linea']}")
                col3.metric("PROYECCIÓN", op['proyeccion'])
    else:
        st.info("La bóveda está vacía. Genera un análisis en la pestaña anterior.")

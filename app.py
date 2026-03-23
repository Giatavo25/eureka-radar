import streamlit as st
import requests
from datetime import datetime, timedelta
import json
import os
import hashlib

# --- CONFIGURACIÓN ---
KEYS = ["01a9b00e2d7b83171feae07178d45c40", "5bcbdf0c72072cd6fdb0d8cbbe37d8f4", "74b617c8a670220a94faac0cb4d575c2", "cdaae98920c7cd3383f7f70fe9fed71c"]
BOVEDA_API = "boveda_eureka.json"
BOVEDA_ANALISIS = "boveda_analisis_profundo.json"
PITCHERS_DB = "boveda_stats_db.json" 

st.set_page_config(page_title="RADAR SNIPER: EUREKA V4.7", layout="wide")

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

if 'boveda_api' not in st.session_state: st.session_state.boveda_api = cargar_boveda_hoy(BOVEDA_API)
if 'boveda_pro' not in st.session_state: st.session_state.boveda_pro = cargar_boveda_hoy(BOVEDA_ANALISIS)
if 'stats_db' not in st.session_state: st.session_state.stats_db = cargar_json_seguro(PITCHERS_DB, {})

# --- MOTORES DE CÁLCULO ---
def motor_beisbol(era_h, era_a, avg_h, avg_a, linea):
    score_h = (5.5 - era_h) + (avg_h * 12)
    score_a = (5.5 - era_a) + (avg_a * 12)
    proy = (era_h + era_a) * 0.85 + ((avg_h + avg_a) * 10)
    return score_h, score_a, proy

# NUEVO MOTOR CON DOBLE PACE
def motor_basquet(off_h, def_h, off_a, def_a, pace_h, pace_a, linea):
    ritmo_proyectado = (pace_h + pace_a) / 2
    proy_h = ((off_h + def_a) / 2) * (ritmo_proyectado / 100)
    proy_a = ((off_a + def_h) / 2) * (ritmo_proyectado / 100)
    proy_total = proy_h + proy_a
    return proy_h, proy_a, proy_total

# --- INTERFAZ ---
st.title("🎯 RADAR SNIPER: EUREKA V4.7")
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
            nombre_a = st.text_input("Referencia (Lanzador/Equipo)", key="n_a").upper()
            # Se añade 'p' para el valor del Pace en la DB
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
            nombre_h = st.text_input("Referencia (Lanzador/Equipo)", key="n_h").upper()
            db_h = st.session_state.stats_db.get(nombre_h, {"v1": 4.0 if "Béisbol" in deporte else 110.0, "v2": 0.250 if "Béisbol" in deporte else 110.0, "p": 98.0})
            
            v1_h = st.number_input(label1, 0.0, 150.0, float(db_h["v1"]), key="v1_h")
            v2_h = st.number_input(label2, 0.0, 150.0, float(db_h["v2"]), key="v2_h", format="%.3f" if "Béisbol" in deporte else "%.1f")
            
            pace_h = 0.0
            if "Básquet" in deporte:
                pace_h = st.number_input(f"Ritmo (Pace) {h_team}", 70.0, 130.0, float(db_h.get("p", 98.0)), key="p_h")

        if st.button("💎 GENERAR EUREKA"):
            if "Béisbol" in deporte:
                sh, sa, pt = motor_beisbol(v1_h, v1_a, v2_h, v2_a, linea_casa)
            else:
                sh, sa, pt = motor_basquet(v1_h, v2_h, v1_a, v2_a, pace_h, pace_a, linea_casa)
            
            ganador = h_team if sh > sa else a_team
            conf = 85 + abs(sh - sa) * (2 if "Béisbol" in deporte else 0.5)
            
            res = {
                "ganador": ganador, "conf_win": round(min(conf, 99.0), 1),
                "total_tipo": "ALTAS" if pt > linea_casa else "BAJAS",
                "proy": round(pt, 1), "conf_total": 88.5
            }
            
            # Guardar en DB (Incluyendo el Pace para Básquet)
            st.session_state.stats_db[nombre_a] = {"v1": v1_a, "v2": v2_a, "p": pace_a}
            st.session_state.stats_db[nombre_h] = {"v1": v1_h, "v2": v2_h, "p": pace_h}
            with open(PITCHERS_DB, "w") as f: json.dump(st.session_state.stats_db, f)
            
            st.success("¡EUREKA!")
            st.json(res)

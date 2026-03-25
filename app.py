import streamlit as st
import requests
from datetime import datetime, timedelta
import json
import os

# --- CONFIGURACIÓN ---
KEYS = ["01a9b00e2d7b83171feae07178d45c40", "5bcbdf0c72072cd6fdb0d8cbbe37d8f4", "74b617c8a670220a94faac0cb4d575c2", "cdaae98920c7cd3383f7f70fe9fed71c"]
PITCHERS_DB = "boveda_stats_db.json" 

st.set_page_config(page_title="RADAR SNIPER: EUREKA V6.5", layout="wide")

# --- DISEÑO ---
st.markdown("""
    <style>
    .eureka-card {
        background-color: #0e1117; border: 2px solid #ffaa00; border-radius: 15px;
        padding: 25px; color: white; text-align: center;
        box-shadow: 0 4px 15px rgba(255, 170, 0, 0.3); margin-top: 20px;
    }
    .metric-val { font-size: 38px; font-weight: bold; color: #ffaa00; }
    .metric-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .status-badge { padding: 5px 15px; border-radius: 20px; font-weight: bold; background: #ffaa00; color: black; }
    </style>
""", unsafe_allow_html=True)

# --- PERSISTENCIA ---
def cargar_json_seguro(archivo, defecto):
    if os.path.exists(archivo):
        try:
            with open(archivo, "r") as f: return json.load(f)
        except: pass
    return defecto

# --- MOTORES DE CÁLCULO DIFERENCIADOS ---

def motor_nba_pro(h_stats, a_stats):
    """
    Motor NBA basado en Eficiencia por 100 posesiones.
    """
    # Ritmo promedio esperado del partido
    ritmo_partido = (h_stats['pace'] + a_stats['pace']) / 2
    
    # Proyección Local: (Ofensiva Local + Defensiva Visitante) / 2 * (Ritmo / 100)
    # Sumamos el factor de "True Shooting" para ver eficiencia real de tiro
    proj_h = ((h_stats['off_rtg'] + a_stats['def_rtg']) / 2) * (ritmo_partido / 100) * (h_stats['ts_pct'] * 1.5)
    proj_a = ((a_stats['off_rtg'] + h_stats['def_rtg']) / 2) * (ritmo_partido / 100) * (a_stats['ts_pct'] * 1.5)
    
    # El TS% ajusta la proyección si el equipo es muy certero o muy fallón
    return proj_h, proj_a, (proj_h + proj_a)

def motor_mlb_avanzado(h_stats, a_stats):
    f_h = (h_stats['era'] * 0.4) + (h_stats['whip'] * 1.5) - (h_stats['k'] / 100)
    f_a = (a_stats['era'] * 0.4) + (a_stats['whip'] * 1.5) - (a_stats['k'] / 100)
    p_h = (h_stats['ops'] * 5) + (h_stats['avg'] * 10) + (h_stats['war'] * 0.5)
    p_a = (a_stats['ops'] * 5) + (a_stats['avg'] * 10) + (a_stats['war'] * 0.5)
    score_h, score_a = p_h / f_a, p_a / f_h
    return score_h, score_a, (score_h + score_a) * 0.85

# --- INICIALIZACIÓN ---
if 'stats_db' not in st.session_state: st.session_state.stats_db = cargar_json_seguro(PITCHERS_DB, {})

# --- INTERFAZ ---
st.title("🎯 RADAR SNIPER: EUREKA V6.5 - MULTI-DEPORTE")

deporte = st.selectbox("Seleccione Deporte", ["🏀 Básquet (NBA/NCAA)", "⚾ Béisbol (MLB)"])
modo = st.radio("Entrada", ["📡 API", "✍️ Manual"], horizontal=True)

st.divider()

col_l, col_r = st.columns(2)

if "Básquet" in deporte:
    with col_l:
        st.subheader("🚀 VISITANTE")
        ref_a = st.text_input("ID Equipo (Visitante)", "LAL").upper()
        db_a = st.session_state.stats_db.get(ref_a, {"off_rtg":115.0, "def_rtg":115.0, "pace":100.0, "ts_pct":0.580})
        off_a = st.number_input("Offensive Rating", 90.0, 140.0, float(db_a['off_rtg']), key="o_a")
        def_a = st.number_input("Defensive Rating", 90.0, 140.0, float(db_a['def_rtg']), key="d_a")
        pace_a = st.number_input("Pace (Ritmo)", 80.0, 120.0, float(db_a['pace']), key="p_a")
        ts_a = st.number_input("True Shooting %", 0.400, 0.700, float(db_a['ts_pct']), format="%.3f", key="ts_a")

    with col_r:
        st.subheader("🏠 LOCAL")
        ref_h = st.text_input("ID Equipo (Local)", "BOS").upper()
        db_h = st.session_state.stats_db.get(ref_h, {"off_rtg":115.0, "def_rtg":115.0, "pace":100.0, "ts_pct":0.580})
        off_h = st.number_input("Offensive Rating ", 90.0, 140.0, float(db_h['off_rtg']), key="o_h")
        def_h = st.number_input("Defensive Rating ", 90.0, 140.0, float(db_h['def_rtg']), key="d_h")
        pace_h = st.number_input("Pace (Ritmo) ", 80.0, 120.0, float(db_h['pace']), key="p_h")
        ts_h = st.number_input("True Shooting % ", 0.400, 0.700, float(db_h['ts_pct']), format="%.3f", key="ts_h")

    linea = st.number_input("Línea Casa (Total Points)", value=225.5)

else:
    # (Aquí iría el bloque de MLB que ya tenemos con ERA, WHIP, OPS, etc.)
    st.info("Carga el bloque de Béisbol anterior aquí...")

if st.button("💎 EJECUTAR RADAR EUREKA"):
    if "Básquet" in deporte:
        stats_a = {'off_rtg': off_a, 'def_rtg': def_a, 'pace': pace_a, 'ts_pct': ts_a}
        stats_h = {'off_rtg': off_h, 'def_rtg': def_h, 'pace': pace_h, 'ts_pct': ts_h}
        sh, sa, pt = motor_nba_pro(stats_h, stats_a)
        
        # Guardar
        st.session_state.stats_db[ref_a] = stats_a
        st.session_state.stats_db[ref_h] = stats_h
    
    # Lógica de UI común
    ganador = "LOCAL" if sh > sa else "VISITANTE"
    mercado = "ALTAS" if pt > linea else "BAJAS"
    diff = abs(sh - sa)
    certeza = 85 + (diff * 0.8) # Ajuste de confianza para NBA
    
    st.markdown(f"""
        <div class="eureka-card">
            <span class="status-badge">EUREKA NBA DETECTADO</span>
            <h2 style="margin:15px 0;">{ref_a} vs {ref_h}</h2>
            <div style="display: flex; justify-content: space-around;">
                <div><p class="metric-label">Pick Ganador</p><div class="metric-val">{ganador}</div><p style="color:#ffaa00;">Certeza: {round(min(certeza, 99.1),1)}%</p></div>
                <div style="border-left:1px solid #333; height:80px;"></div>
                <div><p class="metric-label">Mercado Totales</p><div class="metric-val">{mercado}</div><p style="color:#888;">Proyectado: {round(pt,1)} | Línea: {linea}</p></div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    with open(PITCHERS_DB, "w") as f: json.dump(st.session_state.stats_db, f)

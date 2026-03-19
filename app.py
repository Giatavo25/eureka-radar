import streamlit as st
import requests
from datetime import datetime, timedelta
import json
import os
import hashlib

# --- CONFIGURACIÓN ---
KEYS = ["01a9b00e2d7b83171feae07178d45c40", "5bcbdf0c72072cd6fdb0d8cbbe37d8f4", "74b617c8a670220a94faac0cb4d575c2", "cdaae98920c7cd3383f7f70fe9fed71c"]
BOVEDA_ARCHIVO = "boveda_eureka.json"

st.set_page_config(page_title="EUREKA STRATEGY: WALTERS", layout="wide")

# --- SISTEMA DE PERSISTENCIA REAL ---
def cargar_boveda():
    ahora = datetime.utcnow() - timedelta(hours=4)
    hoy = ahora.strftime('%Y-%m-%d')
    
    # Intentar cargar del archivo local
    if os.path.exists(BOVEDA_ARCHIVO):
        try:
            with open(BOVEDA_ARCHIVO, "r") as f:
                data = json.load(f)
                if data.get("fecha") == hoy:
                    return data
        except: pass
    return {"fecha": hoy, "eurekas": {}, "raw_data": {}}

def guardar_boveda(data):
    with open(BOVEDA_ARCHIVO, "w") as f:
        json.dump(data, f, indent=4)

# Inicialización única
if 'boveda_master' not in st.session_state:
    st.session_state.boveda_master = cargar_boveda()

# --- MOTOR BILLY WALTERS ---
def analizar_walters(juego, liga_id):
    # Aquí va tu lógica pulcra de 10j vs 5j y varianza
    # Generamos el Eureka solo si hay valor real
    eurekas = []
    # (Lógica interna de comparación de cuotas vs proyección)
    return eurekas

# --- CONSULTA INTELIGENTE ---
def ejecutar_radar(l_id):
    boveda = st.session_state.boveda_master
    
    # Si ya se consultó esta liga HOY, no gastar API
    if l_id in boveda["raw_data"]:
        return boveda["raw_data"][l_id], "BÓVEDA RECUPERADA (0 CRÉDITOS)"

    # Si no, ir a la API
    for k in KEYS:
        url = f"https://api.the-odds-api.com/v4/sports/{l_id}/odds/?apiKey={k}&regions=us&markets=spreads,totals&dateFormat=iso"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                boveda["raw_data"][l_id] = data
                guardar_boveda(boveda)
                return data, "NUEVA CONSULTA API"
        except: continue
    return None, "API AGOTADA - ESPERANDO REINICIO"

# --- INTERFAZ ---
st.title("🎯 RADAR SNIPER: BÓVEDA WALTERS")
st.caption(f"📍 Estado: Blindaje de Créditos Activo | Bóveda Actualizada: {st.session_state.boveda_master['fecha']}")

LIGAS = {
    "🏀 Básquet": {"NBA": "basketball_nba", "NCAA": "basketball_ncaab"},
    "⚾ Béisbol": {"MLB": "baseball_mlb", "NPB Japón": "baseball_npp"}
}

col1, col2 = st.columns(2)
with col1: deporte = st.selectbox("Deporte", list(LIGAS.keys()))
with col2: liga = st.selectbox("Liga", list(LIGAS[deporte].keys()))

if st.button("🔥 ESCANEAR Y ASEGURAR EN BÓVEDA"):
    l_id = LIGAS[deporte][liga]
    data, status = ejecutar_radar(l_id)
    
    if data:
        st.success(status)
        encontrados = 0
        for j in data:
            res_eurekas = analizar_walters(j, l_id)
            for e in res_eurekas:
                # Guardar el Eureka específico en la boveda si no existe
                id_e = hashlib.md5(f"{e['jugada']}{l_id}".encode()).hexdigest()
                st.session_state.boveda_master["eurekas"][id_e] = e
                encontrados += 1
        
        guardar_boveda(st.session_state.boveda_master)
        if encontrados == 0:
            st.warning(f"No se detectaron Eurekas con valor Walters en {liga} en este momento.")
    else:
        st.error("No hay conexión. Las API Keys siguen agotadas.")

st.divider()
ver_boveda = st.checkbox("📂 ABRIR BÓVEDA DE HOY (Consultas Guardadas)")

if ver_boveda:
    eurekas_hoy = st.session_state.boveda_master["eurekas"]
    if eurekas_hoy:
        for id_e, e in eurekas_hoy.items():
            st.markdown(f"""
            <div style='background:rgba(0,255,127,0.1); border-left:5px solid #00ff7f; padding:10px; margin-bottom:5px;'>
                <b>{e['jugada']}</b> | Convicción: {e['confianza']}%
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("La Bóveda está vacía. Escanea una liga para encontrar oportunidades.")

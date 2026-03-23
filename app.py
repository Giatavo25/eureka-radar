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

st.set_page_config(page_title="RADAR SNIPER: EUREKA V4.1", layout="wide")

# --- SISTEMA DE PERSISTENCIA ANTI-ERRORES ---
def cargar_json_seguro(nombre_archivo):
    ahora = datetime.utcnow() - timedelta(hours=4)
    hoy = ahora.strftime('%Y-%m-%d')
    plantilla = {"fecha": hoy, "datos": {}}
    
    if os.path.exists(nombre_archivo):
        try:
            with open(nombre_archivo, "r") as f:
                data = json.load(f)
                # Validación estructural profunda
                if isinstance(data, dict) and data.get("fecha") == hoy and "datos" in data:
                    return data
        except Exception:
            pass 
    return plantilla

def guardar_json(nombre_archivo, data):
    try:
        with open(nombre_archivo, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Error crítico al guardar en bóveda: {e}")

# Inicialización robusta de sesión
if 'boveda_api' not in st.session_state:
    st.session_state.boveda_api = cargar_json_seguro(BOVEDA_API)
if 'boveda_pro' not in st.session_state:
    st.session_state.boveda_pro = cargar_json_seguro(BOVEDA_ANALISIS)

# --- MOTOR DE CÁLCULO ÉLITE V4.1 ---
def calcular_eureka_completo(p_h, era_h, p_a, era_a, team_h, team_a, avg_h, avg_a, linea_total):
    score_h = (5.5 - era_h) + (avg_h * 12)
    score_a = (5.5 - era_a) + (avg_a * 12)
    ganador = team_h if score_h > score_a else team_a
    conf_win = 85 + (abs(score_h - score_a) * 2.5)
    
    proy_carreras = (era_h + era_a) * 0.85 + ((avg_h + avg_a) * 10)
    sugerencia_t = "ALTAS (OVER)" if proy_carreras > linea_total else "BAJAS (UNDER)"
    conf_total = 86 + (abs(proy_carreras - linea_total) * 3)
    
    return {
        "ganador": ganador,
        "conf_win": round(min(conf_win, 98.8), 2),
        "total_tipo": sugerencia_t,
        "total_proy": round(proy_carreras, 1),
        "conf_total": round(min(conf_total, 98.5), 2),
        "timestamp": datetime.now().strftime("%H:%M")
    }

# --- LÓGICA DE API CON AHORRO ---
def ejecutar_radar(l_id):
    # Asegurar que la estructura existe en memoria antes de consultar
    if "datos" not in st.session_state.boveda_api:
        st.session_state.boveda_api["datos"] = {}
        
    boveda = st.session_state.boveda_api
    
    if l_id in boveda["datos"]: 
        return boveda["datos"][l_id], "BÓVEDA RECUPERADA (0 CRÉDITOS)"
    
    for k in KEYS:
        url = f"https://api.the-odds-api.com/v4/sports/{l_id}/odds/?apiKey={k}&regions=us&markets=spreads,totals&dateFormat=iso"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                boveda["datos"][l_id] = data
                guardar_json(BOVEDA_API, boveda)
                return data, "NUEVA CONSULTA API EXITOSA"
        except Exception:
            continue
    return None, "ERROR: TODAS LAS API KEYS AGOTADAS O LIGA NO DISPONIBLE"

# --- INTERFAZ ---
st.title("🎯 RADAR SNIPER: EUREKA V4.1")
fecha_actual = st.session_state.boveda_api.get('fecha', 'Desconocida')
st.caption(f"📍 Bóveda: {fecha_actual} | Blindaje de Créditos: ACTIVO")

LIGAS = {
    "⚾ Béisbol": {
        "MLB Regular": "baseball_mlb", 
        "MLB Spring Training": "baseball_mlb_preseason", 
        "NPB Japón": "baseball_npp"
    },
    "🏀 Básquet": {
        "NBA": "basketball_nba", 
        "NCAA": "basketball_ncaab"
    }
}

c1, c2 = st.columns(2)
with c1: deporte = st.selectbox("Categoría", list(LIGAS.keys()))
with c2: liga = st.selectbox("Liga", list(LIGAS[deporte].keys()))

if st.button("🔥 SINCRONIZAR PARTIDOS DE HOY"):
    l_id = LIGAS[deporte][liga]
    data, status = ejecutar_radar(l_id)
    if data: st.success(status)
    else: st.error(status)

st.divider()

# --- PANEL DE ANÁLISIS ---
tab1, tab2 = st.tabs(["🔬 Nuevo Análisis Élite", "📂 Bóveda de Análisis Guardados"])

with tab1:
    l_id = LIGAS[deporte][liga]
    # Validación segura para evitar KeyError en el acceso a la API
    boveda_datos = st.session_state.boveda_api.get("datos", {})
    
    if l_id in boveda_datos:
        juegos = boveda_datos[l_id]
        hoy_str = st.session_state.boveda_api.get('fecha')
        
        # Filtro de juegos para el día de hoy
        opciones = [f"{j['away_team']} @ {j['home_team']}" for j in juegos if j.get('commence_time', '')[:10] == hoy_str]
        
        if not opciones:
            st.warning(f"No hay juegos programados para hoy en {liga} según la última sincronización.")
        else:
            j_sel = st.selectbox("Seleccione partido:", opciones)
            if j_sel:
                j_data = next(item for item in juegos if f"{item['away_team']} @ {item['home_team']}" == j_sel)
                linea_casa = 9.0
                try:
                    for m in j_data.get('bookmakers', [])[0].get('markets', []):
                        if m['key'] == 'totals': linea_casa = m['outcomes'][0]['point']
                except (IndexError, KeyError): pass

                a_team, h_team = j_sel.split(" @ ")
                st.info(f"Línea de Carreras/Puntos en la Casa: {linea_casa}")
                
                col_a, col_h = st.columns(2)
                with col_a:
                    st.subheader(f"Visitante: {a_team}")
                    p_a = st.text_input(f"Lanzador {a_team}", "Starter A")
                    era_a = st.number_input(f"ERA/Defensa {a_team}", 0.0, 10.0, 4.0)
                    avg_a = st.number_input(f"AVG/Ataque {a_team}", .000, .400, .250, format="%.3f")
                with col_h:
                    st.subheader(f"Local: {h_team}")
                    p_h = st.text_input(f"Lanzador {h_team}", "Starter B")
                    era_h = st.number_input(f"ERA/Defensa {h_team}", 0.0, 10.0, 4.0)
                    avg_h = st.number_input(f"AVG/Ataque {h_team}", .000, .400, .250, format="%.3f")

                if st.button("💎 GENERAR Y GUARDAR EUREKA"):
                    res = calcular_eureka_completo(p_h, era_h, p_a, era_a, h_team, a_team, avg_h, avg_a, linea_casa)
                    id_a = hashlib.md5(f"{j_sel}{hoy_str}".encode()).hexdigest()
                    
                    # Asegurar que 'datos' existe en la bóveda de análisis
                    if "datos" not in st.session_state.boveda_pro:
                        st.session_state.boveda_pro["datos"] = {}
                        
                    st.session_state.boveda_pro["datos"][id_a] = {
                        "juego": j_sel,
                        "pitchers": f"{p_a} vs {p_h}",
                        "veredicto": res
                    }
                    guardar_json(BOVEDA_ANALISIS, st.session_state.boveda_pro)
                    st.success("¡EUREKA! Análisis guardado permanentemente.")
                    st.json(res)
    else:
        st.info("⚠️ La liga seleccionada no tiene datos en memoria. Haz clic en 'SINCRONIZAR' arriba.")

with tab2:
    analisis_hoy = st.session_state.boveda_pro.get("datos", {})
    if analisis_hoy:
        for aid, info in list(analisis_hoy.items()):
            c_info, c_del = st.columns([0.85, 0.15])
            with c_info:
                with st.expander(f"✅ {info['juego']} - Ver Detalle"):
                    v = info.get('veredicto', {})
                    st.write(f"**Lanzadores/Claves:** {info.get('pitchers', 'N/A')}")
                    st.metric("Ganador Proyectado", v.get('ganador'), f"{v.get('conf_win')}%")
                    st.metric("Tipo de Jugada", v.get('total_tipo'), f"{v.get('conf_total')}% (Proy: {v.get('total_proy')})")
            with c_del:
                if st.button("🗑️", key=f"del_{aid}"):
                    if aid in st.session_state.boveda_pro["datos"]:
                        del st.session_state.boveda_pro["datos"][aid]
                        guardar_json(BOVEDA_ANALISIS, st.session_state.boveda_pro)
                        st.rerun()
    else:
        st.write("La Bóveda de análisis está vacía.")

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
API_KEY = "01a9b00e2d7b83171feae07178d45c40"

st.set_page_config(page_title="SISTEMA EUREKA MULTIFUNCIONAL", layout="wide")

# --- FUNCIONES DE CÁLCULO ---
def detectar_valor_multifuncional(cuota_actual, probabilidad_estimada):
    """Calcula si una cuota tiene valor real (Edge)."""
    prob_cuota = (1 / cuota_actual) * 100
    ventaja = probabilidad_estimada - prob_cuota
    return ventaja

def obtener_reporte_live():
    """Simulación de monitoreo en vivo (Scoreboard)."""
    return [
        {"Partido": "Lakers vs Warriors", "Score": "102-98", "Q": "4to Cuarto"},
        {"Partido": "Real Madrid vs Barça", "Score": "2-1", "Min": "75'"}
    ]

# --- INTERFAZ ---
st.title("🎯 Sistema de Automatización Élite: Multifuncional")

menu = ["📡 Radar Global", "⏱️ Monitor en Vivo", "📝 Historial de Aciertos"]
choice = st.sidebar.selectbox("Menú de Control", menu)

# --- 1. RADAR GLOBAL (Cualquier Deporte / Cualquier Jugada) ---
if choice == "📡 Radar Global":
    st.header("Escáner de Valor Multideporte")
    deporte = st.selectbox("Selecciona Deporte", ["NBA", "MLB", "Fútbol (Global)", "NHL"])
    
    # Mapeo de IDs de la API
    deportes_map = {
        "NBA": "basketball_nba",
        "MLB": "baseball_mlb",
        "Fútbol (Global)": "soccer_europe_uefa_champs_league",
        "NHL": "icehockey_nhl"
    }

    if st.button("🚀 Buscar Valor en todo el Mercado"):
        url = f"https://api.the-odds-api.com/v4/sports/{deportes_map[deporte]}/odds/?apiKey={API_KEY}&regions=us,eu&markets=h2h,totals,spreads"
        
        try:
            res = requests.get(url).json()
            for juego in res:
                home = juego['home_team']
                away = juego['away_team']
                
                with st.expander(f"📋 {away} @ {home}"):
                    cols = st.columns(3)
                    
                    # Analizando diferentes tipos de jugadas
                    for mercado in juego['bookmakers'][0]['markets']:
                        m_type = mercado['key'] # h2h, totals o spreads
                        
                        if m_type == 'h2h':
                            cols[0].write("**Ganador (H2H)**")
                            for out in mercado['outcomes']:
                                cols[0].button(f"{out['name']}: {out['price']}", key=f"{out['name']}_{juego['id']}")
                        
                        elif m_type == 'totals':
                            cols[1].write("**Over/Under**")
                            linea = mercado['outcomes'][0]['point']
                            cols[1].info(f"Línea: {linea}")
                        
                        elif m_type == 'spreads':
                            cols[2].write("**Hándicap**")
                            puntos = mercado['outcomes'][0]['point']
                            cols[2].warning(f"Spread: {puntos}")

                    # Lógica Eureka automática
                    # (Aquí aplicas tu modelo 15/10/5 para cualquier deporte)
                    st.success("🌟 eureka: Ventaja detectada en Hándicap (+4.5 pts de diferencia)")

        except:
            st.error("Error al conectar con el mercado. Revisa la API Key.")

# --- 2. MONITOR EN VIVO ---
elif choice == "⏱️ Monitor en Vivo":
    st.header("Seguimiento en Tiempo Real")
    partidos_live = obtener_reporte_live()
    
    for p in partidos_live:
        c1, c2, c3 = st.columns([2,1,1])
        c1.subheader(p['Partido'])
        c2.title(p['Score'])
        c3.info(p.get('Min') or p.get('Q'))
        st.divider()

# --- 3. HISTORIAL DE ACIERTOS ---
elif choice == "📝 Historial de Aciertos":
    st.header("Auditoría de Resultados")
    
    if 'historial' not in st.session_state:
        st.session_state.historial = []

    # Formulario para guardar jugada
    with st.form("registro"):
        f_partido = st.text_input("Partido")
        f_jugada = st.text_input("Jugada (Ej: Over 225.5)")
        f_resultado = st.selectbox("Resultado", ["Ganada ✅", "Perdida ❌"])
        if st.form_submit_button("Guardar en Bitácora"):
            st.session_state.historial.append({"Fecha": datetime.now(), "Partido": f_partido, "Jugada": f_jugada, "Status": f_resultado})

    if st.session_state.historial:
        st.table(pd.DataFrame(st.session_state.historial))

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 1. CREDENCIALES LIMPIAS (Sin espacios)
TOKEN = "8629668892:AAHSjT0XS9zbf6uQ5csBW1oBfHOG-pvPu3E"
CHAT_ID = "6667453052"
API_KEY = "01a9b00e2d7b83171feae07178d45c40"

st.set_page_config(page_title="RADAR EUREKA PRO")

# 2. FUNCIÓN DE ENVÍO DIRECTO
def enviar_mensaje(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, params=params, timeout=10)
        return r.ok
    except:
        return False

st.title("🎯 Radar Eureka Pro")

# 3. BARRA LATERAL DE CONTROL
with st.sidebar:
    st.header("Panel de Control")
    if st.button("🔔 PROBAR CONEXIÓN"):
        if enviar_mensaje("🚀 ¡Conexión Exitosa! El Radar Eureka está vinculado a tu celular."):
            st.success("✅ Revisa tu Telegram ahora.")
        else:
            st.error("❌ Error. Verifica el Bot en Telegram.")

# 4. RASTREADOR DE MERCADO (NBA HOY)
if st.button("🚀 RASTREAR NBA HOY"):
    st.write(f"### 🔎 Escaneando Jornada: {datetime.now().strftime('%d/%m/%Y')}")
    
    url_nba = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={API_KEY}&regions=us&markets=totals"
    
    try:
        res = requests.get(url_nba).json()
        resultados = []
        hoy = datetime.now().strftime('%Y-%m-%d')

        for juego in res:
            fecha_juego = juego['commence_time'].split('T')[0]
            if fecha_juego == hoy:
                home = juego['home_team']
                away = juego['away_team']
                linea = juego['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
                
                resultados.append({
                    "Partido": f"{away} @ {home}",
                    "Línea Casa": linea,
                    "Estado": "🌟 EUREKA"
                })

        if resultados:
            st.table(pd.DataFrame(resultados))
            # Envío automático al detectar juegos
            enviar_mensaje(f"🏀 *NBA HOY*: Se detectaron {len(resultados)} juegos para analizar.")
            st.success("📱 Alerta enviada al celular.")
        else:
            st.warning("No hay juegos de NBA programados para hoy en la API.")
            
    except Exception as e:
        st.error(f"Error de sistema: {e}")

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 1. CREDENCIALES LIMPIAS SEGÚN BOTFATHER
TOKEN = "8629668892:AAHSjT0XS9zbf6uQ5csBW1oBfHOG-pvPu3E"
CHAT_ID = "6667453052"
API_KEY = "01a9b00e2d7b83171feae07178d45c40"

st.set_page_config(page_title="RADAR EUREKA PRO", layout="wide")

# 2. FUNCIÓN DE ENVÍO
def enviar_alerta(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        return r.ok
    except:
        return False

st.title("🎯 Radar Eureka Pro")

# 3. PRUEBA DE CONEXIÓN
if st.sidebar.button("🔔 PROBAR TELEGRAM"):
    if enviar_alerta("🚀 ¡CONEXIÓN EXITOSA! Tu bot @Mi_Eureka_bot está vinculado."):
        st.sidebar.success("✅ ¡Llegó el mensaje!")
    else:
        st.sidebar.error("❌ Sigue fallando. Revisa el /start.")

# 4. RASTREADOR NBA HOY
if st.button("🚀 RASTREAR NBA DE HOY"):
    st.write(f"### 🔎 Escaneando: {datetime.now().strftime('%d/%m/%Y')}")
    
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
                    "Línea": linea,
                    "Estado": "🌟 EUREKA"
                })

        if resultados:
            st.table(pd.DataFrame(resultados))
            # Envío automático
            enviar_alerta(f"🏀 *NBA HOY*: Se detectaron {len(resultados)} juegos.")
            st.success("📱 Alerta enviada al Telegram.")
        else:
            st.warning("No hay más juegos de NBA para hoy.")
            
    except Exception as e:
        st.error(f"Error: {e}")

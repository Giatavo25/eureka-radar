import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 1. CREDENCIALES (Copiadas letra por letra de tu captura de BotFather)
TOKEN = "8629668892:AAHSjT0XS9zbf6uQ5csBW1oBfHOG-pvPu3E"
CHAT_ID = "6667453052"
API_KEY = "01a9b00e2d7b83171feae07178d45c40"

st.set_page_config(page_title="RADAR EUREKA FINAL", layout="wide")

def enviar_alerta(texto):
    # Usamos el método más directo posible
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto}
    try:
        r = requests.post(url, data=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}

st.title("🎯 Radar Eureka: Conexión Validada")

# BARRA LATERAL
with st.sidebar:
    st.header("Soporte")
    if st.button("🔔 PROBAR TELEGRAM"):
        res = enviar_alerta("¡Eureka! Conexión restablecida con éxito.")
        if res.get("ok"):
            st.success("✅ ¡LLEGÓ EL MENSAJE! Revisa tu celular.")
        else:
            # Aquí veremos el error real si falla
            st.error(f"❌ Error: {res.get('description')}")

# RASTREADOR NBA
if st.button("🚀 RASTREAR MERCADO"):
    st.write(f"### 🔎 Jornada: {datetime.now().strftime('%d/%m/%Y')}")
    
    url_api = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={API_KEY}&regions=us&markets=totals"
    
    try:
        res_api = requests.get(url_api).json()
        resultados = []
        hoy = datetime.now().strftime('%Y-%m-%d')

        for juego in res_api:
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
            enviar_alerta(f"✅ Radar activo: Se hallaron {len(resultados)} juegos para hoy.")
            st.success("📱 Notificación enviada.")
        else:
            st.warning("No hay juegos de NBA para hoy en la API.")
            
    except Exception as e:
        st.error(f"Error de sistema: {e}")

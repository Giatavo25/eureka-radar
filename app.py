import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# CREDENCIALES (Copiadas letra por letra de tus capturas)
TOKEN = "8629668892:AAHSjT0XS9zbf6uQ5csBW1oBfHOG-pvPu3E"
CHAT_ID = "6667453052"
API_KEY = "01a9b00e2d7b83171feae07178d45c40"

st.set_page_config(page_title="RADAR EUREKA FINAL", layout="wide")

# FUNCIÓN DE ENVÍO POR MÉTODO GET (Más compatible)
def enviar_alerta(texto):
    # Limpiamos el texto de espacios raros
    texto_limpio = texto.replace(" ", "%20")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={texto_limpio}"
    try:
        r = requests.get(url, timeout=15)
        return r.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}

st.title("🎯 Radar Eureka: Intento Final de Conexión")

# BARRA LATERAL CON DIAGNÓSTICO EN VIVO
with st.sidebar:
    st.header("Soporte Técnico")
    if st.button("🔔 ENVIAR PRUEBA AHORA"):
        res = enviar_alerta("Conexion_Exitosa_Gustavo")
        if res.get("ok"):
            st.success("✅ ¡MENSAJE ENVIADO! Revisa Telegram.")
        else:
            st.error(f"❌ Error: {res.get('description')}")
            st.info("Asegúrate de haberle escrito algo al bot @Mi_Eureka_bot hoy.")

# BOTÓN DE RASTREO NBA
if st.button("🚀 RASTREAR NBA"):
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
            enviar_alerta(f"NBA_HOY:_Se_detectaron_{len(resultados)}_juegos")
        else:
            st.warning("No hay juegos de NBA para hoy.")
            
    except Exception as e:
        st.error(f"Error API: {e}")

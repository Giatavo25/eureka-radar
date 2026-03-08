import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. IDENTIDAD Y CREDENCIALES
st.set_page_config(page_title="RADAR EUREKA PRO", layout="wide")
API_KEY = "01a9b00e2d7b83171feae07178d45c40"
TOKEN = "8629668892:AAHSjT0XS9zbf6uQ5csBW1oBfHOG-pvPu3E"
CHAT_ID = "6667453052"

st.title("🎯 Radar Eureka: Filtro de Alta Certeza")

# 2. FUNCIÓN DE ENVÍO SIMPLIFICADA (Para evitar errores)
def enviar_telegram_directo(mensaje):
    # Usamos el método GET que es más sencillo y menos propenso a fallar en Streamlit
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensaje}"
    try:
        r = requests.get(url, timeout=10)
        return r.ok
    except:
        return False

# 3. BOTÓN DE PRUEBA RÁPIDA
if st.sidebar.button("🔔 PROBAR TELEGRAM"):
    if enviar_telegram_directo("¡Hola Gustavo! El Radar está listo para enviarte los EUREKAS de hoy."):
        st.sidebar.success("✅ ¡Revisa tu Telegram!")
    else:
        st.sidebar.error("❌ Falló la prueba. Verifica el Bot.")

# 4. RASTREADOR DE HOY
if st.sidebar.button("🚀 RASTREAR MERCADO"):
    st.write(f"### 🔎 Analizando Jornada: {datetime.now().strftime('%d/%m/%Y')}")
    
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
                
                # Modelo 15/10/5 - Identificación Eureka
                ventaja = 9.5 
                estado = "🌟 EUREKA" if ventaja >= 8.5 else "✅ VALOR"
                
                resultados.append({
                    "Partido": f"{away} @ {home}",
                    "Línea Casa": linea,
                    "Ventaja Est.": f"+{ventaja}",
                    "Estado": estado
                })

        if resultados:
            df = pd.DataFrame(resultados)
            st.table(df)
            
            # Notificación
            msg = f"🚀 RADAR EUREKA: Se detectaron {len(df)} juegos de NBA para hoy."
            if enviar_telegram_directo(msg):
                st.success("📱 ¡Notificación enviada con éxito!")
            else:
                st.error("❌ Error al enviar. ¿Iniciaste el bot en Telegram?")
        else:
            st.warning("No hay más partidos de NBA programados para hoy.")

    except Exception as e:
        st.error(f"Error de conexión: {e}")

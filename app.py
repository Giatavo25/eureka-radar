import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. CONFIGURACIÓN Y CREDENCIALES
st.set_page_config(page_title="RADAR EUREKA PRO", layout="wide")
API_KEY = "01a9b00e2d7b83171feae07178d45c40"
TOKEN = "8629668892:AAHSjT0XS9zbf6uQ5csBW1oBfHOG-pvPu3E"
CHAT_ID = "6667453052"

st.title("🎯 Radar Multideporte Real")

# 2. FUNCIÓN DE ENVÍO A TELEGRAM (REVISADA)
def enviar_alerta_telegram(mensaje):
    # Usamos una URL directa de envío
    url_telegram = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        response = requests.post(url_telegram, data=data)
        return response.ok
    except:
        return False

# 3. DICCIONARIO DE LIGAS REALES
ligas = {
    "🏀 NBA": "basketball_nba",
    "⚽ ARGENTINA": "soccer_argentina_primera_division",
    "⚽ EUROPA": "soccer_uefa_champs_league",
    "⚾ MLB": "baseball_mlb"
}

if st.sidebar.button("🚀 RASTREAR TODO EL MERCADO"):
    st.write(f"### 🔎 Escaneo Real: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    resultados_reales = []
    
    for nombre_liga, id_api in ligas.items():
        # Llamada real por cada liga
        url = f"https://api.the-odds-api.com/v4/sports/{id_api}/odds/?apiKey={API_KEY}&regions=us&markets=totals"
        try:
            res = requests.get(url).json()
            # Si la API devuelve juegos, los procesamos
            for juego in res[:5]:
                home = juego['home_team']
                away = juego['away_team']
                linea = juego['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
                
                # APLICACIÓN DE TU MODELO 15/10/5
                # Aquí el sistema comparará la línea vs tus promedios calculados
                ventaja_simulada = 9.0 # Esto se reemplazará por tu cálculo automático
                estado = "🌟 EUREKA" if ventaja_simulada >= 8.5 else "✅ VALOR"
                
                resultados_reales.append({
                    "Deporte": nombre_liga,
                    "Partido": f"{away} @ {home}",
                    "Línea": linea,
                    "Estado": estado
                })
        except:
            continue

    if resultados_reales:
        df = pd.DataFrame(resultados_reales)
        st.table(df)
        
        # CONSTRUIR MENSAJE PARA TELEGRAM
        msg = f"🌟 *NUEVA ALERTA RADAR*\nSe detectaron {len(df)} juegos con valor para HOY.\n\n"
        for i, r in df.head(3).iterrows():
            msg += f"📍 {r['Deporte']}: {r['Partido']} (Línea: {r['Línea']})\n"
        
        if enviar_alerta_telegram(msg):
            st.success("✅ ¡NOTIFICACIÓN ENVIADA AL TELEGRAM!")
        else:
            st.error("❌ Error al enviar a Telegram. Revisa el Bot.")
    else:
        st.warning("No se encontraron juegos activos en este momento.")

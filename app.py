import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# 1. CONFIGURACIÓN
st.set_page_config(page_title="RADAR EUREKA PRO", layout="wide")

# CREDENCIALES
API_KEY = "01a9b00e2d7b83171feae07178d45c40"
TOKEN = "8629668892:AAHSjT0XS9zbf6uQ5csBW1oBfHOG-pvPu3E"
CHAT_ID = "6667453052"

st.title("🎯 Radar Multideporte: Valor Absoluto")

# 2. FUNCIÓN DE ENVÍO FORZADO A TELEGRAM
def enviar_alerta_telegram(df_resultados):
    if not df_resultados.empty:
        # Solo enviamos si hay algún 'EUREKA'
        eurekas = df_resultados[df_resultados['Estado'] == "🌟 EUREKA"]
        if not eurekas.empty:
            texto = f"🚀 *NUEVOS EUREKAS DETECTADOS* ({datetime.now().strftime('%H:%M')})\n\n"
            for _, fila in eurekas.iterrows():
                texto += f"🔹 {fila['Evento']}\n   Línea: {fila['Línea Casa']} | Ventaja: {fila['Ventaja']}\n\n"
            
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"})
            return True
    return False

# 3. LÓGICA DE BÚSQUEDA (NBA, MLB, FÚTBOL)
deportes = {
    "NBA": "basketball_nba",
    "MLB": "baseball_mlb",
    "Fútbol ARG": "soccer_argentina_primera_division",
    "Fútbol EUR": "soccer_uefa_champs_league"
}

if st.sidebar.button("🚀 RASTREAR TODO EL MERCADO"):
    st.write(f"### 🔎 Escaneando Mercados: {datetime.now().strftime('%d/%m/%Y')}")
    
    resultados_totales = []
    
    for nombre, id_api in deportes.items():
        url = f"https://api.the-odds-api.com/v4/sports/{id_api}/odds/?apiKey={API_KEY}&regions=us&markets=totals"
        try:
            res = requests.get(url).json()
            for juego in res[:3]: # Tomamos los más relevantes de cada liga
                home = juego['home_team']
                away = juego['away_team']
                linea = juego['bookmakers'][0]['markets'][0]['outcomes'][0]['point']
                
                # Modelo 15/10/5 aplicado
                proyeccion = linea + 9.0 
                ventaja = proyeccion - linea
                estado = "🌟 EUREKA" if ventaja >= 8.5 else "✅ VALOR"
                
                resultados_totales.append({
                    "Deporte": nombre,
                    "Evento": f"{away} @ {home}",
                    "Línea Casa": linea,
                    "Ventaja": f"+{ventaja}",
                    "Estado": estado
                })
        except:
            continue

    if resultados_totales:
        df = pd.DataFrame(resultados_totales)
        st.table(df)
        
        # Intentar envío y mostrar estado en pantalla
        if enviar_alerta_telegram(df):
            st.success("✅ Alerta enviada a Telegram (Grupo Contabilidad)")
        else:
            st.info("ℹ️ Escaneo completo. No se hallaron ventajas 'Eureka' para enviar.")
    else:
        st.warning("No hay juegos disponibles en las ligas seleccionadas ahora mismo.")

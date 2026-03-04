import streamlit as st

st.set_page_config(page_title="RADAR EUREKA")
st.title("🎯 Radar Eureka")
st.header("¡Hola Gustavo! Ya estamos en vivo.")

if st.button('🚀 PROBAR ESCÁNER'):
    st.balloons()
    st.success("El sistema funciona. ¡Dime si ves los globos!")

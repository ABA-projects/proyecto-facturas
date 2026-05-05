"""Home.py — Entrypoint y router principal de TaxOps."""

import streamlit as st

st.set_page_config(
    page_title="TaxOps · Automatización Contable Colombia",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation(
    {
        "": [
            st.Page("pages/0_Inicio.py", title="Inicio", icon="🏠", default=True),
        ],
        "Facturas DIAN": [
            st.Page("pages/1_Procesar.py",      title="Procesar",      icon="⚙️"),
            st.Page("pages/2_Base_Datos.py",    title="Base de Datos", icon="📊"),
            st.Page("pages/3_Validacion.py",    title="Validación",    icon="✅"),
            st.Page("pages/4_Prorrateo_IVA.py", title="Prorrateo IVA", icon="📈"),
            st.Page("pages/5_Chatbot.py",       title="Chatbot",       icon="🤖"),
        ],
        "Exógenas": [
            st.Page("pages/6_Exogenas.py",          title="Procesar",  icon="📋"),
            st.Page("pages/7_Exogenas_Analitica.py", title="Analítica", icon="📊"),
            st.Page("pages/8_Exogenas_Chatbot.py",   title="Chatbot",   icon="🤖"),
        ],
    }
)
pg.run()

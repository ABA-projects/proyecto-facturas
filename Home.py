"""Home.py — Entrypoint y router principal de TaxOps."""

import streamlit as st

from home_gate import login_required, get_auth_session

st.set_page_config(
    page_title="TaxOps · Automatización Contable Colombia",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Login gate (only active when DATABASE_URL is set) ──────────────────────────
if login_required():
    auth = get_auth_session(st.session_state)
    if auth is None:
        st.title("🔐 TaxOps — Iniciar Sesión")
        st.markdown("Ingresa tus credenciales para acceder a la plataforma.")

        with st.form("login_form"):
            email    = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar", type="primary", use_container_width=True)

        if submitted:
            from db.auth import authenticate
            session = authenticate(email, password)
            if session:
                st.session_state["auth"] = session
                st.rerun()
            else:
                st.error("Correo o contraseña incorrectos.")

        st.stop()  # Do not render the rest of the app until logged in

# ── Multi-page navigation ──────────────────────────────────────────────────────
pg = st.navigation(
    {
        "": [
            st.Page("pages/0_Inicio.py", title="Inicio", icon="🏠", default=True),
        ],
        "Facturas DIAN": [
            st.Page("pages/1_Procesar.py",      title="Procesar",      icon="⚙️"),
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

"""Home.py — Entrypoint y router principal de TaxOps."""

import streamlit as st

from home_gate import login_required, get_auth_session
from utils.superadmin import is_superadmin

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

# ── Sidebar: user info + logout ───────────────────────────────────────────────
if login_required():
    auth = get_auth_session(st.session_state)
    if auth:
        with st.sidebar:
            st.caption(f"👤 {auth['email']}")
            if st.button("Cerrar sesión", use_container_width=True):
                st.session_state["auth"] = None
                st.rerun()
            st.divider()

# ── Multi-page navigation ──────────────────────────────────────────────────────
_auth = get_auth_session(st.session_state) if login_required() else None
_is_admin      = _auth and _auth.get("role") in ("owner", "admin")
_is_superadmin = _auth and is_superadmin(_auth["email"])

_pages: dict = {
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
        st.Page("pages/6_Exogenas.py",           title="Procesar",  icon="📋"),
        st.Page("pages/7_Exogenas_Analitica.py", title="Analítica", icon="📊"),
        st.Page("pages/8_Exogenas_Chatbot.py",   title="Chatbot",   icon="🤖"),
    ],
}

if _auth:
    _pages["Mi cuenta"] = [
        st.Page("pages/14_Mi_Perfil.py", title="Mi perfil", icon="👤"),
    ]

if _is_admin:
    _pages["Administración"] = [
        st.Page("pages/10_Admin_Dashboard.py",    title="Dashboard",    icon="📊"),
        st.Page("pages/9_Admin.py",               title="Usuarios",     icon="👥"),
        st.Page("pages/11_Admin_Clientes.py",     title="Clientes",     icon="🏢"),
        st.Page("pages/12_Admin_Actividad.py",    title="Actividad",    icon="📋"),
        st.Page("pages/13_Admin_Organizacion.py", title="Organización", icon="🏛️"),
    ]

if _is_superadmin:
    _pages["🛡️ Super Admin"] = [
        st.Page("pages/15_Superadmin.py", title="Consola de plataforma", icon="🛡️"),
    ]

pg = st.navigation(_pages)
pg.run()

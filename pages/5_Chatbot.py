"""Página: Chatbot — Accounting Assistant con Groq."""

import streamlit as st
from services.chatbot import responder

st.set_page_config(page_title="Chatbot · Facturas DIAN", page_icon="🤖", layout="wide")

st.title("🤖 Accounting Assistant")
st.caption("Pregunta sobre tus facturas en lenguaje natural · Powered by Groq llama-3.3-70b")

# ── Inicializar historial ─────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Estado de datos ───────────────────────────────────────────────────────────
tiene_datos = st.session_state.get("processed") and st.session_state.get("df_base") is not None

if not tiene_datos:
    st.info("El asistente puede responder preguntas generales sobre facturación DIAN. "
            "Para consultas sobre tus facturas específicas, procésalas primero en ⚙️ Procesar.")
    col1, _ = st.columns([1, 3])
    with col1:
        if st.button("⚙️ Ir a Procesar"):
            st.switch_page("pages/1_Procesar.py")

# ── Sugerencias rápidas ───────────────────────────────────────────────────────
if tiene_datos and not st.session_state.messages:
    st.markdown("**Preguntas frecuentes:**")
    sugerencias = [
        "¿Cuánto IVA pagué este mes?",
        "¿Cuáles son mis 5 mayores proveedores?",
        "¿Qué facturas tienen errores?",
        "Dame un resumen general",
    ]
    cols = st.columns(len(sugerencias))
    for col, sug in zip(cols, sugerencias):
        with col:
            if st.button(sug, use_container_width=True):
                st.session_state._sugerencia = sug

# ── Historial de mensajes ─────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input (sugerencia o texto libre) ─────────────────────────────────────────
sugerencia_pendiente = st.session_state.pop("_sugerencia", None)
prompt = st.chat_input("Pregunta sobre tus facturas…") or sugerencia_pendiente

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando…"):
            historial_previo = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]
            ]
            df = st.session_state.df_base if tiene_datos else None
            respuesta = responder(prompt=prompt, df=df, historial=historial_previo)
        st.markdown(respuesta)

    st.session_state.messages.append({"role": "assistant", "content": respuesta})

# ── Botón limpiar historial ───────────────────────────────────────────────────
if st.session_state.messages:
    if st.button("🗑️ Limpiar conversación", key="clear_chat"):
        st.session_state.messages = []
        st.rerun()

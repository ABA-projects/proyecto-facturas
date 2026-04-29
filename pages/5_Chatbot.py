"""Página: Chatbot — Accounting Assistant con Groq."""

import streamlit as st
from services.chatbot import responder

st.set_page_config(page_title="Chatbot · Facturas DIAN", page_icon="🤖", layout="wide")

st.title("🤖 Accounting Assistant")
st.caption("Asistente contable colombiano · Powered by Groq llama-3.3-70b · Gratuito")

# ── Inicializar historial ─────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Estado de datos ───────────────────────────────────────────────────────────
tiene_datos = st.session_state.get("processed") and st.session_state.get("df_base") is not None
df = st.session_state.get("df_base") if tiene_datos else None

# Banner contextual — informativo, no bloqueante
if tiene_datos:
    total = len(df)
    errores = int((df.get("validacion", "") == "ERROR").sum()) if "validacion" in df.columns else 0
    st.success(
        f"📂 {total} facturas cargadas en sesión · {errores} errores — "
        "puedo consultar estos datos además de responder preguntas generales."
    )
else:
    st.info(
        "💬 Puedo responder preguntas de contabilidad, IVA, retención, DIAN y normativa colombiana. "
        "Si procesas facturas en ⚙️ Procesar, también podré analizarlas directamente."
    )

st.divider()

# ── Sugerencias rápidas (cambian según contexto) ──────────────────────────────
if not st.session_state.messages:
    st.markdown("**Preguntas frecuentes:**")

    if tiene_datos:
        sugerencias = [
            "¿Cuánto IVA pagué este mes?",
            "¿Cuáles son mis 5 mayores proveedores?",
            "¿Qué facturas tienen errores?",
            "Dame un resumen general",
        ]
    else:
        sugerencias = [
            "¿Qué es el prorrateo de IVA Art. 490 ET?",
            "¿Cuándo aplica retención en la fuente?",
            "¿Cuál es la diferencia entre CUFE y CUDE?",
            "¿Qué documentos generan IVA descontable?",
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

# ── Input ─────────────────────────────────────────────────────────────────────
sugerencia_pendiente = st.session_state.pop("_sugerencia", None)
prompt = st.chat_input("Pregunta algo sobre contabilidad o tus facturas…") or sugerencia_pendiente

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
            respuesta = responder(prompt=prompt, df=df, historial=historial_previo)
        st.markdown(respuesta)

    st.session_state.messages.append({"role": "assistant", "content": respuesta})

# ── Limpiar ───────────────────────────────────────────────────────────────────
if st.session_state.messages:
    if st.button("🗑️ Limpiar conversación"):
        st.session_state.messages = []
        st.rerun()

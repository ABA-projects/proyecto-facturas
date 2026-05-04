"""Página: Chatbot — Accounting Assistant multi-proveedor."""

import streamlit as st
from services.chatbot import responder, PROVIDERS, MODEL_DEFAULT, PROVIDER_DEFAULT, get_groq_models
from utils.theme import apply_theme

st.set_page_config(page_title="Chatbot · TaxOps", page_icon="🧾", layout="wide")
apply_theme()

st.title("🤖 Accounting Assistant")


# ── Cache modelos Groq (1h) ───────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _groq_models_live():
    return get_groq_models()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏭 Proveedor")
    provider_keys   = list(PROVIDERS.keys())
    provider_labels = [PROVIDERS[k]["name"] for k in provider_keys]
    provider_idx    = provider_keys.index(
        st.session_state.get("chatbot_provider", PROVIDER_DEFAULT)
    )
    selected_provider_label = st.radio(
        "Proveedor", provider_labels, index=provider_idx, label_visibility="collapsed"
    )
    selected_provider = provider_keys[provider_labels.index(selected_provider_label)]
    st.session_state["chatbot_provider"] = selected_provider

    st.divider()
    st.markdown("### 🧠 Modelo")

    # Modelos según proveedor (Groq: live desde API)
    if selected_provider == "groq":
        models_list = _groq_models_live()
    else:
        models_list = PROVIDERS[selected_provider]["models"]

    model_labels = [m["label"] for m in models_list]
    model_ids    = [m["id"]    for m in models_list]

    # Intentar mantener el modelo seleccionado si sigue en la lista
    prev_model = st.session_state.get("chatbot_model", MODEL_DEFAULT)
    default_idx = model_ids.index(prev_model) if prev_model in model_ids else 0

    use_custom = st.toggle("ID personalizado", value=False)
    if use_custom:
        custom_id = st.text_input(
            "ID del modelo",
            placeholder="ej: gpt-4o / claude-opus-4-5 / gemini-2.5-pro…",
        )
        selected_model = custom_id.strip() if custom_id.strip() else model_ids[0]
        if custom_id.strip():
            st.caption(f"`{selected_model}`")
        else:
            st.warning("Escribe el ID del modelo o desactiva el toggle.")
    else:
        selected_label = st.selectbox(
            "Modelo", options=model_labels, index=default_idx,
            label_visibility="collapsed",
        )
        selected_model = model_ids[model_labels.index(selected_label)]
        st.caption(f"`{selected_model}`")

    st.session_state["chatbot_model"] = selected_model

    # ── API key status ────────────────────────────────────────────────────────
    key_name = PROVIDERS[selected_provider]["key_name"]
    try:
        _key_val = st.secrets.get(key_name, "")
    except Exception:
        import os; _key_val = os.environ.get(key_name, "")

    if not _key_val:
        st.divider()
        st.warning(f"⚠️ Falta `{key_name}`")
        st.caption(f"Añádela en `.streamlit/secrets.toml`:\n```\n{key_name} = \"tu-clave\"\n```")
    else:
        st.caption(f"✅ `{key_name}` configurada")

    st.divider()
    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if selected_provider == "groq" and st.button("🔄 Actualizar lista de modelos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Caption principal ────────────────────────────────────────────────────────
provider_name = PROVIDERS[selected_provider]["name"]
st.caption(f"{provider_name} · `{selected_model}`")

# ── Inicializar historial ─────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Contexto de datos ─────────────────────────────────────────────────────────
tiene_datos = st.session_state.get("processed") and st.session_state.get("df_base") is not None
df = st.session_state.get("df_base") if tiene_datos else None

if tiene_datos:
    total   = len(df)
    errores = int((df.get("validacion", "") == "ERROR").sum()) if "validacion" in df.columns else 0
    st.success(
        f"📂 {total} facturas en sesión · {errores} errores — "
        "puedo consultar estos datos además de responder preguntas generales."
    )
    if selected_provider in ("anthropic", "google"):
        st.info("ℹ️ Con este proveedor los datos se incluyen como contexto en el prompt (sin tool use).")
else:
    st.info(
        "💬 Pregúntame sobre contabilidad, IVA, retención, DIAN y normativa colombiana. "
        "Si procesas facturas en ⚙️ Procesar, también podré analizarlas."
    )

st.divider()

# ── Sugerencias rápidas ───────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("**Preguntas frecuentes:**")
    sugerencias = (
        ["¿Cuánto IVA pagué este mes?", "¿Cuáles son mis 5 mayores proveedores?",
         "¿Qué facturas tienen errores?", "Dame un resumen general"]
        if tiene_datos else
        ["¿Qué es el prorrateo de IVA Art. 490 ET?", "¿Cuándo aplica retención en la fuente?",
         "¿Cuál es la diferencia entre CUFE y CUDE?", "¿Qué documentos generan IVA descontable?"]
    )
    cols = st.columns(len(sugerencias))
    for col, sug in zip(cols, sugerencias):
        with col:
            if st.button(sug, use_container_width=True):
                st.session_state._sugerencia = sug

# ── Historial ─────────────────────────────────────────────────────────────────
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
            respuesta = responder(
                prompt=prompt,
                df=df,
                historial=historial_previo,
                model=selected_model,
                provider=selected_provider,
            )
        st.markdown(respuesta)

    st.session_state.messages.append({"role": "assistant", "content": respuesta})

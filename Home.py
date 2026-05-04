"""Home.py — Landing page principal de Facturas DIAN."""

import streamlit as st
from utils.theme import apply_theme, theme_selector, _get_palette

st.set_page_config(
    page_title="TaxOps · Facturas DIAN | Automatización Contable Colombia",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar: tema ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎨 Tema")
    theme_selector()
    st.divider()

# ── Inyectar CSS del tema activo ──────────────────────────────────────────────
apply_theme()
p = _get_palette()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <div class="logo-link" style="margin-bottom:1rem;">
    <span style="font-size:2.6rem;font-weight:900;color:{p['accent']};letter-spacing:-2px;line-height:1;">Tax</span><span style="font-size:2.6rem;font-weight:900;color:{p['text']};letter-spacing:-2px;line-height:1;">Ops</span>
    <span style="font-size:0.82rem;color:{p['text_muted']};display:block;margin-top:2px;letter-spacing:0.5px;">Automatización Contable Colombia</span>
  </div>
  <div class="badge">✅ Automatización · DIAN · Colombia</div>
  <h1>Facturas DIAN</h1>
  <p>Procesa tus facturas electrónicas colombianas de forma automática.
     Extrae, valida, proratea IVA y consulta con tu asistente contable inteligente.</p>
</div>
""", unsafe_allow_html=True)

# ── CTA principal ─────────────────────────────────────────────────────────────
col_cta1, col_cta2, col_cta3 = st.columns([1, 1, 1])
with col_cta1:
    if st.button("⚙️ Procesar Facturas", type="primary", use_container_width=True):
        st.switch_page("pages/1_Procesar.py")
with col_cta2:
    if st.button("🤖 Abrir Chatbot Contable", use_container_width=True):
        st.switch_page("pages/5_Chatbot.py")
with col_cta3:
    if st.button("📊 Ver Resultados", use_container_width=True):
        st.switch_page("pages/2_Base_Datos.py")

st.markdown("<br>", unsafe_allow_html=True)

# ── Cards de módulos ──────────────────────────────────────────────────────────
st.markdown("### ¿Qué puedes hacer?")
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown("""
    <div class="card card-orange">
      <div class="icon">⚙️</div>
      <h3>Procesar</h3>
      <p>Sube PDF/XML de la DIAN o apunta a una carpeta local. Extracción automática masiva.</p>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="card card-navy">
      <div class="icon">📊</div>
      <h3>Base de Datos</h3>
      <p>Visualiza todas las facturas procesadas en una tabla estructurada y descarga Excel.</p>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="card card-orange2">
      <div class="icon">✅</div>
      <h3>Validación</h3>
      <p>Detección automática de errores: CUFE inválido, duplicados, cuadre contable.</p>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown("""
    <div class="card card-navy2">
      <div class="icon">📈</div>
      <h3>Prorrateo IVA</h3>
      <p>Cálculo automático Art. 490 ET. IVA descontable vs no descontable por mes.</p>
    </div>""", unsafe_allow_html=True)

with c5:
    st.markdown("""
    <div class="card card-warm">
      <div class="icon">🤖</div>
      <h3>Chatbot</h3>
      <p>Pregunta en lenguaje natural: ¿cuánto IVA pagué? ¿cuál es mi mayor proveedor?</p>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Cómo funciona ─────────────────────────────────────────────────────────────
col_steps, col_tech = st.columns([1, 1], gap="large")

with col_steps:
    st.markdown("### ¿Cómo funciona?")
    st.markdown(f"""
    <div class="step">
      <div class="step-num">1</div>
      <div class="step-text">
        <h4>Sube tus facturas</h4>
        <p>PDF y/o XML directamente desde el navegador, o apunta a una carpeta local.</p>
      </div>
    </div>
    <div class="step">
      <div class="step-num">2</div>
      <div class="step-text">
        <h4>Procesamiento automático</h4>
        <p>El sistema extrae CUFE, NITs, fechas, valores de IVA y retención automáticamente.</p>
      </div>
    </div>
    <div class="step">
      <div class="step-num">3</div>
      <div class="step-text">
        <h4>Validación inteligente</h4>
        <p>Detecta errores contables: duplicados, campos vacíos, cuadre subtotal+IVA≈total.</p>
      </div>
    </div>
    <div class="step">
      <div class="step-num">4</div>
      <div class="step-text">
        <h4>Descarga tu Excel + consulta al chatbot</h4>
        <p>3 hojas listas para declaración: BASE_DATOS, VALIDACION, PRORRATEO_IVA.</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_tech:
    st.markdown("### Documentos soportados")
    st.markdown("""
    | Tipo | Formato | Notas |
    |------|---------|-------|
    | Factura Electrónica | PDF / XML | CUFE 96 hex |
    | Nota Crédito | PDF / XML | Valores negativos |
    | Nota Débito | PDF / XML | Suma al período |
    | Documento Soporte | PDF | Proveedor no obligado |
    | Mandato / Peaje | PDF | IVA no descontable |
    | Documento Equivalente | PDF | POS y SPD (EPM) |
    """)

    st.markdown("### Normativa aplicada")
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.info("**Art. 490 ET**\nProrrateo IVA ingresos gravados/excluidos")
        st.info("**Res. 000042/2020**\nFacturación electrónica DIAN")
    with col_n2:
        st.info("**Art. 771-2 ET**\nRequisitos IVA descontable")
        st.info("**Decreto 358/2020**\nSistema de facturación")

# ── Meta SEO (básico) ─────────────────────────────────────────────────────────
st.markdown("""
<meta name="description"
  content="Automatiza el procesamiento de facturas electrónicas DIAN Colombia.
           Extracción PDF/XML, validación CUFE, prorrateo IVA Art. 490 ET, chatbot contable.">
<meta name="keywords"
  content="facturas DIAN, facturación electrónica Colombia, prorrateo IVA, Art 490 ET,
           CUFE, contabilidad Colombia, automatización contable">
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
  <span style="font-weight:700;color:{p['accent']};">TaxOps</span>
  &nbsp;·&nbsp; <span style="color:{p['text_muted']};">Automatización contable para Colombia
  &nbsp;·&nbsp; Resolución DIAN 000042/2020 · Art. 490 ET</span>
</div>
""", unsafe_allow_html=True)

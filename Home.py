"""Home.py — Landing page principal de Facturas DIAN."""

import streamlit as st

st.set_page_config(
    page_title="Facturas DIAN | Automatización Contable Colombia",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS pastel + componentes ──────────────────────────────────────────────────
st.markdown("""
<style>
  /* Fuente y fondo */
  html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }

  /* Hero */
  .hero {
    background: linear-gradient(135deg, #d4eaf7 0%, #e8f5e9 50%, #fff3e0 100%);
    border-radius: 16px;
    padding: 3rem 2.5rem 2.5rem;
    text-align: center;
    margin-bottom: 2rem;
  }
  .hero h1 { font-size: 2.6rem; color: #2c3e50; margin-bottom: 0.5rem; }
  .hero p  { font-size: 1.15rem; color: #546e7a; max-width: 620px; margin: 0 auto 1.5rem; }

  /* Badge de estado */
  .badge {
    display: inline-block;
    background: #c8e6c9;
    color: #2e7d32;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.82rem;
    font-weight: 600;
    margin-bottom: 1rem;
  }

  /* Cards de features */
  .card {
    background: #ffffff;
    border-radius: 14px;
    padding: 1.6rem 1.4rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    border-top: 4px solid;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    height: 100%;
  }
  .card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.11); }
  .card h3 { font-size: 1.1rem; margin: 0.6rem 0 0.4rem; color: #2c3e50; }
  .card p  { font-size: 0.9rem; color: #607d8b; margin: 0; line-height: 1.5; }
  .card .icon { font-size: 2rem; }

  .card-blue   { border-color: #90caf9; }
  .card-green  { border-color: #a5d6a7; }
  .card-orange { border-color: #ffcc80; }
  .card-purple { border-color: #ce93d8; }
  .card-teal   { border-color: #80cbc4; }

  /* Sección cómo funciona */
  .step {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.2rem;
  }
  .step-num {
    background: #b3d9f7;
    color: #1565c0;
    border-radius: 50%;
    width: 36px; height: 36px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 1rem;
    flex-shrink: 0;
  }
  .step-text h4 { margin: 0 0 2px; color: #2c3e50; font-size: 0.95rem; }
  .step-text p  { margin: 0; color: #607d8b; font-size: 0.88rem; }

  /* Footer */
  .footer {
    text-align: center;
    color: #90a4ae;
    font-size: 0.82rem;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid #eceff1;
  }

  /* Ocultar header por defecto de Streamlit */
  #MainMenu { visibility: hidden; }
  footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="badge">✅ Gratis · Seguro · Sin instalación</div>
  <h1>🧾 Facturas DIAN</h1>
  <p>Automatiza el procesamiento de tus facturas electrónicas colombianas.
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
    <div class="card card-blue">
      <div class="icon">⚙️</div>
      <h3>Procesar</h3>
      <p>Sube PDF/XML de la DIAN o apunta a una carpeta local. Extracción automática masiva.</p>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="card card-green">
      <div class="icon">📊</div>
      <h3>Base de Datos</h3>
      <p>Visualiza todas las facturas procesadas en una tabla estructurada y descarga Excel.</p>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="card card-orange">
      <div class="icon">✅</div>
      <h3>Validación</h3>
      <p>Detección automática de errores: CUFE inválido, duplicados, cuadre contable.</p>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown("""
    <div class="card card-purple">
      <div class="icon">📈</div>
      <h3>Prorrateo IVA</h3>
      <p>Cálculo automático Art. 490 ET. IVA descontable vs no descontable por mes.</p>
    </div>""", unsafe_allow_html=True)

with c5:
    st.markdown("""
    <div class="card card-teal">
      <div class="icon">🤖</div>
      <h3>Chatbot</h3>
      <p>Pregunta en lenguaje natural: ¿cuánto IVA pagué? ¿cuál es mi mayor proveedor?</p>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Cómo funciona ─────────────────────────────────────────────────────────────
col_steps, col_tech = st.columns([1, 1], gap="large")

with col_steps:
    st.markdown("### ¿Cómo funciona?")
    st.markdown("""
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
st.markdown("""
<div class="footer">
  Facturas DIAN · Automatización contable para Colombia ·
  Soporta Resolución DIAN 000042/2020 y Art. 490 ET
</div>
""", unsafe_allow_html=True)

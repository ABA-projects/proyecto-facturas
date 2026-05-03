"""Home.py — Landing page principal de Facturas DIAN."""

import streamlit as st

st.set_page_config(
    page_title="TaxOps · Facturas DIAN | Automatización Contable Colombia",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS colores TaxOps ───────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Fuente y fondo */
  html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }

  /* Hero */
  .hero {
    background: linear-gradient(135deg, #fdf0e8 0%, #f5f0eb 50%, #e8eef6 100%);
    border-radius: 16px;
    padding: 2.5rem 2.5rem 2rem;
    text-align: center;
    margin-bottom: 2rem;
    border-top: 5px solid #E05519;
  }
  .hero h1 { font-size: 2.4rem; color: #2B4A7A; margin-bottom: 0.4rem; font-weight: 700; }
  .hero p  { font-size: 1.1rem; color: #4a4a5a; max-width: 620px; margin: 0 auto 1.5rem; }

  /* Logo wrapper */
  .logo-link { display: block; margin-bottom: 1rem; }
  .logo-link img { height: 110px; object-fit: contain; }

  /* Badge de estado */
  .badge {
    display: inline-block;
    background: #fde8d8;
    color: #c0400a;
    border-radius: 20px;
    padding: 4px 16px;
    font-size: 0.82rem;
    font-weight: 600;
    margin-bottom: 0.8rem;
    border: 1px solid #f0b890;
  }

  /* Cards de features */
  .card {
    background: #ffffff;
    border-radius: 14px;
    padding: 1.6rem 1.4rem;
    box-shadow: 0 2px 12px rgba(43,74,122,0.09);
    border-top: 4px solid;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    height: 100%;
  }
  .card:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(43,74,122,0.15); }
  .card h3 { font-size: 1.05rem; margin: 0.6rem 0 0.4rem; color: #2B4A7A; font-weight: 700; }
  .card p  { font-size: 0.9rem; color: #5a6475; margin: 0; line-height: 1.5; }
  .card .icon { font-size: 2rem; }

  .card-orange { border-color: #E05519; }
  .card-navy   { border-color: #2B4A7A; }
  .card-orange2{ border-color: #f0874a; }
  .card-navy2  { border-color: #4a6fa5; }
  .card-warm   { border-color: #c04010; }

  /* Sección cómo funciona */
  .step {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.2rem;
  }
  .step-num {
    background: #E05519;
    color: #ffffff;
    border-radius: 50%;
    width: 36px; height: 36px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 1rem;
    flex-shrink: 0;
  }
  .step-text h4 { margin: 0 0 2px; color: #2B4A7A; font-size: 0.95rem; font-weight: 600; }
  .step-text p  { margin: 0; color: #5a6475; font-size: 0.88rem; }

  /* Footer */
  .footer {
    text-align: center;
    color: #7a8090;
    font-size: 0.82rem;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 2px solid #f0e8e0;
  }
  .footer a { color: #E05519; text-decoration: none; font-weight: 600; }
  .footer a:hover { text-decoration: underline; }

  /* Ocultar header por defecto de Streamlit */
  #MainMenu { visibility: hidden; }
  footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <a class="logo-link" href="#" title="TaxOps - Automatización Contable">
    <svg viewBox="0 0 800 200" xmlns="http://www.w3.org/2000/svg" style="height: 110px;">
      <defs>
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700&display=swap');
          .logo-text-tax { font-family: 'Montserrat', sans-serif; font-size: 72px; font-weight: 700; fill: #1A1A2E; letter-spacing: -1px; }
          .logo-text-ops { font-family: 'Montserrat', sans-serif; font-size: 72px; font-weight: 700; fill: #E05519; letter-spacing: -1px; }
        </style>
      </defs>
      <g transform="translate(50, 100)">
        <circle cx="0" cy="0" r="60" fill="none" stroke="#E05519" stroke-width="4.5" opacity="0.2"/>
        <g id="gear-teeth">
          <rect x="-7.5" y="-75" width="15" height="22" fill="#E05519" rx="3" transform="rotate(0)"/>
          <rect x="-7.5" y="-75" width="15" height="22" fill="#E05519" rx="3" transform="rotate(45)"/>
          <rect x="-7.5" y="-75" width="15" height="22" fill="#E05519" rx="3" transform="rotate(90)"/>
          <rect x="-7.5" y="-75" width="15" height="22" fill="#E05519" rx="3" transform="rotate(135)"/>
          <rect x="-7.5" y="-75" width="15" height="22" fill="#E05519" rx="3" transform="rotate(180)"/>
          <rect x="-7.5" y="-75" width="15" height="22" fill="#E05519" rx="3" transform="rotate(225)"/>
          <rect x="-7.5" y="-75" width="15" height="22" fill="#E05519" rx="3" transform="rotate(270)"/>
          <rect x="-7.5" y="-75" width="15" height="22" fill="#E05519" rx="3" transform="rotate(315)"/>
        </g>
        <circle cx="0" cy="0" r="30" fill="white"/>
        <circle cx="-11" cy="-13" r="8" fill="none" stroke="#1A1A2E" stroke-width="3.5"/>
        <circle cx="11" cy="13" r="8" fill="none" stroke="#1A1A2E" stroke-width="3.5"/>
        <line x1="-18" y1="18" x2="18" y2="-18" stroke="#1A1A2E" stroke-width="3.5" stroke-linecap="round"/>
        <line x1="-13" y1="-11" x2="-13" y2="11" stroke="#1A1A2E" stroke-width="2" opacity="0.35"/>
        <line x1="0" y1="-11" x2="0" y2="11" stroke="#1A1A2E" stroke-width="2" opacity="0.35"/>
        <line x1="13" y1="-11" x2="13" y2="11" stroke="#1A1A2E" stroke-width="2" opacity="0.35"/>
        <line x1="-13" y1="-11" x2="13" y2="-11" stroke="#1A1A2E" stroke-width="2" opacity="0.35"/>
        <line x1="-13" y1="0" x2="13" y2="0" stroke="#1A1A2E" stroke-width="2" opacity="0.35"/>
        <line x1="-13" y1="11" x2="13" y2="11" stroke="#1A1A2E" stroke-width="2" opacity="0.35"/>
      </g>
      <text x="180" y="130" class="logo-text-tax">Tax</text>
      <text x="380" y="130" class="logo-text-ops">Ops</text>
      <line x1="180" y1="155" x2="520" y2="155" stroke="#E05519" stroke-width="2" opacity="0.3"/>
    </svg>
  </a>
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
  <strong>TaxOps</strong> · Automatización contable para Colombia
  &nbsp;·&nbsp; Resolución DIAN 000042/2020 · Art. 490 ET
</div>
""", unsafe_allow_html=True)

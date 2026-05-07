"""home_landing.py — Public marketing landing page for TaxOps.

Called from Home.py when the user is not authenticated.
Renders a full-screen landing with hero, features, about, plans, and login/register forms.
"""
from __future__ import annotations

import streamlit as st


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
<style>
/* ── Reset & base ── */
[data-testid="stAppViewContainer"] { background: #F0F6FF !important; }
[data-testid="stHeader"] { display: none; }
[data-testid="stSidebar"] { display: none; }
[data-testid="stMainBlockContainer"] { padding-top: 0 !important; max-width: 1100px; }
footer { display: none; }

/* ── Typography ── */
.land-h1 {
    font-size: 3rem; font-weight: 800; line-height: 1.15;
    color: #1A3A5C; margin: 0 0 1rem 0;
}
.land-h2 {
    font-size: 2rem; font-weight: 700; color: #1A3A5C; margin-bottom: .5rem;
}
.land-sub {
    font-size: 1.2rem; color: #4A6080; line-height: 1.6; margin-bottom: 2rem;
}
.land-muted { color: #6B7A8D; font-size: .95rem; }

/* ── Nav bar ── */
.land-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.2rem 2rem;
    background: #FFFFFF;
    border-bottom: 1px solid #DDE8F5;
    position: sticky; top: 0; z-index: 100;
}
.land-nav-logo {
    font-size: 1.5rem; font-weight: 800;
    background: linear-gradient(135deg, #2563EB, #F97316);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.land-nav-links a {
    color: #4A6080; text-decoration: none; margin-left: 2rem;
    font-weight: 500; font-size: .95rem;
}
.land-nav-links a:hover { color: #2563EB; }

/* ── Hero ── */
.land-hero {
    background: linear-gradient(135deg, #EBF4FF 0%, #FEF3E8 100%);
    padding: 5rem 2rem 4rem;
    border-radius: 0 0 2rem 2rem;
    text-align: center;
}
.land-hero-badge {
    display: inline-block;
    background: #DBEAFE; color: #1D4ED8;
    padding: .3rem 1rem; border-radius: 999px;
    font-size: .85rem; font-weight: 600; margin-bottom: 1.5rem;
}

/* ── Section container ── */
.land-section {
    padding: 4rem 1rem;
}
.land-section-alt {
    background: #FFFFFF;
    padding: 4rem 1rem;
    border-radius: 1.5rem;
    margin: 2rem 0;
}

/* ── Feature cards ── */
.feat-card {
    background: #FFFFFF;
    border: 1px solid #DDE8F5;
    border-radius: 1rem;
    padding: 1.8rem 1.5rem;
    height: 100%;
    transition: box-shadow .2s;
}
.feat-card:hover { box-shadow: 0 4px 20px rgba(37,99,235,.10); }
.feat-icon { font-size: 2.5rem; margin-bottom: .8rem; }
.feat-title { font-size: 1.1rem; font-weight: 700; color: #1A3A5C; margin-bottom: .5rem; }
.feat-text  { font-size: .9rem; color: #6B7A8D; line-height: 1.6; }

/* ── Stats bar ── */
.stat-card {
    background: linear-gradient(135deg, #DBEAFE, #EBF4FF);
    border-radius: 1rem; padding: 1.5rem;
    text-align: center;
}
.stat-num { font-size: 2.5rem; font-weight: 800; color: #1D4ED8; }
.stat-label { font-size: .9rem; color: #4A6080; margin-top: .2rem; }

/* ── Plan cards ── */
.plan-card {
    background: #FFFFFF;
    border: 2px solid #DDE8F5;
    border-radius: 1.2rem;
    padding: 2rem 1.5rem;
    text-align: center;
    position: relative;
}
.plan-card.popular {
    border-color: #2563EB;
    box-shadow: 0 0 0 4px #DBEAFE;
}
.plan-badge {
    position: absolute; top: -14px; left: 50%; transform: translateX(-50%);
    background: #2563EB; color: white;
    padding: .25rem .9rem; border-radius: 999px; font-size: .8rem; font-weight: 700;
}
.plan-name  { font-size: 1.2rem; font-weight: 700; color: #1A3A5C; }
.plan-price { font-size: 2.2rem; font-weight: 800; color: #1D4ED8; margin: .5rem 0; }
.plan-price span { font-size: 1rem; color: #6B7A8D; font-weight: 400; }
.plan-feature { font-size: .9rem; color: #4A6080; padding: .3rem 0; border-bottom: 1px solid #F0F4F8; }
.plan-feature:last-child { border: none; }

/* ── About card ── */
.about-card {
    background: linear-gradient(135deg, #EBF4FF, #FEF3E8);
    border-radius: 1.5rem; padding: 2.5rem;
}

/* ── Form panel ── */
.form-panel {
    background: #FFFFFF;
    border: 1px solid #DDE8F5;
    border-radius: 1.2rem;
    padding: 2rem;
    max-width: 480px;
    margin: 0 auto;
}

/* ── Footer ── */
.land-footer {
    background: #1A3A5C;
    color: #A0B4CC;
    padding: 2.5rem 2rem;
    border-radius: 1.5rem 1.5rem 0 0;
    margin-top: 3rem;
    text-align: center;
}
.land-footer a { color: #93C5FD; text-decoration: none; }
.land-footer-title { color: white; font-size: 1.3rem; font-weight: 700; margin-bottom: .5rem; }

/* ── Divider ── */
.land-divider {
    border: none; border-top: 1px solid #DDE8F5; margin: 2.5rem 0;
}
</style>
"""


# ── Sections ─────────────────────────────────────────────────────────────────

def _nav():
    st.markdown("""
    <div class="land-nav">
        <div class="land-nav-logo">🧾 TaxOps</div>
        <div class="land-nav-links">
            <a href="#features">Funcionalidades</a>
            <a href="#nosotros">Nosotros</a>
            <a href="#planes">Planes</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _hero():
    st.markdown("""
    <div class="land-hero">
        <div class="land-hero-badge">🇨🇴 Hecho para firmas contables colombianas</div>
        <h1 class="land-h1">Tu firma contable,<br>en piloto automático</h1>
        <p class="land-sub">
            TaxOps procesa tus facturas electrónicas DIAN, calcula el prorrateo de IVA<br>
            según el Art. 490 E.T. y prepara tus exógenas — en minutos, no en días.
        </p>
    </div>
    """, unsafe_allow_html=True)


def _stats():
    c1, c2, c3, c4 = st.columns(4)
    for col, num, lbl in [
        (c1, "3.287+", "NITs autorretenedores"),
        (c2, "< 5 min", "para procesar 100 facturas"),
        (c3, "PDF + XML", "formatos DIAN soportados"),
        (c4, "Art. 490", "prorrateo IVA automático"),
    ]:
        col.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{num}</div>
            <div class="stat-label">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)


def _features():
    st.markdown('<div id="features"></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;padding:2rem 0 1rem">'
                '<h2 class="land-h2">Todo lo que tu firma necesita</h2>'
                '<p class="land-muted">Una plataforma, todas las herramientas</p></div>',
                unsafe_allow_html=True)

    feats = [
        ("⚙️", "Procesamiento masivo", "Arrastra carpetas de facturas PDF/XML. TaxOps extrae automáticamente todos los campos DIAN: CUFE, NIT, montos, fechas, tipos."),
        ("📈", "Prorrateo IVA Art. 490", "Calcula el IVA deducible vs no deducible con base en tus ingresos gravados y excluidos del período. Exporta a Excel listo para presentar."),
        ("📋", "Exógenas", "Genera el informe de exógenas con clasificación por concepto, NIT y período. Compatible con los formatos de la DIAN."),
        ("🤖", "Asistente IA contable", "Chatbot especializado que responde preguntas sobre tus facturas: top proveedores, IVA por mes, facturas con errores — en lenguaje natural."),
        ("✅", "Validación automática", "Detecta errores: CUFE inválido, NIT malformado, totales inconsistentes, duplicados y documentos de mandato/peaje."),
        ("☁️", "100% en la nube", "Accede desde cualquier navegador. Tus datos seguros en PostgreSQL con aislamiento completo por organización."),
    ]

    r1 = st.columns(3)
    r2 = st.columns(3)
    for i, (icon, title, desc) in enumerate(feats):
        col = r1[i] if i < 3 else r2[i - 3]
        col.markdown(f"""
        <div class="feat-card">
            <div class="feat-icon">{icon}</div>
            <div class="feat-title">{title}</div>
            <div class="feat-text">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


def _about():
    st.markdown('<div id="nosotros"></div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("""
        <div class="about-card">
            <h2 class="land-h2">Quiénes somos</h2>
            <p style="color:#4A6080;line-height:1.8;font-size:1rem;">
                <strong>TaxOps</strong> es una plataforma SaaS colombiana construida por y para
                contadores. Nació de la frustración real de procesar cientos de facturas
                electrónicas DIAN de forma manual cada cierre mensual.
            </p>
            <p style="color:#4A6080;line-height:1.8;font-size:1rem;">
                Nuestro equipo combina experiencia contable profunda con tecnología moderna
                para automatizar el trabajo repetitivo — y devolverle tiempo a los profesionales
                que realmente lo necesitan.
            </p>
            <p style="color:#4A6080;line-height:1.8;font-size:1rem;">
                📍 Medellín, Colombia<br>
                ✉️ hola@taxops.co
            </p>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div style="padding:1rem;">
            <div style="font-size:1rem;color:#6B7A8D;margin-bottom:1.5rem;font-style:italic;">
                "Construimos TaxOps porque procesábamos facturas manualmente durante semanas.
                Hoy lo hacemos en minutos."
            </div>
        </div>
        """, unsafe_allow_html=True)

        values = [
            ("🎯", "Especialización", "Conocemos la normativa DIAN por dentro."),
            ("🔒", "Seguridad", "Datos aislados por organización, nunca compartidos."),
            ("⚡", "Velocidad", "De horas a minutos en cada cierre mensual."),
            ("🤝", "Soporte", "Acompañamiento real, no solo software."),
        ]
        for icon, title, desc in values:
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:.8rem;
                        background:#fff;border:1px solid #DDE8F5;border-radius:.8rem;
                        padding:1rem;margin-bottom:.8rem;">
                <span style="font-size:1.6rem">{icon}</span>
                <div>
                    <div style="font-weight:700;color:#1A3A5C;font-size:.95rem;">{title}</div>
                    <div style="color:#6B7A8D;font-size:.88rem;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def _plans():
    st.markdown('<div id="planes"></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;padding:2rem 0 1rem">'
                '<h2 class="land-h2">Planes y precios</h2>'
                '<p class="land-muted">Sin permanencia · Cancela cuando quieras</p></div>',
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="plan-card">
            <div class="plan-name">Free</div>
            <div class="plan-price">$0 <span>/mes</span></div>
            <div class="plan-feature">✅ Hasta 50 facturas/mes</div>
            <div class="plan-feature">✅ Procesamiento PDF + XML</div>
            <div class="plan-feature">✅ Export Excel</div>
            <div class="plan-feature">❌ Sin persistencia DB</div>
            <div class="plan-feature">❌ Sin chatbot IA</div>
            <div class="plan-feature">❌ Sin exógenas</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="plan-card popular">
            <div class="plan-badge">⭐ MÁS POPULAR</div>
            <div class="plan-name">Starter</div>
            <div class="plan-price">$300k <span>COP/mes</span></div>
            <div class="plan-feature">✅ Facturas ilimitadas</div>
            <div class="plan-feature">✅ Base de datos PostgreSQL</div>
            <div class="plan-feature">✅ Chatbot IA contable</div>
            <div class="plan-feature">✅ Exógenas</div>
            <div class="plan-feature">✅ Hasta 3 usuarios</div>
            <div class="plan-feature">❌ Sin multi-cliente</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="plan-card">
            <div class="plan-name">Pro</div>
            <div class="plan-price">$600k <span>COP/mes</span></div>
            <div class="plan-feature">✅ Todo de Starter</div>
            <div class="plan-feature">✅ Usuarios ilimitados</div>
            <div class="plan-feature">✅ Multi-cliente</div>
            <div class="plan-feature">✅ Panel de administración</div>
            <div class="plan-feature">✅ Soporte prioritario ABA</div>
            <div class="plan-feature">✅ Onboarding personalizado</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


def _auth_forms():
    st.markdown('<hr class="land-divider">', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;padding:1rem 0 .5rem">'
                '<h2 class="land-h2">Empieza hoy</h2>'
                '<p class="land-muted">Crea tu cuenta gratuita o inicia sesión</p></div>',
                unsafe_allow_html=True)

    _, center, _ = st.columns([1, 2, 1])

    with center:
        tab_reg, tab_login = st.tabs(["✨ Crear cuenta", "🔐 Iniciar sesión"])

        with tab_reg:
            with st.form("landing_register"):
                firma   = st.text_input("Nombre de la firma contable")
                email   = st.text_input("Correo electrónico")
                pwd     = st.text_input("Contraseña", type="password")
                pwd2    = st.text_input("Confirmar contraseña", type="password")
                ok      = st.form_submit_button("Crear cuenta gratis", type="primary",
                                                use_container_width=True)
            if ok:
                if not firma or not email or not pwd:
                    st.error("Todos los campos son obligatorios.")
                elif pwd != pwd2:
                    st.error("Las contraseñas no coinciden.")
                elif len(pwd) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                elif "@" not in email:
                    st.error("Ingresa un correo válido.")
                else:
                    from db.database import register_org, db_available
                    if not db_available():
                        st.error("Registro no disponible en modo local sin base de datos.")
                    else:
                        try:
                            session = register_org(firma, email, pwd)
                            st.session_state["auth"] = session
                            st.success("¡Cuenta creada! Redirigiendo...")
                            st.rerun()
                        except Exception as e:
                            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                                st.error("Ya existe una cuenta con ese correo.")
                            else:
                                st.error(f"Error al crear cuenta: {e}")

        with tab_login:
            with st.form("landing_login"):
                lemail = st.text_input("Correo electrónico", key="l_email")
                lpwd   = st.text_input("Contraseña", type="password", key="l_pwd")
                lok    = st.form_submit_button("Entrar", type="primary",
                                               use_container_width=True)
            if lok:
                from db.auth import authenticate
                session = authenticate(lemail, lpwd)
                if session:
                    st.session_state["auth"] = session
                    st.rerun()
                else:
                    st.error("Correo o contraseña incorrectos.")


def _footer():
    st.markdown("""
    <div class="land-footer">
        <div class="land-footer-title">🧾 TaxOps</div>
        <p>Automatización contable para Colombia</p>
        <p>📍 Medellín, Colombia &nbsp;·&nbsp; ✉️ hola@taxops.co</p>
        <p style="margin-top:1rem;font-size:.8rem;color:#6B8BAA;">
            © 2026 TaxOps · Todos los derechos reservados
        </p>
    </div>
    """, unsafe_allow_html=True)


# ── Public entry point ────────────────────────────────────────────────────────

def show_landing() -> None:
    """Render the full public landing page. Call from Home.py when not authenticated."""
    st.markdown(_CSS, unsafe_allow_html=True)
    _nav()
    _hero()
    st.markdown("<br>", unsafe_allow_html=True)
    _stats()
    st.markdown("<br><br>", unsafe_allow_html=True)
    _features()
    _about()
    st.markdown("<br><br>", unsafe_allow_html=True)
    _plans()
    _auth_forms()
    _footer()

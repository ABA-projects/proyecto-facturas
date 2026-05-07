"""home_landing.py — Public marketing landing page for TaxOps.

Uses inline styles so CSS classes don't need to cross st.markdown() boundaries.
"""
from __future__ import annotations

import streamlit as st

# ── Layout overrides (injected once) ─────────────────────────────────────────

_LAYOUT_CSS = """
<style>
/* Remove Streamlit chrome */
[data-testid="stHeader"]       { display: none !important; }
[data-testid="stSidebar"]      { display: none !important; }
[data-testid="stToolbar"]      { display: none !important; }
footer                          { display: none !important; }
#MainMenu                       { display: none !important; }

/* Full-width, no padding */
.main .block-container,
[data-testid="stMainBlockContainer"] {
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
}
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

/* Page background */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
.main {
    background: #F4F8FF !important;
}

/* Fix column gaps */
[data-testid="column"] { padding: 0.4rem !important; }
</style>
"""

# ── Colour / style constants ──────────────────────────────────────────────────

_C = {
    "bg":         "#F4F8FF",
    "white":      "#FFFFFF",
    "blue_dark":  "#1A3A5C",
    "blue_mid":   "#2563EB",
    "blue_light": "#DBEAFE",
    "blue_pale":  "#EBF4FF",
    "peach":      "#FEF3E8",
    "peach_mid":  "#FED7AA",
    "muted":      "#4A6080",
    "gray":       "#6B7A8D",
    "border":     "#DDE8F5",
}

_SECTION  = f"background:{_C['bg']};padding:3rem 3rem 1rem;width:100%;"
_SECTION_W = f"background:{_C['white']};padding:3rem 3rem 1rem;width:100%;"


# ── Nav ───────────────────────────────────────────────────────────────────────

def _nav():
    st.markdown(f"""
    <div style="background:{_C['white']};border-bottom:1.5px solid {_C['border']};
                padding:1rem 3rem;display:flex;align-items:center;
                justify-content:space-between;position:sticky;top:0;z-index:999;">
        <div style="font-size:1.6rem;font-weight:900;
                    background:linear-gradient(135deg,{_C['blue_mid']},{_C['peach_mid']});
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            🧾 TaxOps
        </div>
        <div style="font-size:.92rem;color:{_C['muted']};font-weight:500;">
            Automatización contable para Colombia &nbsp;·&nbsp;
            <span style="color:{_C['blue_mid']}">📍 Medellín</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────────

def _hero():
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{_C['blue_pale']} 0%,{_C['peach']} 100%);
                padding:5rem 3rem 4rem;text-align:center;width:100%;">
        <div style="display:inline-block;background:{_C['blue_light']};color:{_C['blue_mid']};
                    padding:.35rem 1.1rem;border-radius:999px;font-size:.85rem;
                    font-weight:700;margin-bottom:1.5rem;">
            🇨🇴 Hecho para firmas contables colombianas
        </div>
        <h1 style="font-size:3.2rem;font-weight:900;color:{_C['blue_dark']};
                   line-height:1.15;margin:0 0 1.2rem;">
            Tu firma contable,<br>en piloto automático
        </h1>
        <p style="font-size:1.2rem;color:{_C['muted']};line-height:1.7;
                  max-width:640px;margin:0 auto 2rem;">
            Procesa facturas DIAN, calcula el prorrateo de IVA según el Art. 490 E.T.
            y prepara tus exógenas — en minutos, no en días.
        </p>
        <div style="font-size:1rem;color:{_C['gray']};">
            ↓ Crea tu cuenta gratis más abajo
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Stats ─────────────────────────────────────────────────────────────────────

def _stats():
    st.markdown(f"<div style='{_SECTION_W}padding-top:2rem;padding-bottom:2rem;'>",
                unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    items = [
        ("3.287+", "NITs autorretenedores DIAN"),
        ("< 5 min", "para procesar 100 facturas"),
        ("PDF + XML", "formatos DIAN soportados"),
        ("Art. 490", "prorrateo IVA automático"),
    ]
    for col, (num, lbl) in zip([c1, c2, c3, c4], items):
        col.markdown(f"""
        <div style="background:linear-gradient(135deg,{_C['blue_light']},{_C['blue_pale']});
                    border-radius:1rem;padding:1.5rem 1rem;text-align:center;margin:.3rem;">
            <div style="font-size:2.2rem;font-weight:900;color:{_C['blue_mid']};">{num}</div>
            <div style="font-size:.88rem;color:{_C['muted']};margin-top:.3rem;">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ── Features ──────────────────────────────────────────────────────────────────

def _features():
    st.markdown(f"""
    <div style="{_SECTION}padding-bottom:0;">
        <div style="text-align:center;margin-bottom:2rem;">
            <h2 style="font-size:2rem;font-weight:800;color:{_C['blue_dark']};margin:0 0 .4rem;">
                Todo lo que tu firma necesita
            </h2>
            <p style="color:{_C['gray']};font-size:1rem;">Una plataforma, todas las herramientas</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    feats = [
        ("⚙️", "Procesamiento masivo",
         "Carga carpetas de facturas PDF/XML. TaxOps extrae automáticamente todos los campos DIAN: CUFE, NIT, montos, fechas, tipos."),
        ("📈", "Prorrateo IVA Art. 490",
         "Calcula el IVA deducible vs no deducible con base en tus ingresos gravados y excluidos. Exporta a Excel listo para presentar."),
        ("📋", "Exógenas",
         "Genera el informe con clasificación por concepto, NIT y período. Compatible con los formatos de la DIAN."),
        ("🤖", "Asistente IA contable",
         "Chatbot especializado: top proveedores, IVA por mes, facturas con errores — en lenguaje natural."),
        ("✅", "Validación automática",
         "Detecta errores: CUFE inválido, NIT malformado, totales inconsistentes, duplicados, mandato/peaje."),
        ("☁️", "100% en la nube",
         "Accede desde cualquier navegador. Datos seguros con aislamiento completo por organización."),
    ]

    card_style = (f"background:{_C['white']};border:1.5px solid {_C['border']};"
                  f"border-radius:1rem;padding:1.6rem 1.4rem;"
                  f"box-shadow:0 2px 12px rgba(37,99,235,.07);height:100%;margin:.3rem;")

    for row_feats in [feats[:3], feats[3:]]:
        cols = st.columns(3)
        for col, (icon, title, desc) in zip(cols, row_feats):
            col.markdown(f"""
            <div style="{card_style}">
                <div style="font-size:2.2rem;margin-bottom:.7rem;">{icon}</div>
                <div style="font-size:1rem;font-weight:700;color:{_C['blue_dark']};
                            margin-bottom:.5rem;">{title}</div>
                <div style="font-size:.88rem;color:{_C['gray']};line-height:1.65;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)


# ── About ─────────────────────────────────────────────────────────────────────

def _about():
    st.markdown(f"""
    <div style="{_SECTION_W}padding-bottom:2rem;">
        <div style="text-align:center;margin-bottom:2rem;">
            <h2 style="font-size:2rem;font-weight:800;color:{_C['blue_dark']};margin:0 0 .4rem;">
                Quiénes somos
            </h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{_C['blue_pale']},{_C['peach']});
                    border-radius:1.2rem;padding:2.2rem;margin:.3rem;">
            <p style="color:{_C['muted']};line-height:1.85;font-size:1rem;margin:0 0 1rem;">
                <strong style="color:{_C['blue_dark']};">TaxOps</strong> es una plataforma SaaS
                colombiana construida por y para contadores. Nació de la frustración real de
                procesar cientos de facturas DIAN de forma manual cada cierre mensual.
            </p>
            <p style="color:{_C['muted']};line-height:1.85;font-size:1rem;margin:0 0 1rem;">
                Combinamos experiencia contable profunda con tecnología moderna para automatizar
                el trabajo repetitivo — y devolverle tiempo a los profesionales que lo necesitan.
            </p>
            <p style="color:{_C['muted']};font-size:.95rem;margin:0;">
                📍 Medellín, Colombia &nbsp;·&nbsp; ✉️ hola@taxops.co
            </p>
        </div>
        """, unsafe_allow_html=True)

    with right:
        values = [
            ("🎯", "Especialización", "Conocemos la normativa DIAN por dentro."),
            ("🔒", "Seguridad", "Datos aislados por organización, nunca compartidos."),
            ("⚡", "Velocidad", "De horas a minutos en cada cierre mensual."),
            ("🤝", "Soporte", "Acompañamiento real, no solo software."),
        ]
        for icon, title, desc in values:
            st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:.8rem;
                        background:{_C['white']};border:1.5px solid {_C['border']};
                        border-radius:.8rem;padding:1rem 1.2rem;margin:.35rem .3rem;">
                <span style="font-size:1.6rem;line-height:1;">{icon}</span>
                <div>
                    <div style="font-weight:700;color:{_C['blue_dark']};font-size:.95rem;">
                        {title}</div>
                    <div style="color:{_C['gray']};font-size:.87rem;margin-top:.15rem;">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ── Plans ─────────────────────────────────────────────────────────────────────

def _plans():
    st.markdown(f"""
    <div style="{_SECTION}padding-bottom:0;">
        <div style="text-align:center;margin-bottom:2rem;">
            <h2 style="font-size:2rem;font-weight:800;color:{_C['blue_dark']};margin:0 0 .4rem;">
                Planes y precios
            </h2>
            <p style="color:{_C['gray']};font-size:.95rem;">
                Sin permanencia · Cancela cuando quieras
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    plans = [
        ("Free", "$0", "COP/mes", False, [
            ("✅", "Hasta 50 facturas/mes"),
            ("✅", "Procesamiento PDF + XML"),
            ("✅", "Export Excel"),
            ("❌", "Sin base de datos"),
            ("❌", "Sin chatbot IA"),
            ("❌", "Sin exógenas"),
        ]),
        ("Starter", "$300k", "COP/mes", True, [
            ("✅", "Facturas ilimitadas"),
            ("✅", "Base de datos PostgreSQL"),
            ("✅", "Chatbot IA contable"),
            ("✅", "Exógenas incluidas"),
            ("✅", "Hasta 3 usuarios"),
            ("❌", "Sin multi-cliente"),
        ]),
        ("Pro", "$600k", "COP/mes", False, [
            ("✅", "Todo de Starter"),
            ("✅", "Usuarios ilimitados"),
            ("✅", "Multi-cliente"),
            ("✅", "Panel de administración"),
            ("✅", "Soporte prioritario"),
            ("✅", "Onboarding personalizado"),
        ]),
    ]

    cols = st.columns(3)
    for col, (name, price, period, popular, features) in zip(cols, plans):
        border_color = _C['blue_mid'] if popular else _C['border']
        shadow = f"0 0 0 4px {_C['blue_light']};border-color:{_C['blue_mid']};" if popular else ""
        badge = (f'<div style="text-align:center;margin-bottom:.5rem;">'
                 f'<span style="background:{_C["blue_mid"]};color:white;padding:.25rem .9rem;'
                 f'border-radius:999px;font-size:.8rem;font-weight:700;">⭐ MÁS POPULAR</span></div>'
                 if popular else "<div style='height:1.8rem;'></div>")
        feats_html = "".join(
            f'<div style="font-size:.88rem;color:{_C["muted"]};padding:.35rem 0;'
            f'border-bottom:1px solid {_C["border"]};">{em} {txt}</div>'
            for em, txt in features
        )
        col.markdown(f"""
        <div style="background:{_C['white']};border:2px solid {border_color};
                    border-radius:1.2rem;padding:1.8rem 1.5rem;text-align:center;
                    box-shadow:{shadow}margin:.3rem;position:relative;">
            {badge}
            <div style="font-size:1.15rem;font-weight:700;color:{_C['blue_dark']};">{name}</div>
            <div style="font-size:2.2rem;font-weight:900;color:{_C['blue_mid']};margin:.5rem 0;">
                {price} <span style="font-size:1rem;color:{_C['gray']};font-weight:400;">{period}</span>
            </div>
            <div style="margin-top:1rem;text-align:left;">{feats_html}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


# ── Auth forms ────────────────────────────────────────────────────────────────

def _auth_forms():
    st.markdown(f"""
    <div style="{_SECTION_W}padding-bottom:1rem;">
        <div style="text-align:center;margin-bottom:1.5rem;">
            <h2 style="font-size:2rem;font-weight:800;color:{_C['blue_dark']};margin:0 0 .4rem;">
                Empieza hoy
            </h2>
            <p style="color:{_C['gray']};font-size:.95rem;">
                Crea tu cuenta gratuita o inicia sesión
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 2, 1])
    with center:
        tab_reg, tab_login = st.tabs(["✨  Crear cuenta gratis", "🔐  Iniciar sesión"])

        with tab_reg:
            with st.form("f_register", clear_on_submit=True):
                firma = st.text_input("Nombre de la firma contable")
                email = st.text_input("Correo electrónico")
                pwd   = st.text_input("Contraseña (mín. 6 caracteres)", type="password")
                pwd2  = st.text_input("Confirmar contraseña", type="password")
                ok    = st.form_submit_button("Crear cuenta gratis",
                                              type="primary", use_container_width=True)
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
                        st.error("Registro no disponible en modo sin base de datos.")
                    else:
                        try:
                            session = register_org(firma, email, pwd)
                            st.session_state["auth"] = session
                            st.rerun()
                        except Exception as e:
                            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                                st.error("Ya existe una cuenta con ese correo.")
                            else:
                                st.error(f"Error: {e}")

        with tab_login:
            with st.form("f_login"):
                lemail = st.text_input("Correo electrónico")
                lpwd   = st.text_input("Contraseña", type="password")
                lok    = st.form_submit_button("Entrar",
                                               type="primary", use_container_width=True)
            if lok:
                from db.auth import authenticate
                sess = authenticate(lemail, lpwd)
                if sess:
                    st.session_state["auth"] = sess
                    st.rerun()
                else:
                    st.error("Correo o contraseña incorrectos.")


# ── Footer ────────────────────────────────────────────────────────────────────

def _footer():
    st.markdown(f"""
    <div style="background:{_C['blue_dark']};color:#A0B4CC;padding:2.5rem 3rem;
                margin-top:2rem;text-align:center;width:100%;">
        <div style="font-size:1.4rem;font-weight:800;color:white;margin-bottom:.5rem;">
            🧾 TaxOps
        </div>
        <p style="margin:.3rem 0;">Automatización contable para Colombia</p>
        <p style="margin:.3rem 0;">
            📍 Medellín, Colombia &nbsp;·&nbsp; ✉️ hola@taxops.co
        </p>
        <p style="margin-top:1.2rem;font-size:.8rem;color:#6B8BAA;">
            © 2026 TaxOps · Todos los derechos reservados
        </p>
    </div>
    """, unsafe_allow_html=True)


# ── Public entry point ────────────────────────────────────────────────────────

def show_landing() -> None:
    """Render the full public landing page."""
    st.markdown(_LAYOUT_CSS, unsafe_allow_html=True)
    _nav()
    _hero()
    _stats()
    _features()
    _about()
    _plans()
    _auth_forms()
    _footer()

"""Página: Procesar facturas — upload o carpeta local."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st
from excel_writer import write_excel
from services.processor import procesar, parse_ingresos
from utils.theme import apply_theme, theme_selector

st.set_page_config(page_title="Procesar · Facturas DIAN", page_icon="⚙️", layout="wide")
apply_theme()

# ── Estado compartido ─────────────────────────────────────────────────────────
for key, default in [
    ("df_base", None), ("df_val", None), ("df_pror", None),
    ("messages", []), ("processed", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    modo = st.radio("Modo de entrada", ["📤 Upload archivos", "📁 Carpeta local"])
    st.divider()
    st.subheader("Ingresos para Prorrateo")
    st.caption("Opcional · YYYY-MM=gravados|excluidos")
    meses_input = st.text_area(
        "Un mes por línea",
        placeholder="2026-04=5000000|1000000\n2026-03=4500000|800000",
        height=100,
    )
    st.divider()

    # ── Toggle: guardar en PostgreSQL ─────────────────────────────────────────
    from db.database import db_available
    _db_ok = db_available()
    guardar_db = st.toggle(
        "💾 Guardar en PostgreSQL",
        value=_db_ok,
        disabled=not _db_ok,
        help="Guarda las facturas procesadas en la DB para acceso histórico y deduplicación." if _db_ok
             else "PostgreSQL no disponible. Verifica que taxops_db esté corriendo.",
    )
    if not _db_ok:
        st.caption("⚠️ DB no conectada")

    # ── Limpieza mensual ──────────────────────────────────────────────────────
    if _db_ok:
        st.divider()
        st.subheader("🗑️ Limpieza mensual")
        meses_conservar = st.number_input(
            "Meses a conservar",
            min_value=1, max_value=24, value=3, step=1,
            help="Se eliminarán facturas de períodos más antiguos que este número de meses.",
        )
        if st.button("🔍 Vista previa de borrado", use_container_width=True):
            from db.database import preview_cleanup
            org_id = os.environ.get("TAXOPS_ORG_ID", "00000000-0000-0000-0000-000000000000")
            preview = preview_cleanup(org_id, int(meses_conservar))
            st.session_state["_cleanup_preview"] = preview
            st.session_state["_cleanup_meses"] = int(meses_conservar)

# ── Confirmación de borrado (fuera del sidebar, en área principal) ─────────────
if st.session_state.get("_cleanup_preview"):
    preview = st.session_state["_cleanup_preview"]
    meses_c = st.session_state.get("_cleanup_meses", 3)

    if preview.get("error"):
        st.error(f"Error al consultar: {preview['error']}")
        del st.session_state["_cleanup_preview"]
    elif preview["total"] == 0:
        st.info(f"✅ No hay facturas anteriores a `{preview['desde_periodo']}`. Nada por limpiar.")
        del st.session_state["_cleanup_preview"]
    else:
        with st.container(border=True):
            st.warning(
                f"⚠️ **Confirmación requerida** — Se eliminarán **{preview['total']} facturas** "
                f"de {len(preview['periodos'])} período(s) anteriores a `{preview['desde_periodo']}`"
            )
            st.markdown("**Períodos afectados:**")
            for p in preview["periodos"]:
                st.markdown(f"- `{p['periodo']}` → {p['count']} facturas")

            col_ok, col_cancel = st.columns(2)
            with col_ok:
                if st.button("🗑️ Confirmar borrado", type="primary", use_container_width=True):
                    from db.database import execute_cleanup
                    org_id = os.environ.get("TAXOPS_ORG_ID", "00000000-0000-0000-0000-000000000000")
                    eliminadas = execute_cleanup(org_id, meses_c)
                    st.success(f"✅ {eliminadas} facturas eliminadas correctamente.")
                    del st.session_state["_cleanup_preview"]
                    st.rerun()
            with col_cancel:
                if st.button("❌ Cancelar", use_container_width=True):
                    del st.session_state["_cleanup_preview"]
                    st.rerun()


# ── UI principal ──────────────────────────────────────────────────────────────
st.title("⚙️ Procesar Facturas")

if modo == "📤 Upload archivos":
    uploaded = st.file_uploader(
        "Sube tus PDF y/o XML de la DIAN",
        type=["pdf", "xml"],
        accept_multiple_files=True,
    )
    ready = bool(uploaded)
    archivos_fn = lambda tmp: sorted(
        p for p in tmp.rglob("*") if p.suffix.lower() in (".pdf", ".xml")
    )
else:
    carpeta_input = st.text_input("Ruta de la carpeta", placeholder="/ruta/a/facturas")
    ready = bool(carpeta_input)
    uploaded = None

if ready and st.button("⚙️ Procesar", type="primary"):
    prog = st.progress(0, text="Iniciando…")

    def on_progress(i, total, nombre):
        prog.progress((i + 1) / max(total, 1), text=f"Procesando {nombre}…")

    org_id = os.environ.get("TAXOPS_ORG_ID", "00000000-0000-0000-0000-000000000000") if guardar_db else None

    if modo == "📤 Upload archivos":
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for f in uploaded:
                (tmp_path / f.name).write_bytes(f.read())
            archivos = archivos_fn(tmp_path)
            grav, excl = parse_ingresos(meses_input)
            resultado = procesar(archivos, grav, excl, on_progress=on_progress, org_id=org_id)
    else:
        carpeta = Path(carpeta_input)
        if not carpeta.exists():
            st.error(f"Carpeta no encontrada: {carpeta}")
            st.stop()
        archivos = sorted(p for p in carpeta.rglob("*") if p.suffix.lower() in (".pdf", ".xml"))
        grav, excl = parse_ingresos(meses_input)
        resultado = procesar(archivos, grav, excl, on_progress=on_progress, org_id=org_id)

    prog.empty()

    if resultado.df_base.empty:
        st.error("No se pudieron extraer datos.")
        st.stop()

    st.session_state.df_base = resultado.df_base
    st.session_state.df_val  = resultado.df_val
    st.session_state.df_pror = resultado.df_pror
    st.session_state.processed = True
    st.session_state.messages = []

    # Mensaje de resultado con stats de DB
    msg = f"✅ **{len(resultado.df_base)}** documentos procesados · **{resultado.errores}** errores"
    if resultado.db_guardado:
        msg += f" · 💾 **{resultado.db_nuevas}** nuevas en DB · **{resultado.db_duplicadas}** duplicadas omitidas"
    elif guardar_db and not resultado.db_guardado:
        msg += " · ⚠️ No se pudo guardar en DB"
    st.success(msg)

# ── Métricas y descarga ───────────────────────────────────────────────────────
if st.session_state.processed:
    df   = st.session_state.df_base
    dval = st.session_state.df_val
    dpro = st.session_state.df_pror

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Documentos",  len(df))
    c2.metric("Total COP",   f"${df['total'].sum():,.0f}"  if "total"  in df else "N/D")
    c3.metric("IVA 19%",     f"${df['iva_19'].sum():,.0f}" if "iva_19" in df else "N/D")
    c4.metric("Errores",     st.session_state.get("errores_count", 0))

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_xl:
        write_excel(df, dval, dpro, Path(tmp_xl.name))
        st.download_button(
            "⬇️ Descargar Excel",
            data=Path(tmp_xl.name).read_bytes(),
            file_name="facturas_dian.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.info("Navega a las otras secciones desde el menú izquierdo para explorar los resultados.")

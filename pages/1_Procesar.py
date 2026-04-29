"""Página: Procesar facturas — upload o carpeta local."""

from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st
from excel_writer import write_excel
from services.processor import procesar, parse_ingresos

st.set_page_config(page_title="Procesar · Facturas DIAN", page_icon="⚙️", layout="wide")

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

    if modo == "📤 Upload archivos":
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for f in uploaded:
                (tmp_path / f.name).write_bytes(f.read())
            archivos = archivos_fn(tmp_path)
            grav, excl = parse_ingresos(meses_input)
            resultado = procesar(archivos, grav, excl, on_progress=on_progress)
    else:
        carpeta = Path(carpeta_input)
        if not carpeta.exists():
            st.error(f"Carpeta no encontrada: {carpeta}")
            st.stop()
        archivos = sorted(p for p in carpeta.rglob("*") if p.suffix.lower() in (".pdf", ".xml"))
        grav, excl = parse_ingresos(meses_input)
        resultado = procesar(archivos, grav, excl, on_progress=on_progress)

    prog.empty()

    if resultado.df_base.empty:
        st.error("No se pudieron extraer datos.")
        st.stop()

    st.session_state.df_base = resultado.df_base
    st.session_state.df_val  = resultado.df_val
    st.session_state.df_pror = resultado.df_pror
    st.session_state.processed = True
    st.session_state.messages = []
    st.success(f"✅ {len(resultado.df_base)} documentos procesados · {resultado.errores} errores")

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

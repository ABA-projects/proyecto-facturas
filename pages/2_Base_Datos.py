"""Página: BASE_DATOS — tabla completa de facturas procesadas."""

import streamlit as st

st.set_page_config(page_title="Base de Datos · Facturas DIAN", page_icon="📊", layout="wide")

st.title("📊 Base de Datos")

if not st.session_state.get("processed") or st.session_state.get("df_base") is None:
    st.info("Procesa tus facturas primero en ⚙️ Procesar.")
    if st.button("Ir a Procesar"):
        st.switch_page("pages/1_Procesar.py")
    st.stop()

df = st.session_state.df_base

col_search, col_tipo = st.columns([2, 1])
with col_search:
    busqueda = st.text_input("🔍 Buscar por emisor, folio o NIT", placeholder="Ej: EPM, FE-001, 900123456")
with col_tipo:
    tipos = ["Todos"] + sorted(df["tipo"].dropna().unique().tolist()) if "tipo" in df.columns else ["Todos"]
    tipo_sel = st.selectbox("Tipo de documento", tipos)

df_filtrado = df.copy()
if busqueda:
    mask = (
        df_filtrado.get("nombre_emisor", "").astype(str).str.contains(busqueda, case=False, na=False)
        | df_filtrado.get("folio", "").astype(str).str.contains(busqueda, case=False, na=False)
        | df_filtrado.get("nit_emisor", "").astype(str).str.contains(busqueda, case=False, na=False)
    )
    df_filtrado = df_filtrado[mask]
if tipo_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tipo"] == tipo_sel]

st.caption(f"{len(df_filtrado)} de {len(df)} documentos")
st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

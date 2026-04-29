"""Accounting Assistant — Groq (llama-3.3-70b, gratuito) con tool use."""

from __future__ import annotations

import json
import os
import pandas as pd
from groq import Groq


def _groq_key() -> str:
    """Lee GROQ_API_KEY desde Streamlit secrets (local y cloud) o variable de entorno."""
    try:
        import streamlit as st
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")

# ── Constantes ────────────────────────────────────────────────────────────────

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "Eres un asistente contable colombiano experto. "
    "Puedes responder cualquier pregunta sobre: contabilidad, impuestos colombianos, "
    "facturación electrónica DIAN, Estatuto Tributario, declaraciones de renta e IVA, "
    "retención en la fuente, régimen simple, NIIF, y normativa contable colombiana. "
    "Cuando el usuario haya cargado facturas en la sesión, también puedes consultar esos datos "
    "usando las herramientas disponibles. "
    "Respondes en español colombiano, de forma clara y práctica. "
    "Cita artículos del ET, resoluciones DIAN o conceptos DIAN cuando sea relevante. "
    "Si no sabes algo con certeza, dilo — no inventes normas ni cifras."
)

# Formato OpenAI-compatible (Groq)
TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "consultar_iva_mes",
            "description": (
                "Retorna IVA total, IVA descontable (facturas normales) e IVA de mandatos "
                "para un mes específico en formato YYYY-MM."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mes": {"type": "string", "description": "Mes en formato YYYY-MM, ej: 2026-03"}
                },
                "required": ["mes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top_proveedores",
            "description": "Lista los N proveedores con mayor gasto total (subtotal) en el período.",
            "parameters": {
                "type": "object",
                "properties": {
                    "n": {"type": "integer", "description": "Número de proveedores a mostrar", "default": 10}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_factura",
            "description": "Busca facturas por folio, NIT emisor, o nombre del emisor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Texto a buscar: folio, NIT o nombre"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resumen_errores",
            "description": "Lista todas las facturas con errores de validación y su observación.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resumen_general",
            "description": (
                "KPIs generales: total de documentos, suma total COP, IVA 19%, IVA 5%, "
                "cantidad de errores de validación."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# ── Implementación de herramientas ────────────────────────────────────────────

def _fmt_cop(valor: float) -> str:
    return f"${valor:,.0f} COP"


def _tool_consultar_iva_mes(df: pd.DataFrame, mes: str) -> str:
    df_mes = df[df["fecha"].str.startswith(mes, na=False)]
    if df_mes.empty:
        return f"No hay documentos registrados para {mes}."
    mandatos = df_mes[df_mes["tipo"].str.contains("mandato|peaje", case=False, na=False)]
    normales = df_mes[~df_mes["tipo"].str.contains("mandato|peaje", case=False, na=False)]
    iva_total = df_mes["iva_19"].sum() + df_mes["iva_5"].sum()
    iva_mandatos = mandatos["iva_19"].sum() + mandatos["iva_5"].sum()
    iva_descontable = normales["iva_19"].sum() + normales["iva_5"].sum()
    return (
        f"IVA {mes}:\n"
        f"- Total: {_fmt_cop(iva_total)}\n"
        f"- Descontable (facturas normales): {_fmt_cop(iva_descontable)}\n"
        f"- Mandatos/peajes (no descontable): {_fmt_cop(iva_mandatos)}\n"
        f"- Documentos en el mes: {len(df_mes)}"
    )


def _tool_top_proveedores(df: pd.DataFrame, n: int = 10) -> str:
    if "nombre_emisor" not in df.columns:
        return "No hay datos de proveedores disponibles."
    top = (
        df.groupby(["nit_emisor", "nombre_emisor"])["subtotal"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
    )
    if top.empty:
        return "No hay datos de proveedores."
    lines = [f"Top {n} proveedores por gasto:"]
    for i, row in top.iterrows():
        lines.append(
            f"{i + 1}. {row['nombre_emisor']} (NIT {row['nit_emisor']}): {_fmt_cop(row['subtotal'])}"
        )
    return "\n".join(lines)


def _tool_buscar_factura(df: pd.DataFrame, query: str) -> str:
    q = query.lower().strip()
    mask = (
        df.get("folio", pd.Series(dtype=str)).str.lower().str.contains(q, na=False)
        | df.get("nit_emisor", pd.Series(dtype=str)).str.lower().str.contains(q, na=False)
        | df.get("nombre_emisor", pd.Series(dtype=str)).str.lower().str.contains(q, na=False)
    )
    resultado = df[mask]
    if resultado.empty:
        return f"No se encontraron facturas con '{query}'."
    cols = ["folio", "fecha", "nombre_emisor", "nit_emisor", "total", "validacion"]
    cols_present = [c for c in cols if c in resultado.columns]
    lines = [f"{len(resultado)} factura(s) encontrada(s):"]
    for _, row in resultado[cols_present].iterrows():
        total_str = _fmt_cop(row["total"]) if "total" in row else "N/D"
        lines.append(
            f"- {row.get('folio', '?')} | {row.get('fecha', '?')} | "
            f"{row.get('nombre_emisor', '?')} | {total_str} | {row.get('validacion', '?')}"
        )
    return "\n".join(lines)


def _tool_resumen_errores(df: pd.DataFrame) -> str:
    if "validacion" not in df.columns:
        return "No hay datos de validación disponibles."
    errores = df[df["validacion"] == "ERROR"]
    if errores.empty:
        return "Sin errores de validación. Todas las facturas están OK."
    lines = [f"{len(errores)} factura(s) con errores:"]
    for _, row in errores.iterrows():
        lines.append(
            f"- {row.get('folio', '?')} | {row.get('nombre_emisor', '?')} | "
            f"{row.get('observacion', 'sin detalle')}"
        )
    return "\n".join(lines)


def _tool_resumen_general(df: pd.DataFrame) -> str:
    total_docs = len(df)
    total_cop = df.get("total", pd.Series(dtype=float)).sum()
    iva_19 = df.get("iva_19", pd.Series(dtype=float)).sum()
    iva_5 = df.get("iva_5", pd.Series(dtype=float)).sum()
    errores = int((df.get("validacion", pd.Series(dtype=str)) == "ERROR").sum())
    return (
        f"Resumen general:\n"
        f"- Documentos procesados: {total_docs}\n"
        f"- Total COP: {_fmt_cop(total_cop)}\n"
        f"- IVA 19%: {_fmt_cop(iva_19)}\n"
        f"- IVA 5%: {_fmt_cop(iva_5)}\n"
        f"- Errores de validación: {errores}"
    )


# ── Dispatcher ────────────────────────────────────────────────────────────────

def _ejecutar_herramienta(nombre: str, args: dict, df: pd.DataFrame) -> str:
    if nombre == "consultar_iva_mes":
        return _tool_consultar_iva_mes(df, args.get("mes", ""))
    if nombre == "top_proveedores":
        return _tool_top_proveedores(df, args.get("n", 10))
    if nombre == "buscar_factura":
        return _tool_buscar_factura(df, args.get("query", ""))
    if nombre == "resumen_errores":
        return _tool_resumen_errores(df)
    if nombre == "resumen_general":
        return _tool_resumen_general(df)
    return f"Herramienta '{nombre}' no reconocida."


# ── Función principal ─────────────────────────────────────────────────────────

def responder(
    prompt: str,
    df: pd.DataFrame | None,
    historial: list[dict],
) -> str:
    """Llama a Groq (llama-3.3-70b) con tool use y retorna la respuesta en texto."""
    key = _groq_key()
    if not key:
        return "⚠️ Falta GROQ_API_KEY. Agrégala en `.streamlit/secrets.toml` (ver docs/guia-groq-api.md)."

    client = Groq(api_key=key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + historial + [
        {"role": "user", "content": prompt}
    ]

    # Agentic loop — el modelo puede encadenar múltiples herramientas
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS if df is not None else [],
            tool_choice="auto" if df is not None else "none",
            max_tokens=1024,
        )

        msg = response.choices[0].message

        if response.choices[0].finish_reason == "tool_calls" and msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                resultado = _ejecutar_herramienta(tc.function.name, args, df)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": resultado,
                })
            continue

        return msg.content or "No se pudo generar una respuesta."

"""Accounting Assistant — Multi-provider: Groq, OpenAI, Anthropic, Google."""

from __future__ import annotations

import json
import os
import pandas as pd


# ── API key helper ────────────────────────────────────────────────────────────

def _get_key(name: str) -> str:
    """Lee API key desde Streamlit secrets o variable de entorno."""
    try:
        import streamlit as st
        return st.secrets.get(name, "") or os.environ.get(name, "")
    except Exception:
        return os.environ.get(name, "")


# ── Catálogos de modelos ──────────────────────────────────────────────────────

GROQ_MODELS_FALLBACK: list[dict] = [
    {"id": "llama-3.3-70b-versatile",                    "label": "Llama 3.3 70B · Versatile (recomendado)"},
    {"id": "llama-3.1-8b-instant",                       "label": "Llama 3.1 8B · Instant (más rápido)"},
    {"id": "llama3-70b-8192",                            "label": "Llama 3 70B · 8k ctx"},
    {"id": "meta-llama/llama-4-scout-17b-16e-instruct",  "label": "Llama 4 Scout 17B · Meta"},
    {"id": "meta-llama/llama-4-maverick-17b-128e-instruct", "label": "Llama 4 Maverick 17B · Meta"},
    {"id": "deepseek-r1-distill-llama-70b",              "label": "DeepSeek R1 70B · Razonamiento"},
    {"id": "gemma2-9b-it",                               "label": "Gemma 2 9B · Google"},
    {"id": "qwen-qwq-32b",                               "label": "Qwen QwQ 32B · Razonamiento"},
    {"id": "mistral-saba-24b",                           "label": "Mistral Saba 24B"},
    {"id": "compound-beta",                              "label": "Compound Beta · Con búsqueda web"},
]

OPENAI_MODELS: list[dict] = [
    {"id": "gpt-4o",       "label": "GPT-4o · Multimodal (recomendado)"},
    {"id": "gpt-4o-mini",  "label": "GPT-4o mini · Rápido y económico"},
    {"id": "gpt-4-turbo",  "label": "GPT-4 Turbo"},
    {"id": "o1",           "label": "o1 · Razonamiento avanzado"},
    {"id": "o1-mini",      "label": "o1-mini · Razonamiento rápido"},
    {"id": "o3-mini",      "label": "o3-mini · Razonamiento (más reciente)"},
]

ANTHROPIC_MODELS: list[dict] = [
    {"id": "claude-opus-4-5",              "label": "Claude Opus 4.5 · Más potente"},
    {"id": "claude-sonnet-4-5",            "label": "Claude Sonnet 4.5 · Balanceado"},
    {"id": "claude-haiku-3-5",             "label": "Claude Haiku 3.5 · Rápido"},
    {"id": "claude-3-7-sonnet-20250219",   "label": "Claude 3.7 Sonnet · Razonamiento"},
    {"id": "claude-3-5-sonnet-20241022",   "label": "Claude 3.5 Sonnet"},
    {"id": "claude-3-5-haiku-20241022",    "label": "Claude 3.5 Haiku"},
    {"id": "claude-3-opus-20240229",       "label": "Claude 3 Opus"},
]

GOOGLE_MODELS: list[dict] = [
    {"id": "gemini-2.0-flash",               "label": "Gemini 2.0 Flash · Recomendado"},
    {"id": "gemini-2.0-flash-exp",           "label": "Gemini 2.0 Flash Experimental"},
    {"id": "gemini-2.0-flash-thinking-exp",  "label": "Gemini 2.0 Flash Thinking"},
    {"id": "gemini-1.5-pro",                 "label": "Gemini 1.5 Pro"},
    {"id": "gemini-1.5-flash",               "label": "Gemini 1.5 Flash · Rápido"},
    {"id": "gemini-1.5-flash-8b",            "label": "Gemini 1.5 Flash 8B · Más rápido"},
]

PROVIDERS: dict[str, dict] = {
    "groq":      {"name": "🟢 Groq (Llama, Gemma, Mistral…)", "models": GROQ_MODELS_FALLBACK, "key_name": "GROQ_API_KEY",      "free": True},
    "openai":    {"name": "💬 OpenAI (ChatGPT)",               "models": OPENAI_MODELS,        "key_name": "OPENAI_API_KEY",    "free": False},
    "anthropic": {"name": "🔮 Anthropic (Claude)",             "models": ANTHROPIC_MODELS,     "key_name": "ANTHROPIC_API_KEY", "free": False},
    "google":    {"name": "✨ Google (Gemini)",                 "models": GOOGLE_MODELS,        "key_name": "GOOGLE_API_KEY",    "free": False},
}

MODEL_DEFAULT   = "llama-3.3-70b-versatile"
PROVIDER_DEFAULT = "groq"

# ── System prompt ─────────────────────────────────────────────────────────────

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

# ── Tool definitions (formato OpenAI-compatible) ──────────────────────────────

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "consultar_iva_mes",
            "description": "Retorna IVA total, descontable y de mandatos para un mes YYYY-MM.",
            "parameters": {
                "type": "object",
                "properties": {"mes": {"type": "string", "description": "Mes en formato YYYY-MM"}},
                "required": ["mes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top_proveedores",
            "description": "Lista los N proveedores con mayor gasto total.",
            "parameters": {
                "type": "object",
                "properties": {"n": {"type": "integer", "default": 10}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_factura",
            "description": "Busca facturas por folio, NIT emisor o nombre del emisor.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resumen_errores",
            "description": "Lista facturas con errores de validación.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resumen_general",
            "description": "KPIs generales: total documentos, suma COP, IVA, errores.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# ── Groq: fetch live models ───────────────────────────────────────────────────

def get_groq_models() -> list[dict]:
    """Obtiene la lista actualizada de modelos desde la API de Groq."""
    key = _get_key("GROQ_API_KEY")
    if not key:
        return GROQ_MODELS_FALLBACK
    try:
        from groq import Groq
        data = Groq(api_key=key).models.list().data
        models = sorted(
            [{"id": m.id, "label": m.id} for m in data if getattr(m, "active", True)],
            key=lambda x: x["id"],
        )
        return models if models else GROQ_MODELS_FALLBACK
    except Exception:
        return GROQ_MODELS_FALLBACK


# ── Tool implementations ──────────────────────────────────────────────────────

def _fmt_cop(v: float) -> str:
    return f"${v:,.0f} COP"


def _df_summary(df: pd.DataFrame) -> str:
    """Resumen compacto del DataFrame para incluir en system prompt."""
    total = len(df)
    total_cop = df.get("total", pd.Series(dtype=float)).sum()
    iva = df.get("iva_19", pd.Series(dtype=float)).sum()
    periodos = df.get("fecha", pd.Series(dtype=str)).str[:7].dropna().unique().tolist()
    return (
        f"{total} facturas, total {_fmt_cop(total_cop)}, IVA 19% {_fmt_cop(iva)}. "
        f"Períodos: {', '.join(sorted(periodos))}."
    )


def _tool_consultar_iva_mes(df: pd.DataFrame, mes: str) -> str:
    df_mes = df[df["fecha"].str.startswith(mes, na=False)]
    if df_mes.empty:
        return f"No hay documentos para {mes}."
    mandatos = df_mes[df_mes["tipo"].str.contains("mandato|peaje", case=False, na=False)]
    normales  = df_mes[~df_mes["tipo"].str.contains("mandato|peaje", case=False, na=False)]
    return (
        f"IVA {mes}:\n"
        f"- Total: {_fmt_cop(df_mes['iva_19'].sum() + df_mes['iva_5'].sum())}\n"
        f"- Descontable: {_fmt_cop(normales['iva_19'].sum() + normales['iva_5'].sum())}\n"
        f"- Mandatos/peajes (no descontable): {_fmt_cop(mandatos['iva_19'].sum() + mandatos['iva_5'].sum())}\n"
        f"- Documentos: {len(df_mes)}"
    )


def _tool_top_proveedores(df: pd.DataFrame, n: int = 10) -> str:
    if "nombre_emisor" not in df.columns:
        return "Sin datos de proveedores."
    top = (
        df.groupby(["nit_emisor", "nombre_emisor"])["subtotal"]
        .sum().sort_values(ascending=False).head(n).reset_index()
    )
    lines = [f"Top {n} proveedores:"]
    for i, row in top.iterrows():
        lines.append(f"{i+1}. {row['nombre_emisor']} (NIT {row['nit_emisor']}): {_fmt_cop(row['subtotal'])}")
    return "\n".join(lines)


def _tool_buscar_factura(df: pd.DataFrame, query: str) -> str:
    q = query.lower()
    mask = (
        df.get("folio", pd.Series(dtype=str)).str.lower().str.contains(q, na=False)
        | df.get("nit_emisor", pd.Series(dtype=str)).str.lower().str.contains(q, na=False)
        | df.get("nombre_emisor", pd.Series(dtype=str)).str.lower().str.contains(q, na=False)
    )
    res = df[mask]
    if res.empty:
        return f"No se encontraron facturas con '{query}'."
    cols = [c for c in ["folio", "fecha", "nombre_emisor", "nit_emisor", "total", "validacion"] if c in res.columns]
    lines = [f"{len(res)} resultado(s):"]
    for _, row in res[cols].iterrows():
        lines.append(" | ".join(str(row.get(c, "")) for c in cols))
    return "\n".join(lines)


def _tool_resumen_errores(df: pd.DataFrame) -> str:
    if "validacion" not in df.columns:
        return "Sin datos de validación."
    err = df[df["validacion"] == "ERROR"]
    if err.empty:
        return "Sin errores. Todas las facturas están OK."
    lines = [f"{len(err)} factura(s) con errores:"]
    for _, row in err.iterrows():
        lines.append(f"- {row.get('folio','?')} | {row.get('nombre_emisor','?')} | {row.get('observacion','sin detalle')}")
    return "\n".join(lines)


def _tool_resumen_general(df: pd.DataFrame) -> str:
    return (
        f"Resumen:\n"
        f"- Documentos: {len(df)}\n"
        f"- Total COP: {_fmt_cop(df.get('total', pd.Series(dtype=float)).sum())}\n"
        f"- IVA 19%: {_fmt_cop(df.get('iva_19', pd.Series(dtype=float)).sum())}\n"
        f"- IVA 5%: {_fmt_cop(df.get('iva_5', pd.Series(dtype=float)).sum())}\n"
        f"- Errores: {int((df.get('validacion', pd.Series(dtype=str)) == 'ERROR').sum())}"
    )


def _ejecutar_herramienta(nombre: str, args: dict, df: pd.DataFrame) -> str:
    if nombre == "consultar_iva_mes":   return _tool_consultar_iva_mes(df, args.get("mes", ""))
    if nombre == "top_proveedores":     return _tool_top_proveedores(df, args.get("n", 10))
    if nombre == "buscar_factura":      return _tool_buscar_factura(df, args.get("query", ""))
    if nombre == "resumen_errores":     return _tool_resumen_errores(df)
    if nombre == "resumen_general":     return _tool_resumen_general(df)
    return f"Herramienta '{nombre}' no reconocida."


# ── Provider: Groq ────────────────────────────────────────────────────────────

def _responder_groq(prompt: str, df, historial: list[dict], model: str) -> str:
    key = _get_key("GROQ_API_KEY")
    if not key:
        return "⚠️ Falta `GROQ_API_KEY` en `.streamlit/secrets.toml`."
    from groq import Groq
    client = Groq(api_key=key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + historial + [
        {"role": "user", "content": prompt}
    ]
    try:
        while True:
            resp = client.chat.completions.create(
                model=model, messages=messages,
                tools=TOOLS if df is not None else [],
                tool_choice="auto" if df is not None else "none",
                max_tokens=1024,
            )
            msg = resp.choices[0].message
            if resp.choices[0].finish_reason == "tool_calls" and msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    resultado = _ejecutar_herramienta(tc.function.name, json.loads(tc.function.arguments), df)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": resultado})
                continue
            return msg.content or "Sin respuesta."
    except Exception as e:
        return _handle_error(e, model)


# ── Provider: OpenAI ──────────────────────────────────────────────────────────

def _responder_openai(prompt: str, df, historial: list[dict], model: str) -> str:
    key = _get_key("OPENAI_API_KEY")
    if not key:
        return "⚠️ Falta `OPENAI_API_KEY` en `.streamlit/secrets.toml`."
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + historial + [
            {"role": "user", "content": prompt}
        ]
        while True:
            resp = client.chat.completions.create(
                model=model, messages=messages,
                tools=TOOLS if df is not None else None,
                tool_choice="auto" if df is not None else None,
                max_tokens=1024,
            )
            msg = resp.choices[0].message
            if resp.choices[0].finish_reason == "tool_calls" and msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    resultado = _ejecutar_herramienta(tc.function.name, json.loads(tc.function.arguments), df)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": resultado})
                continue
            return msg.content or "Sin respuesta."
    except Exception as e:
        return _handle_error(e, model)


# ── Provider: Anthropic ───────────────────────────────────────────────────────

def _responder_anthropic(prompt: str, df, historial: list[dict], model: str) -> str:
    key = _get_key("ANTHROPIC_API_KEY")
    if not key:
        return "⚠️ Falta `ANTHROPIC_API_KEY` en `.streamlit/secrets.toml`."
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=key)
        system = SYSTEM_PROMPT
        if df is not None and not df.empty:
            system += f"\n\nDatos de facturas cargadas: {_df_summary(df)}"
        # Anthropic: roles deben alternar user/assistant
        messages = []
        for m in historial:
            role = "user" if m["role"] == "user" else "assistant"
            messages.append({"role": role, "content": m["content"]})
        messages.append({"role": "user", "content": prompt})
        resp = client.messages.create(
            model=model, max_tokens=1024, system=system, messages=messages
        )
        return resp.content[0].text
    except Exception as e:
        return _handle_error(e, model)


# ── Provider: Google Gemini ───────────────────────────────────────────────────

def _responder_google(prompt: str, df, historial: list[dict], model: str) -> str:
    key = _get_key("GOOGLE_API_KEY")
    if not key:
        return "⚠️ Falta `GOOGLE_API_KEY` en `.streamlit/secrets.toml`."
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        system = SYSTEM_PROMPT
        if df is not None and not df.empty:
            system += f"\n\nDatos de facturas: {_df_summary(df)}"
        gen_model = genai.GenerativeModel(model, system_instruction=system)
        history = []
        for m in historial:
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [m["content"]]})
        resp = gen_model.start_chat(history=history).send_message(prompt)
        return resp.text
    except Exception as e:
        return _handle_error(e, model)


# ── Error handler ─────────────────────────────────────────────────────────────

def _handle_error(e: Exception, model: str) -> str:
    err = str(e)
    if "decommissioned" in err or "model_decommissioned" in err:
        return f"⚠️ El modelo `{model}` fue dado de baja. Selecciona otro en el sidebar."
    if "rate_limit" in err.lower():
        return "⏳ Límite de velocidad alcanzado. Espera unos segundos e intenta de nuevo."
    if "authentication" in err.lower() or "api_key" in err.lower() or "invalid" in err.lower():
        return f"🔑 API key inválida o sin permisos. Verifica tu clave en `secrets.toml`."
    if "not found" in err.lower() or "404" in err or "models/" in err.lower():
        return (
            f"❌ Modelo `{model}` no encontrado.\n\n"
            f"Error de la API: `{err}`\n\n"
            "Usa el toggle **ID personalizado** para escribir un ID válido, "
            "o selecciona otro modelo de la lista."
        )
    return f"❌ Error ({type(e).__name__}): {err}"


# ── Función principal ─────────────────────────────────────────────────────────

def responder(
    prompt: str,
    df: pd.DataFrame | None,
    historial: list[dict],
    model: str = MODEL_DEFAULT,
    provider: str = PROVIDER_DEFAULT,
) -> str:
    if provider == "groq":      return _responder_groq(prompt, df, historial, model)
    if provider == "openai":    return _responder_openai(prompt, df, historial, model)
    if provider == "anthropic": return _responder_anthropic(prompt, df, historial, model)
    if provider == "google":    return _responder_google(prompt, df, historial, model)
    return f"Proveedor '{provider}' no reconocido."


# Backward-compat
AVAILABLE_MODELS = GROQ_MODELS_FALLBACK


# ── Constantes ────────────────────────────────────────────────────────────────

MODEL_DEFAULT = "llama-3.3-70b-versatile"

AVAILABLE_MODELS: list[dict] = [
    {"id": "llama-3.3-70b-versatile",        "label": "Llama 3.3 70B · Versatile (recomendado)"},
    {"id": "llama-3.1-8b-instant",            "label": "Llama 3.1 8B · Instant (más rápido)"},
    {"id": "llama3-70b-8192",                 "label": "Llama 3 70B · 8k ctx"},
    {"id": "deepseek-r1-distill-llama-70b",   "label": "DeepSeek R1 70B · Razonamiento"},
    {"id": "gemma2-9b-it",                    "label": "Gemma 2 9B · Google"},
    {"id": "qwen-qwq-32b",                    "label": "Qwen QwQ 32B · Razonamiento"},
    {"id": "meta-llama/llama-4-scout-17b-16e-instruct", "label": "Llama 4 Scout 17B · Meta"},
]

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


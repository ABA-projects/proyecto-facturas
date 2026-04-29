"""Orquestación del pipeline: extracción → validación → prorrateo.

UI-agnóstico: lo llama Streamlit, CLI, FastAPI o cualquier otro cliente.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from extractor import extract_one
from validator import validate, build_validation_sheet
from prorateo import calcular_prorateo, calcular_prorateo_simple

BASE_COLS = [
    "tipo", "cufe", "folio", "fecha",
    "nit_emisor", "nombre_emisor", "nit_receptor", "nombre_receptor",
    "subtotal", "base_iva_19", "iva_19", "base_iva_5", "iva_5",
    "no_gravado", "total", "retencion_fuente", "fuente",
]


@dataclass
class ResultadoProcesamiento:
    df_base: pd.DataFrame
    df_val: pd.DataFrame
    df_pror: pd.DataFrame
    total_archivos: int
    errores: int


def procesar(
    archivos: list[Path],
    ingresos_gravados: dict[str, float] | None = None,
    ingresos_excluidos: dict[str, float] | None = None,
    on_progress: callable | None = None,
) -> ResultadoProcesamiento:
    """
    Procesa una lista de archivos PDF/XML y retorna los tres DataFrames.

    Args:
        archivos: Lista de rutas a procesar.
        ingresos_gravados: Dict {YYYY-MM: float} para prorrateo Art. 490 ET.
        ingresos_excluidos: Dict {YYYY-MM: float} para prorrateo.
        on_progress: Callback opcional (i, total, nombre_archivo) para reportar progreso.

    Returns:
        ResultadoProcesamiento con df_base, df_val, df_pror y métricas.
    """
    processed_keys: set[str] = set()
    filas = []

    for i, archivo in enumerate(archivos):
        clave = str(archivo.with_suffix("")).lower()
        if clave in processed_keys:
            continue
        processed_keys.add(clave)

        if on_progress:
            on_progress(i, len(archivos), archivo.name)

        try:
            row = extract_one(archivo)
            if row:
                filas.append(row)
        except Exception:
            pass

    if not filas:
        empty = pd.DataFrame(columns=BASE_COLS)
        return ResultadoProcesamiento(
            df_base=empty, df_val=empty, df_pror=pd.DataFrame(),
            total_archivos=len(archivos), errores=0,
        )

    df = pd.DataFrame(filas)
    df = validate(df)
    df_val = build_validation_sheet(df)

    grav = ingresos_gravados or {}
    excl = ingresos_excluidos or {}
    df_pror = calcular_prorateo(df, grav, excl) if grav else calcular_prorateo_simple(df)

    df_base = df[[c for c in BASE_COLS if c in df.columns]]
    errores = int((df_val.get("validacion", pd.Series(dtype=str)) == "ERROR").sum())

    return ResultadoProcesamiento(
        df_base=df_base,
        df_val=df_val,
        df_pror=df_pror,
        total_archivos=len(archivos),
        errores=errores,
    )


def parse_ingresos(raw: str) -> tuple[dict[str, float], dict[str, float]]:
    """Parsea el string del sidebar: 'YYYY-MM=gravados|excluidos'."""
    grav, excl = {}, {}
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        mes, vals = line.split("=", 1)
        partes = vals.split("|")
        try:
            grav[mes.strip()] = float(partes[0].strip().replace(",", ""))
            if len(partes) > 1:
                excl[mes.strip()] = float(partes[1].strip().replace(",", ""))
        except ValueError:
            pass
    return grav, excl

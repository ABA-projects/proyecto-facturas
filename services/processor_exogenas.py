"""Orquestación UI-agnóstica para procesamiento de exógenas (Formato 1003)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

from exogenas.extractor import extract_many
from exogenas.municipios import buscar_municipio


@dataclass
class ResultadoExogenas:
    df_detalle:      pd.DataFrame
    df_1003:         pd.DataFrame
    total_archivos:  int
    errores:         int
    ica_excluidos:   int
    advertencias:    list[str] = field(default_factory=list)


def _agregar(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa por (nit, concepto), suma base y retención."""
    df_clean = df[df["concepto"] != "ICA"].copy()
    if df_clean.empty:
        return pd.DataFrame(columns=[
            "concepto","tipo_doc","nit","dv","primer_apellido","segundo_apellido",
            "primer_nombre","otros_nombres","razon_social","direccion",
            "cod_dpto","cod_mpio","base","retencion","porcentaje",
        ])

    agg = (
        df_clean
        .groupby(["nit", "concepto"], as_index=False)
        .agg(
            razon_social     =("razon_social", "first"),
            dv               =("dv", "first"),
            tipo_doc         =("tipo_doc", "first"),
            direccion        =("direccion", "first"),
            ciudad_retencion =("ciudad_retencion", "first"),
            cod_dpto         =("cod_dpto", "first"),
            cod_mpio         =("cod_mpio", "first"),
            base             =("base", "sum"),
            retencion        =("retencion", "sum"),
            porcentaje       =("porcentaje", "first"),
        )
    )

    for col in ("primer_apellido", "segundo_apellido", "primer_nombre", "otros_nombres"):
        agg[col] = ""

    col_order = [
        "concepto","tipo_doc","nit","dv","primer_apellido","segundo_apellido",
        "primer_nombre","otros_nombres","razon_social","direccion",
        "ciudad_retencion","cod_dpto","cod_mpio","base","retencion","porcentaje",
    ]
    return agg[col_order]


def procesar_exogenas(
    paths: list[Path],
    on_progress: Callable[[int, int, str], None] | None = None,
    org_id: str | None = None,          # Si se pasa, guarda en PostgreSQL
) -> ResultadoExogenas:
    """
    Procesa una lista de certificados de retención PDF.
    Retorna ResultadoExogenas con DataFrames listos para UI y Excel.

    Args:
        paths: Lista de rutas a procesar.
        on_progress: Callback opcional (i, total, nombre) para reportar progreso.
        org_id: UUID de organización. Si se pasa, persiste en PostgreSQL.
    """
    filas: list[dict] = []
    errores = 0
    advertencias: list[str] = []

    for i, p in enumerate(paths):
        if on_progress:
            on_progress(i, len(paths), Path(p).name)
        try:
            rows = extract_many(p)
            for row in rows:
                if row.get("error"):
                    errores += 1
                    advertencias.append(f"⚠️ {Path(p).name}: {row['error']}")
                filas.append(row)
        except Exception as e:
            errores += 1
            advertencias.append(f"❌ {Path(p).name}: {e}")

    if not filas:
        return ResultadoExogenas(
            df_detalle=pd.DataFrame(),
            df_1003=pd.DataFrame(),
            total_archivos=len(paths),
            errores=errores,
            ica_excluidos=0,
            advertencias=advertencias,
        )

    df = pd.DataFrame(filas)

    # Resolver códigos de municipio
    def _resolve_mpio(ciudad: str) -> pd.Series:
        dpto, mpio = buscar_municipio(str(ciudad))
        return pd.Series({"cod_dpto": dpto, "cod_mpio": mpio})

    mpio_df = df["ciudad_retencion"].apply(_resolve_mpio)
    df["cod_dpto"] = mpio_df["cod_dpto"]
    df["cod_mpio"] = mpio_df["cod_mpio"]

    ica_count = int((df["concepto"] == "ICA").sum())
    df_1003 = _agregar(df)

    # Advertir filas sin municipio detectado
    sin_mpio = df_1003[df_1003["cod_dpto"] == ""]
    for _, row in sin_mpio.iterrows():
        advertencias.append(
            f"ℹ️ No se encontró código DIAN para ciudad '{row.get('ciudad_retencion','')}' "
            f"({row.get('razon_social','')}). Completa manualmente."
        )

    # ── Persistir en PostgreSQL ───────────────────────────────────────────────
    if org_id and not df_1003.empty:
        try:
            from db.database import insert_exogenas_batch, db_available
            if db_available():
                insert_exogenas_batch(df_1003, org_id)
        except Exception:
            pass

    return ResultadoExogenas(
        df_detalle=df,
        df_1003=df_1003,
        total_archivos=len(paths),
        errores=errores,
        ica_excluidos=ica_count,
        advertencias=advertencias,
    )

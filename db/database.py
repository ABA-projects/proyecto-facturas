"""db/database.py — PostgreSQL access layer. Engine is lazy: only created when DATABASE_URL is set."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

import pandas as pd

_DATABASE_URL: str | None = os.environ.get("DATABASE_URL")

# Module-level engine/session — created only when DATABASE_URL is present
_engine = None
_SessionLocal = None

if _DATABASE_URL:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, Session
    _engine = create_engine(
        _DATABASE_URL,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=5,
        echo=False,
        connect_args={"connect_timeout": 3},
    )
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

_db_status: bool | None = None


@contextmanager
def get_db() -> Generator:
    if _SessionLocal is None:
        raise RuntimeError("DATABASE_URL not set — DB unavailable")
    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def db_available() -> bool:
    """True if PostgreSQL is reachable. Result is cached for the process lifetime."""
    global _db_status
    if _DATABASE_URL is None:
        return False
    if _db_status is not None:
        return _db_status
    try:
        from sqlalchemy import text
        with get_db() as db:
            db.execute(text("SELECT 1"))
        _db_status = True
    except Exception:
        _db_status = False
    return _db_status


def get_existing_cufes(org_id: str) -> set[str]:
    """CUFEs already processed for an org. Returns empty set if DB unavailable."""
    try:
        from sqlalchemy import text
        with get_db() as db:
            rows = db.execute(
                text("SELECT cufe FROM invoices WHERE org_id = :org_id"),
                {"org_id": org_id},
            ).fetchall()
        return {r[0] for r in rows}
    except Exception:
        return set()


def insert_invoices_batch(rows: list[dict], org_id: str, session_id: str | None = None) -> tuple[int, int]:
    """Insert invoices in batch. Skips duplicates via ON CONFLICT DO NOTHING.

    Returns:
        (new_count, duplicate_count)
    """
    if not rows or not db_available():
        return 0, 0

    from sqlalchemy import text
    sql = text("""
        INSERT INTO invoices (
            org_id, cufe, folio, tipo, fecha,
            nit_emisor, nombre_emisor, nit_receptor, nombre_receptor,
            subtotal, base_iva_19, iva_19, base_iva_5, iva_5,
            no_gravado, total, retencion_fuente, fuente, periodo
        ) VALUES (
            :org_id, :cufe, :folio, :tipo, :fecha,
            :nit_emisor, :nombre_emisor, :nit_receptor, :nombre_receptor,
            :subtotal, :base_iva_19, :iva_19, :base_iva_5, :iva_5,
            :no_gravado, :total, :retencion_fuente, :fuente, :periodo
        )
        ON CONFLICT (org_id, cufe) DO NOTHING
    """)

    nuevas = 0
    with get_db() as db:
        for row in rows:
            r = dict(row)
            r["org_id"] = org_id
            fecha = r.get("fecha") or None
            r["fecha"] = fecha
            if fecha and str(fecha) not in ("None", "nan", ""):
                try:
                    r["periodo"] = str(fecha)[:7]
                except Exception:
                    r["periodo"] = None
            else:
                r["periodo"] = None
            result = db.execute(sql, r)
            nuevas += result.rowcount

    return nuevas, len(rows) - nuevas


def insert_exogenas_batch(df: pd.DataFrame, org_id: str, session_id: str | None = None) -> None:
    """Insert exogenas detail rows into exogenas_results. One row per df row."""
    if df.empty or not db_available():
        return

    from sqlalchemy import text
    import json
    sql = text("""
        INSERT INTO exogenas_results (org_id, session_id, anio, concepto, nit,
            razon_social, base, retencion, porcentaje, raw_row)
        VALUES (:org_id, :session_id, :anio, :concepto, :nit,
            :razon_social, :base, :retencion, :porcentaje, :raw_row::jsonb)
        ON CONFLICT (org_id, nit, concepto, anio) DO NOTHING
    """)

    with get_db() as db:
        for _, row in df.iterrows():
            db.execute(sql, {
                "org_id":       org_id,
                "session_id":   session_id,
                "anio":         int(row.get("anio", 0) or 0),
                "concepto":     str(row.get("concepto") or ""),
                "nit":          str(row.get("nit") or ""),
                "razon_social": str(row.get("razon_social") or ""),
                "base":         float(row.get("base") or 0),
                "retencion":    float(row.get("retencion") or 0),
                "porcentaje":   float(row.get("porcentaje") or 0),
                "raw_row":      json.dumps(row.to_dict(), default=str),
            })


def get_autorretenedores_nits() -> set[str]:
    """Load autorretenedor NITs from PostgreSQL. Falls back to empty set."""
    try:
        from sqlalchemy import text
        with get_db() as db:
            rows = db.execute(
                text("SELECT nit FROM autorretenedores WHERE vigente = TRUE")
            ).fetchall()
        return {r[0] for r in rows}
    except Exception:
        return set()


# ── Cleanup helpers (used by future admin UI) ─────────────────────────────────

def preview_cleanup(org_id: str, meses_a_conservar: int = 3) -> dict:
    """Preview what would be deleted. Does NOT delete anything."""
    try:
        from sqlalchemy import text
        with get_db() as db:
            corte_result = db.execute(
                text(f"SELECT TO_CHAR(NOW() - INTERVAL '{meses_a_conservar} months', 'YYYY-MM') AS corte")
            ).fetchone()
            corte = corte_result[0] if corte_result else None
            if not corte:
                return {"total": 0, "periodos": [], "desde_periodo": ""}
            rows = db.execute(
                text("""
                    SELECT periodo, COUNT(*) as cnt
                    FROM invoices
                    WHERE org_id = :org_id AND periodo IS NOT NULL AND periodo < :corte
                    GROUP BY periodo ORDER BY periodo
                """),
                {"org_id": org_id, "corte": corte},
            ).fetchall()
        periodos = [{"periodo": r[0], "count": r[1]} for r in rows]
        return {"total": sum(p["count"] for p in periodos), "periodos": periodos, "desde_periodo": corte}
    except Exception as e:
        return {"total": 0, "periodos": [], "desde_periodo": "", "error": str(e)}


def execute_cleanup(org_id: str, meses_a_conservar: int = 3) -> int:
    """Delete invoices older than N months. Returns number of deleted rows."""
    try:
        from sqlalchemy import text
        with get_db() as db:
            corte_result = db.execute(
                text(f"SELECT TO_CHAR(NOW() - INTERVAL '{meses_a_conservar} months', 'YYYY-MM') AS corte")
            ).fetchone()
            corte = corte_result[0] if corte_result else None
            if not corte:
                return 0
            result = db.execute(
                text("DELETE FROM invoices WHERE org_id = :org_id AND periodo IS NOT NULL AND periodo < :corte"),
                {"org_id": org_id, "corte": corte},
            )
            return result.rowcount
    except Exception:
        return 0

"""db/database.py — Capa de acceso a PostgreSQL con SQLAlchemy.

Uso actual: utilidad para el procesamiento incremental (deduplicación por CUFE).
Ruta hacia FastAPI: este módulo es UI-agnóstico y se importa igual desde Streamlit o FastAPI.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# ── Configuración ─────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://taxops:taxops_dev_pass@localhost:5432/taxops",
)

# pool_pre_ping detecta conexiones caídas automáticamente
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,  # True para ver SQL en consola durante desarrollo
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager para sesiones DB. Uso:

    with get_db() as db:
        db.execute(text("SELECT 1"))
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Helpers de negocio ────────────────────────────────────────────────────────

def db_available() -> bool:
    """Retorna True si la conexión a PostgreSQL está activa."""
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_existing_cufes(org_id: str) -> set[str]:
    """Retorna el conjunto de CUFEs ya procesados para una organización.

    Utilizado por services/processor.py para el procesamiento incremental.
    Si la DB no está disponible retorna set vacío (degraded mode).
    """
    try:
        with get_db() as db:
            rows = db.execute(
                text("SELECT cufe FROM invoices WHERE org_id = :org_id"),
                {"org_id": org_id},
            ).fetchall()
        return {r[0] for r in rows}
    except Exception:
        return set()


def insert_invoices_batch(rows: list[dict], org_id: str, session_id: str | None = None) -> tuple[int, int]:
    """Inserta facturas en lote. Omite duplicados (ON CONFLICT DO NOTHING).

    Returns:
        (nuevas, duplicadas) conteo de filas.
    """
    if not rows:
        return 0, 0

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
            :no_gravado, :total, :retencion_fuente, :fuente,
            TO_CHAR(:fecha::date, 'YYYY-MM')
        )
        ON CONFLICT (org_id, cufe) DO NOTHING
    """)

    nuevas = 0
    try:
        with get_db() as db:
            for row in rows:
                r = dict(row)
                r["org_id"] = org_id
                # Normalizar None para fecha
                if not r.get("fecha"):
                    r["fecha"] = None
                result = db.execute(sql, r)
                nuevas += result.rowcount
    except Exception:
        return 0, len(rows)

    duplicadas = len(rows) - nuevas
    return nuevas, duplicadas


def get_autorretenedores_nits() -> set[str]:
    """Carga NITs autorretenedores desde PostgreSQL.

    Fallback a set vacío si la DB no está disponible (el validador
    usará el archivo .txt como respaldo).
    """
    try:
        with get_db() as db:
            rows = db.execute(
                text("SELECT nit FROM autorretenedores WHERE vigente = TRUE")
            ).fetchall()
        return {r[0] for r in rows}
    except Exception:
        return set()

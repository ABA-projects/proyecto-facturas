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
            :no_gravado, :total, :retencion_fuente, :fuente, :periodo
        )
        ON CONFLICT (org_id, cufe) DO NOTHING
    """)

    nuevas = 0
    with get_db() as db:
        for row in rows:
            r = dict(row)
            r["org_id"] = org_id
            # Normalizar fecha y calcular periodo en Python
            fecha = r.get("fecha") or None
            r["fecha"] = fecha
            if fecha and str(fecha) not in ("None", "nan", ""):
                try:
                    r["periodo"] = str(fecha)[:7]  # "YYYY-MM"
                except Exception:
                    r["periodo"] = None
            else:
                r["periodo"] = None
            result = db.execute(sql, r)
            nuevas += result.rowcount

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


# ── Limpieza mensual ──────────────────────────────────────────────────────────

def preview_cleanup(org_id: str, meses_a_conservar: int = 3) -> dict:
    """Devuelve cuántas facturas y qué períodos se borrarían SIN borrar nada.

    Args:
        org_id: UUID de la organización.
        meses_a_conservar: Períodos recientes a mantener (default 3).

    Returns:
        dict con 'total', 'periodos' (lista), 'desde_periodo' (str corte).
    """
    try:
        with get_db() as db:
            # Calcular el período de corte: hoy - N meses
            corte_sql = text(
                "SELECT TO_CHAR(NOW() - INTERVAL ':n months', 'YYYY-MM') AS corte"
            )
            # SQLAlchemy no interpola bien en INTERVAL, usamos formato directo
            from sqlalchemy import literal_column
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
                    WHERE org_id = :org_id
                      AND periodo IS NOT NULL
                      AND periodo < :corte
                    GROUP BY periodo
                    ORDER BY periodo
                """),
                {"org_id": org_id, "corte": corte},
            ).fetchall()

        periodos = [{"periodo": r[0], "count": r[1]} for r in rows]
        total = sum(p["count"] for p in periodos)
        return {
            "total": total,
            "periodos": periodos,
            "desde_periodo": corte,
        }
    except Exception as e:
        return {"total": 0, "periodos": [], "desde_periodo": "", "error": str(e)}


def execute_cleanup(org_id: str, meses_a_conservar: int = 3) -> int:
    """Elimina facturas más antiguas que N meses. Requiere aprobación previa en UI.

    Returns:
        Número de filas eliminadas.
    """
    try:
        with get_db() as db:
            corte_result = db.execute(
                text(f"SELECT TO_CHAR(NOW() - INTERVAL '{meses_a_conservar} months', 'YYYY-MM') AS corte")
            ).fetchone()
            corte = corte_result[0] if corte_result else None
            if not corte:
                return 0

            result = db.execute(
                text("""
                    DELETE FROM invoices
                    WHERE org_id = :org_id
                      AND periodo IS NOT NULL
                      AND periodo < :corte
                """),
                {"org_id": org_id, "corte": corte},
            )
            return result.rowcount
    except Exception:
        return 0

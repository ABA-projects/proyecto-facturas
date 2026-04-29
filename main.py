"""
Sistema de gestión de facturas electrónicas DIAN.

Uso:
    python main.py                         # procesa carpeta ./facturas
    python main.py --carpeta /ruta/pdfs    # carpeta personalizada
    python main.py --ingresos 2026-04:5000000,2026-03:4500000
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from extractor import extract_document
from validator import validate, build_validation_sheet
from prorateo import calcular_prorateo, calcular_prorateo_simple
from excel_writer import write_excel

# ── Logging ────────────────────────────────────────────────────────────────
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"proceso_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def parse_ingresos(raw: str) -> tuple[dict, dict]:
    """
    Parsea argumento:
      --ingresos gravados:2026-04=5000000;2026-03=4500000,excluidos:2026-04=1000000
    Formato simple aceptado: YYYY-MM:valor (solo gravados).
    """
    grav, excl = {}, {}
    if not raw:
        return grav, excl
    for parte in raw.split(","):
        parte = parte.strip()
        if ":" in parte:
            mes, val = parte.split(":", 1)
            grav[mes.strip()] = float(val.strip().replace(".", "").replace(",", "."))
    return grav, excl


def procesar(carpeta: Path, ingresos_raw: str = "") -> Path:
    logger.info("Procesando carpeta: %s", carpeta)

    # Escaneo recursivo: incluye subcarpetas (ej. facturas/2026-03/)
    archivos = sorted(
        p for p in carpeta.rglob("*")
        if p.suffix.lower() in (".pdf", ".xml")
    )
    if not archivos:
        logger.warning("No se encontraron PDF/XML en %s", carpeta)
        sys.exit(0)

    processed: set[str] = set()
    filas = []
    for archivo in archivos:
        try:
            row = extract_document(archivo, processed)
            if row:
                # Incluye subcarpeta en el campo archivo para trazabilidad
                try:
                    rel = archivo.relative_to(carpeta)
                    if len(rel.parts) > 1:
                        row["archivo"] = str(rel)
                except ValueError:
                    pass
                filas.append(row)
                logger.info("OK  %s -> %s | Total: %s", archivo.name, row["tipo"], row["total"])
        except Exception as e:
            logger.error("FALLO %s: %s", archivo.name, e)

    if not filas:
        logger.error("No se extrajeron datos.")
        sys.exit(1)

    df = pd.DataFrame(filas)
    df = validate(df)

    errores = (df["validacion"] == "ERROR").sum()
    logger.info("Validación: %d OK | %d ERROR", len(df) - errores, errores)

    df_val = build_validation_sheet(df)

    grav, excl = parse_ingresos(ingresos_raw)
    if grav:
        df_pror = calcular_prorateo(df, grav, excl)
    else:
        df_pror = calcular_prorateo_simple(df)
        logger.warning("Ingresos no proporcionados — prorrateo al 100%")

    # Columnas ordenadas para BASE_DATOS (sin validacion/observacion — ver hoja VALIDACION)
    cols_base = [
        "tipo", "cufe", "folio", "fecha",
        "nit_emisor", "nombre_emisor", "nit_receptor", "nombre_receptor",
        "subtotal", "base_iva_19", "iva_19", "base_iva_5", "iva_5",
        "no_gravado", "total", "retencion_fuente", "fuente",
    ]
    df_base = df[[c for c in cols_base if c in df.columns]]

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"facturas_{stamp}.xlsx"

    write_excel(df_base, df_val, df_pror, out_path)
    logger.info("Excel generado: %s", out_path)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Procesador DIAN de facturas electrónicas")
    parser.add_argument("--carpeta",   default="facturas", help="Carpeta con PDF/XML")
    parser.add_argument("--ingresos",  default="",         help="Ingresos gravados: YYYY-MM:valor,...")
    args = parser.parse_args()

    carpeta = Path(args.carpeta)
    if not carpeta.exists():
        logger.error("Carpeta no encontrada: %s", carpeta)
        sys.exit(1)

    out = procesar(carpeta, args.ingresos)
    print(f"\nListo: {out}")


if __name__ == "__main__":
    main()

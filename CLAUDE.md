# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI processor (reads from facturas/, writes to output/)
python main.py
python main.py --carpeta C:/ruta/facturas --ingresos "2026-04:5000000,2026-03:4500000"

# Run Streamlit dashboard
streamlit run app.py
```

## Architecture

The system processes Colombian DIAN electronic invoices (PDF/XML) into a structured Excel workbook with three sheets: BASE_DATOS, VALIDACION, PRORRATEO_IVA.

**Data flow:** `facturas/` folder → `extractor.py` → `validator.py` → `prorateo.py` → `excel_writer.py` → `output/*.xlsx`

### Module responsibilities

- **`extractor.py`** — Entry point for document parsing. `extract_document()` dispatches to `extract_xml()` or `extract_pdf()`. XML always takes priority over PDF when both exist for the same stem. Returns a flat dict with fixed keys: `archivo, tipo, cufe, folio, fecha, nit_emisor, nombre_emisor, nit_receptor, nombre_receptor, subtotal, iva_19, iva_5, total, fuente`.

- **`validator.py`** — Stateless validation over a DataFrame. `validate()` adds `validacion` (OK/ERROR) and `observacion` columns. Checks: CUFE format (96 hex chars), CUFE duplicates, NIT format, subtotal+IVA≈total (tolerance: $1 COP), mandatory empty fields, mandato/peaje documents with IVA.

- **`prorateo.py`** — IVA proration per Art. 490 E.T. `calcular_prorateo()` takes dicts `{YYYY-MM: float}` for gravados/excluidos. Mandatos always go to non-deductible. Notas crédito carry negative values so they automatically reduce monthly totals. Use `calcular_prorateo_simple()` when income data is unavailable (defaults to 100% deductible with a warning column).

- **`excel_writer.py`** — Formats and writes the three-sheet workbook. Applies color coding: red for ERROR rows, green for OK. Uses `openpyxl` directly after pandas writes via `ExcelWriter`.

- **`main.py`** — CLI via `argparse`. Maintains a `processed: set[str]` of stems to avoid double-processing PDF+XML pairs.

- **`app.py`** — Streamlit UI. Uploads files to a `tempfile.TemporaryDirectory`, reuses all the same modules, offers download of the generated Excel.

### Document type detection

Detected by keywords in text or filename (case-insensitive):
- `"nota cr"` → Nota Crédito (values negated with sign = -1)
- `"mandato"` or `"peaje"` → Mandato/Peaje (IVA non-deductible)
- `"documento soporte"` → Documento Soporte
- Default → Factura Electrónica

### XML parsing

Uses `xml.etree.ElementTree` with UBL 2.1 namespaces (`cac`, `cbc`, `ext`). CUFE is at `cbc:UUID`. Tax percentages are read from `cac:TaxSubtotal/cbc:Percent` to distinguish IVA 19% vs 5%.

### PDF parsing

Uses `pdfplumber`. Extraction relies on regex patterns (`_RE_CUFE`, `_RE_NIT`, `_RE_DATE`, `_RE_FOLIO`, `_search_money_near()`). Colombian number format: dots as thousands separator, comma as decimal (`1.234.567,89`). Handled by `_clean_number()`.

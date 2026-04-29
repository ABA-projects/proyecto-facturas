# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI processor (reads from facturas/, writes to output/)
python main.py
python main.py --carpeta C:/ruta/facturas --ingresos "2026-04:5000000,2026-03:4500000"
python main.py --workers 8   # parallel threads (default: min(8, CPUs))

# Run file watcher (auto-processes when new files are added)
python watcher.py
python watcher.py --carpeta C:/ruta/facturas --ingresos "2026-04:5000000"

# Run Streamlit dashboard
python -m streamlit run app.py

# Run tests
python -m pytest                          # all tests
python -m pytest tests/test_extractor.py tests/test_validator.py tests/test_prorateo.py  # unit only
python -m pytest tests/test_e2e.py -v    # end-to-end (requires PDFs in facturas/)
python -m pytest --cov=. --cov-report=term-missing  # with coverage
```

## Architecture

The system processes Colombian DIAN electronic documents (PDF/XML) into a structured Excel workbook with three sheets: BASE_DATOS, VALIDACION, PRORRATEO_IVA.

**Data flow:** `facturas/` folder (recursive) → `extractor.py` → `validator.py` → `prorateo.py` → `excel_writer.py` → `output/*.xlsx`

### Module responsibilities

- **`extractor.py`** — Document parsing. `extract_one(path)` is the primary entry point (thread-safe, no shared state). `extract_document()` is the legacy interface used by watcher/app.py. Dispatches to `extract_xml()` or `extract_pdf()` based on extension. XML always takes priority when both exist. Returns a flat dict with all BASE_DATOS fields plus `archivo`. Falls back to folder name for date when the document has no parseable date. Loads `autorretenedores.txt` at module startup as a frozenset for O(1) lookup.

- **`validator.py`** — Stateless validation over a DataFrame. `validate()` adds `validacion` (OK/ERROR) and `observacion` columns. Checks: CUFE/CUDE format (96 hex chars), duplicates, NIT format, subtotal+IVA≈total (tolerance: $1 COP), mandatory empty fields, mandato/peaje with IVA. These columns appear only in the VALIDACION sheet, NOT in BASE_DATOS.

- **`prorateo.py`** — IVA proration per Art. 490 E.T. `calcular_prorateo()` takes dicts `{YYYY-MM: float}` for gravados/excluidos. Mandatos always go to non-deductible. Notas crédito carry negative values so they automatically reduce monthly totals. Nota Débito treated same as Factura (adds to IVA base). `calcular_prorateo_simple()` defaults to 100% deductible with a warning column when income data is unavailable.

- **`excel_writer.py`** — Formats and writes the three-sheet workbook. Applies color coding to the VALIDACION sheet (red for ERROR, green for OK). Money columns: `subtotal, base_iva_19, iva_19, base_iva_5, iva_5, no_gravado, total, retencion_fuente` all use `#,##0.00` format.

- **`main.py`** — CLI via `argparse`. Pre-resolves PDF/XML pairs with `_resolver_archivos()` (deduplication before parallelism). Processes files in parallel with `ThreadPoolExecutor`. Logs per-file detail to file; prints progress every 50 files to stdout. Args: `--carpeta`, `--ingresos`, `--workers`.

- **`watcher.py`** — File system watcher using `watchdog`. Monitors `facturas/` recursively. Debounce: 10 s. Wait on new file: 5 s (OS copy). Uses legacy `extract_document()` interface.

- **`app.py`** — Streamlit UI. Uploads files to `tempfile.TemporaryDirectory`, reuses all modules, offers Excel download.

- **`autorretenedores.txt`** — One NIT per line. 3,287 NITs from DIAN resolution list (cutoff 25/02/2026). Loaded at extractor module startup. To update: replace the file with a new one-NIT-per-line file.

### Parallel processing

`main.py` uses `ThreadPoolExecutor` for PDF extraction (I/O-bound). Deduplication is done upfront in `_resolver_archivos()` so no locks are needed during extraction. Progress logged every 50 files.

```
Procesando 800 documentos con 8 workers...
  50/800 (6%) — 0 errores
  ...
  800/800 (100%) — 3 errores
```

### Subfolder / folder-date support

`facturas/` supports nested subfolders named by date:

```
facturas/
├── 2026-03/         ← date detected from folder name → used as fallback date
│   └── FE-001.pdf
├── 2026-04/
│   └── FE-100.xml
└── FE-999.pdf       ← flat files also supported
```

`_date_from_folder(path)` parses YYYY-MM, YYYY-MM-DD, DD-MM-YYYY from folder name. Applied only when the document itself has no parseable date.

### Document type detection

Detected by keywords in text or filename stem (case-insensitive), in priority order:

| Type | Detection | Sign | IVA treatment |
|---|---|---|---|
| `Nota Crédito` | "nota cr", "note credit", stem `NC-*` | -1 | negative, reduces month |
| `Nota Débito` | "nota déb/deb", stem `ND-*` | +1 | adds to month base |
| `Mandato/Peaje` | "mandato", "peaje" | +1 | always non-deductible |
| `Documento Soporte` | "documento soporte" | +1 | normal |
| `Documento Equivalente` | "documento equivalente" | +1 | normal (POS, SPD, etc.) |
| `Factura Electrónica` | default | +1 | normal |

### Documento Equivalente — two sub-layouts

The "Documento Equivalente" type covers two different PDF layouts:

**POS layout** (e.g. SUPERMERCADO EL CAMPESINO):
- Has section `"Datos del adquiriente"` (receptor) BEFORE `"Datos del vendedor"` (emisor)
- Folio label: `"Número de documento: POSE5217"` (alphanumeric, starts with letter)
- Emisor NIT: `"Número de documento: 43450844"` inside vendedor section
- Receptor NIT: `"NIT del adquiriente: 222222222222"`
- Detected by presence of `"Datos del vendedor"` in text

**SPD layout** (e.g. EPM utility bill — DEE prefix):
- Has section `"Datos del emisor"` (standard position)
- Folio label: `"Número de documento: DEE46098616"` (starts with letter)
- Uses standard emisor/receptor patterns
- Detected by absence of `"Datos del vendedor"`

The extractor distinguishes these at runtime: `tiene_vendedor = bool(re.search(r'datos\s+del\s+vendedor', text, re.I))`.

### XML parsing

Uses `xml.etree.ElementTree` with UBL 2.1 namespaces (`cac`, `cbc`, `ext`). CUFE/CUDE at `cbc:UUID`. Tax percentages from `cac:TaxSubtotal/cbc:Percent` to distinguish IVA 19% vs 5%. `TaxableAmount` from `cac:TaxSubtotal/cbc:TaxableAmount` provides exact base per rate (more accurate than back-calculation). Supplier name: `PartyLegalEntity/RegistrationName` first, then `PartyName/Name`.

### PDF parsing

Uses `pdfplumber`. Labeled field patterns per document type, with fallbacks:

| Field | Primary pattern | Fallback |
|---|---|---|
| `folio` (factura/nota) | `"Número de Factura:"` | `"No. Factura:"`, `"Nro.:"` |
| `folio` (equivalente/soporte) | `"Número de documento: [A-Z]..."` | — (alpha prefix required) |
| `nit_emisor` (factura/nota/soporte) | `"Nit del Emisor:"` | generic NIT |
| `nit_emisor` (Doc Equiv POS) | `"Número de documento:"` in vendedor section | — |
| `nombre_emisor` (factura/nota/soporte) | `"Razón Social:"` (first occurrence) | — |
| `nombre_emisor` (Doc Equiv POS) | `"Razón social:"` in vendedor section | — |
| `nit_receptor` (factura/nota) | `"Número Documento:"` | `"nit del adquir..."` |
| `nit_receptor` (Doc Equiv POS) | `"NIT del adquiriente:"` | — |
| `nombre_receptor` (factura/nota) | `"Nombre o Razón Social:"` | adquiriente section |
| `nombre_receptor` (Doc Equiv/Soporte) | `"Razón social:"` in adquiriente section | — |
| `fecha` | `"Fecha de Emisión/Generación/Expedición:"` | first date found |
| `subtotal` | `"Total Bruto Factura"` or `"Total bruto documento"` | `"Base gravable"`, `"Subtotal"` |
| `iva_19` / `iva_5` | product detail lines (most accurate) | totals section, `"Total IVA"` |
| `total` | `"Total factura"` or `"Total documento"` | `"Total neto ..."`, `"Total a pagar"` |

**IVA extraction strategy** (`_extract_iva_detalle`):
1. Limits search to the product detail section (between "Detalles de productos" and "Notas finales/Datos totales")
2. Pattern: `{monto_iva} {pct}.00` — amount immediately before the tax rate
3. Sums separately for 19% and 5% across all product lines
4. Fallback if no matches: totals section labels → `"Total IVA"` (goes to iva_19 by convention)

Colombian number format: dots as thousands separator, comma as decimal (`1.234.567,89`). Handled by `_clean_number()`.

### BASE_DATOS columns (ordered)

```
tipo, cufe, folio, fecha,
nit_emisor, nombre_emisor, nit_receptor, nombre_receptor,
subtotal, base_iva_19, iva_19, base_iva_5, iva_5,
no_gravado, total, retencion_fuente, fuente
```

- `archivo` column was removed (not needed by user)
- `validacion` and `observacion` are NOT in BASE_DATOS — they live only in the VALIDACION sheet

### Retención en la fuente

```
retencion_fuente = subtotal × 2.5%
```
- Zero when `nit_emisor` is in `autorretenedores.txt` (frozenset, O(1) lookup)
- Zero for `Nota Crédito` (retention belongs to original invoice)
- Applied to absolute value of subtotal (sign-independent)

### IVA bases

```
base_iva_19 = iva_19 / 0.19   (back-calculated; XML uses TaxableAmount directly)
base_iva_5  = iva_5  / 0.05
no_gravado  = subtotal - base_iva_19 - base_iva_5  (min 0)
```

### Key regex patterns

```python
_RE_FOLIO       # "Número de Factura:" — facturas y notas
_RE_FOLIO_DOC   # "Número de documento: [A-Za-z]..." — doc equivalente/soporte
_RE_EMISOR_NIT  # "Nit del Emisor:"
_RE_EMISOR_NOMBRE  # "Razón Social:" (first occurrence = emisor)
_RE_VENDEDOR_NIT    # "Datos del vendedor ... Número de documento:" (POS)
_RE_VENDEDOR_NOMBRE # "Datos del vendedor ... Razón social:" (POS)
_RE_RECEPTOR_NIT    # "Número Documento:" or "nit del adquir..."
_RE_RECEPTOR_NOMBRE # "Nombre o Razón Social:"
_RE_ADQUIRIENTE_NIT    # "NIT del adquiriente:" (POS)
_RE_ADQUIRIENTE_NOMBRE # "Datos del adquir ... Razón social:" (POS/Soporte)
```

Critical regex bug fixed: `_search_money_near(text, "IVA", line_start=True)` — requires IVA at line start to avoid capturing street numbers from `"Responsabilidad tributaria: 01 - IVA Dirección: CALLE 26"`.

### Tests

```
tests/
├── test_extractor.py   # 44 unit tests — pure functions + mocked PDF
├── test_validator.py   # 19 unit tests — validation rules
├── test_prorateo.py    # 12 unit tests — Art. 490 ET
└── test_e2e.py         # 32 end-to-end tests (skip if PDFs absent)
```

E2E tests cover: field-level extraction of known PDFs (STK-602558, EB-33355), `_resolver_archivos` deduplication, full pipeline Excel output with 3 sheets and correct columns.

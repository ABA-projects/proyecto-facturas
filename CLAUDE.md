# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit app (entry point: Home.py)
python -m streamlit run Home.py

# Run CLI processor
python main.py
python main.py --carpeta /ruta/facturas --ingresos "2026-04:5000000,2026-03:4500000"
python main.py --workers 8

# Run file watcher (requires: pip install watchdog>=4.0.0)
python watcher.py

# Docker — desarrollo local completo (app + PostgreSQL + Adminer)
cp .env.example .env          # rellenar POSTGRES_PASSWORD y GROQ_API_KEY
docker-compose up --build     # primera vez (~3 min)
docker-compose up             # siguientes veces
docker-compose down -v        # destruir incluyendo volumen postgres

# URLs locales Docker
#   App:     http://localhost:8501
#   Adminer: http://localhost:8080  (Server: db, User: taxops)

# Run tests
python -m pytest
python -m pytest tests/test_extractor.py tests/test_validator.py tests/test_prorateo.py tests/test_chatbot.py
python -m pytest tests/test_e2e.py -v    # requiere PDFs en facturas/
python -m pytest --cov=. --cov-report=term-missing
```

## Architecture

TaxOps procesa facturas electrónicas DIAN (PDF/XML) colombianas en un pipeline:
`facturas/` → `extractor.py` → `validator.py` → `prorateo.py` → `excel_writer.py` / PostgreSQL

**Stack:** Streamlit multi-página · PostgreSQL 16 · SQLAlchemy · Groq/OpenAI/Anthropic/Google · Docker

### Module responsibilities

- **`extractor.py`** — Parsing de documentos. `extract_one(path)` es el entry point principal (thread-safe). Despacha a `extract_xml()` o `extract_pdf()` por extensión. XML tiene prioridad cuando coexisten ambos. Carga `autorretenedores.txt` al inicio como frozenset O(1). Fallback de fecha desde nombre de carpeta (`_date_from_folder`).

- **`validator.py`** — Validación stateless sobre DataFrame. `validate()` agrega columnas `validacion` (OK/ERROR) y `observacion`. Verifica: formato CUFE/CUDE (96 hex), duplicados, formato NIT, subtotal+IVA≈total (tolerancia $1 COP), campos obligatorios vacíos, mandato/peaje con IVA.

- **`prorateo.py`** — Prorrateo IVA Art. 490 E.T. `calcular_prorateo()` recibe dicts `{YYYY-MM: float}` para gravados/excluidos. Mandatos siempre van a no-deducible. Notas Crédito tienen signo negativo → reducen automáticamente el mes. `calcular_prorateo_simple()` retorna 100% deducible con columna de advertencia.

- **`excel_writer.py`** — Escribe el workbook de 3 hojas (BASE_DATOS, VALIDACION, PRORRATEO_IVA). Colores en VALIDACION: rojo=ERROR, verde=OK. Columnas de dinero con formato `#,##0.00`.

- **`main.py`** — CLI via `argparse`. Deduplica pares PDF/XML en `_resolver_archivos()` antes del paralelismo. Procesa con `ThreadPoolExecutor`. Log por archivo; progreso cada 50 archivos.

- **`watcher.py`** — Watcher local con `watchdog` (no incluido en requirements.txt cloud). Monitorea `facturas/` recursivamente. Debounce: 10s. Espera 5s al detectar nuevo archivo. Requiere `pip install watchdog>=4.0.0`.

- **`Home.py`** — Landing page TaxOps. Usa `utils/theme.py` para Dark/Light/System. Botones CTA con `st.switch_page()`.

- **`services/processor.py`** — Orquestación UI-agnóstica: extracción → validación → prorrateo → insert DB. `procesar()` devuelve `ResultadoProcesamiento` con los 3 DataFrames. Integra `db/database.py` para deduplicación por CUFE.

- **`services/chatbot.py`** — Accounting Assistant multi-provider. Soporta Groq, OpenAI, Anthropic, Google. Selección dinámica de modelo. Tool use: `consultar_iva_mes`, `top_proveedores`, `buscar_factura`, `resumen_errores`, `resumen_general`.

- **`utils/theme.py`** — Sistema de temas Dark/Light/System. `apply_theme()` inyecta CSS. `theme_selector()` muestra el radio en sidebar. Paletas `_DARK` / `_LIGHT` con tokens de color TaxOps.

- **`db/database.py`** — Capa SQLAlchemy UI-agnóstica. `db_available()` para degraded mode. `get_existing_cufes(org_id)` para deduplicación incremental. `insert_invoices_batch()` con `ON CONFLICT DO NOTHING`. `get_autorretenedores_nits()` desde DB con fallback a `autorretenedores.txt`.

- **`db/init.sql`** — Schema PostgreSQL multi-tenant: `organizations`, `users`, `clients`, `invoices`, `processing_sessions`, `autorretenedores`, `ingresos_prorateo`. UUID como PK, índices GIN trigram en campos de búsqueda.

- **`autorretenedores.txt`** — 3.287 NITs DIAN (corte 25/02/2026). Cargado al inicio de `extractor.py`. Para actualizar: reemplazar por nuevo archivo NIT-por-línea. En producción se carga desde tabla `autorretenedores` de PostgreSQL.

- **`static/favicon.svg`** — Favicon inline SVG con logo TaxOps (Tax naranja + Ops azul marino).

### Data flow

```
PDF/XML → extract_one() → dict plano
                              ↓
                         validate(df) → df + validacion/observacion
                              ↓
                    calcular_prorateo(df, ingresos) → df_pror
                              ↓
              insert_invoices_batch() → PostgreSQL (ON CONFLICT DO NOTHING)
                              ↓
                    ResultadoProcesamiento → Streamlit UI / Excel
```

### Document types

| Type | Detection | Sign | IVA |
|---|---|---|---|
| `Nota Crédito` | "nota cr", stem `NC-*` | -1 | resta del mes |
| `Nota Débito` | "nota déb/deb", stem `ND-*` | +1 | suma al mes |
| `Mandato/Peaje` | "mandato", "peaje" | +1 | siempre no-deducible |
| `Documento Soporte` | "documento soporte" | +1 | normal |
| `Documento Equivalente` | "documento equivalente" | +1 | normal |
| `Factura Electrónica` | default | +1 | normal |

### Documento Equivalente — two sub-layouts

**POS layout** (e.g. SUPERMERCADO EL CAMPESINO): sección `"Datos del vendedor"` presente. Folio alfanumérico `POSE5217`. NIT emisor en sección vendedor.

**SPD layout** (e.g. EPM — prefijo DEE): sección `"Datos del emisor"` estándar. Detectado por ausencia de `"Datos del vendedor"`.

Distinción en runtime: `tiene_vendedor = bool(re.search(r'datos\s+del\s+vendedor', text, re.I))`.

### Multi-tenant DB schema

```
organizations (UUID, plan: free/starter/pro)
    └── users (role: owner/admin/contador)
    └── clients (empresas que gestiona cada contador)
    └── invoices (CUFE único por org — deduplicación automática)
    └── processing_sessions (historial de cargas con métricas)
    └── ingresos_prorateo (persiste ingresos por período)
autorretenedores (reemplaza autorretenedores.txt en producción)
```

### Key regex patterns

```python
_RE_FOLIO          # "Número de Factura:" — facturas y notas
_RE_FOLIO_DOC      # "Número de documento: [A-Za-z]..." — doc equivalente/soporte
_RE_EMISOR_NIT     # "Nit del Emisor:"
_RE_EMISOR_NOMBRE  # "Razón Social:" (primera ocurrencia = emisor)
_RE_VENDEDOR_NIT   # "Datos del vendedor ... Número de documento:" (POS)
_RE_RECEPTOR_NIT   # "Número Documento:" or "nit del adquir..."
_RE_ADQUIRIENTE_NIT # "NIT del adquiriente:" (POS)
```

Bug crítico resuelto: `_search_money_near(text, "IVA", line_start=True)` — requiere IVA al inicio de línea para no capturar números de calle en `"Dirección: CALLE 26"`.

### Tests

```
tests/
├── test_extractor.py   # 44 unit tests — funciones puras + mocked PDF
├── test_validator.py   # 19 unit tests — reglas de validación
├── test_prorateo.py    # 12 unit tests — Art. 490 ET
├── test_chatbot.py     # 11 unit tests — sin llamar API real
└── test_e2e.py         # 32 end-to-end (se saltan si no hay PDFs)
```

### SaaS gaps (próximos pasos)

- **Auth**: cero autenticación — bloqueante para producción
- **Multi-tenant enforcement**: schema listo, app no aplica `org_id`
- **Alembic**: no hay sistema de migraciones
- **Rate limiting**: sin throttling por organización
- **FastAPI**: `services/processor.py` ya es UI-agnóstico, listo para `POST /v1/procesar`

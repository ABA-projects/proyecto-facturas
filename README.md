# Facturas DIAN — Automatización Contable Colombia

Procesa facturas electrónicas DIAN (PDF/XML), valida, calcula prorrateo de IVA y te da un asistente contable inteligente para consultarlas en lenguaje natural.

---

## Inicio rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar API key de Groq (gratis en console.groq.com)
#    Editar .streamlit/secrets.toml y reemplazar el placeholder
#    GROQ_API_KEY = "gsk_tu_clave_aqui"

# 3. Abrir la app web
python3 -m streamlit run Home.py
```

Abre `http://localhost:8501` — landing page con acceso a todas las funciones.

---

## Modos de uso

### App web (recomendado)

```bash
python3 -m streamlit run Home.py
```

Multi-página con landing, procesamiento, visualización y chatbot contable. Desplegable en Streamlit Community Cloud (gratis).

### CLI con procesamiento paralelo

```bash
python main.py
python main.py --carpeta /ruta/facturas --ingresos "2026-04:5000000,2026-03:4500000" --workers 8
```

`--workers`: hilos paralelos (default: `min(8, CPUs)`). Para 800 facturas reduce de ~7 min a ~1-2 min.

### Disparador automático (watcher)

```bash
python watcher.py
python watcher.py --carpeta /ruta/facturas --ingresos "2026-04:5000000"
```

Monitorea la carpeta `facturas/` con watchdog. Cada vez que copias un archivo, genera el Excel automáticamente. Debounce de 10s para lotes.

---

## Estructura del proyecto

```
proyecto-facturas/
│
├── Home.py                    ← Landing page (entry point de la app web)
├── pages/
│   ├── 1_Procesar.py          ← Upload/carpeta + progreso + descarga Excel
│   ├── 2_Base_Datos.py        ← Tabla con búsqueda y filtro por tipo
│   ├── 3_Validacion.py        ← Errores contables con colores OK/ERROR
│   ├── 4_Prorrateo_IVA.py     ← Cálculo Art. 490 ET por mes
│   └── 5_Chatbot.py           ← Accounting Assistant
│
├── services/
│   ├── processor.py           ← Orquestación UI-agnóstica (extracción → validación → prorrateo)
│   └── chatbot.py             ← Accounting Assistant (Groq llama-3.3-70b, tool use)
│
├── extractor.py               ← Extracción PDF + XML (INTACTO)
├── validator.py               ← Validaciones DIAN: CUFE, NITs, cuadre contable (INTACTO)
├── prorateo.py                ← Prorrateo IVA Art. 490 ET (INTACTO)
├── excel_writer.py            ← Excel 3 hojas con formato (INTACTO)
├── main.py                    ← CLI con argparse + ThreadPoolExecutor (INTACTO)
├── watcher.py                 ← File watcher con watchdog (INTACTO)
├── app.py                     ← App Streamlit original (INTACTO, sigue funcionando)
│
├── autorretenedores.txt       ← 3.287 NITs DIAN (corte 25/02/2026)
├── requirements.txt
├── .streamlit/
│   ├── config.toml            ← Tema pastel + límite upload 200 MB
│   └── secrets.toml           ← API keys locales (en .gitignore, nunca a GitHub)
│
├── docs/
│   ├── guia-groq-api.md       ← Cómo obtener y configurar la API key de Groq
│   └── guia-streamlit-cloud.md ← Deploy paso a paso en Streamlit Community Cloud
│
├── tests/
│   ├── test_extractor.py      ← 44 tests unitarios
│   ├── test_validator.py      ← 19 tests unitarios
│   ├── test_prorateo.py       ← 12 tests unitarios
│   ├── test_chatbot.py        ← 11 tests unitarios (sin llamar API real)
│   └── test_e2e.py            ← 32 tests end-to-end (requieren PDFs en facturas/)
└── pytest.ini
```

---

## Chatbot — Accounting Assistant

Asistente contable colombiano disponible sin necesidad de procesar facturas primero.

**Sin facturas cargadas** — responde preguntas generales:
- ¿Qué es el prorrateo de IVA Art. 490 ET?
- ¿Cuándo aplica retención en la fuente?
- ¿Cuál es la diferencia entre CUFE y CUDE?

**Con facturas procesadas** — además consulta tus datos:
- ¿Cuánto IVA pagué en marzo?
- ¿Cuáles son mis 5 mayores proveedores?
- ¿Qué facturas tienen errores?
- Buscar factura por folio o NIT

**Motor:** Groq llama-3.3-70b — gratuito, sin límite de sesión, API key en `.streamlit/secrets.toml`.

**Herramientas (tool use):** `consultar_iva_mes`, `top_proveedores`, `buscar_factura`, `resumen_errores`, `resumen_general`. Extensibles en `services/chatbot.py` sin tocar la UI.

---

## Configuración API Key (Groq)

1. Crear cuenta gratis en [console.groq.com](https://console.groq.com) → API Keys
2. Editar `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_tu_clave_aqui"
```

El archivo ya está en `.gitignore` — nunca se sube a GitHub.
Ver guía completa en `docs/guia-groq-api.md`.

---

## Deploy en la nube (Streamlit Community Cloud)

Gratis, dominio `tuapp.streamlit.app`, redespliega con cada `git push`.

1. Ir a [share.streamlit.io](https://share.streamlit.io) → "New app"
2. Seleccionar repo → branch `main` → archivo `Home.py`
3. En "Advanced settings" → Secrets: `GROQ_API_KEY = "gsk_..."`
4. Deploy → URL pública en ~2 min

Ver guía completa en `docs/guia-streamlit-cloud.md`.

---

## Organización de facturas

```
facturas/
├── 2026-03/           ← fecha tomada del nombre de carpeta si el doc no tiene fecha
│   ├── FE-001.pdf
│   └── FE-002.xml
├── 2026-04/
│   └── FE-100.xml
└── FE-999.pdf         ← archivos en raíz también se procesan
```

- Si existe XML y PDF con el mismo nombre → **se usa siempre el XML**
- Deduplicación por ruta completa antes del procesamiento paralelo

---

## Excel de salida

| Hoja | Contenido |
|------|-----------|
| `BASE_DATOS` | Un registro por factura con todos los campos contables |
| `VALIDACION` | Estado OK/ERROR con observación detallada. Celdas coloreadas (rojo/verde) |
| `PRORRATEO_IVA` | IVA agrupado por mes con % de prorrateo Art. 490 ET aplicado |

### Campos BASE_DATOS

| Campo | Descripción |
|-------|-------------|
| `tipo` | Factura Electrónica / Nota Crédito / Nota Débito / Mandato/Peaje / Documento Soporte / Documento Equivalente |
| `cufe` | Código único DIAN — 96 caracteres hex |
| `folio` | Número de factura (FE-001, STK-602558, POSE5217…) |
| `fecha` | Fecha de emisión YYYY-MM-DD |
| `nit_emisor` / `nombre_emisor` | NIT y razón social del proveedor |
| `nit_receptor` / `nombre_receptor` | NIT y razón social del comprador |
| `subtotal` | Total Bruto Factura (base después de descuentos) |
| `base_iva_19` / `iva_19` | Base e impuesto IVA 19% |
| `base_iva_5` / `iva_5` | Base e impuesto IVA 5% |
| `no_gravado` | Porción del subtotal sin IVA |
| `total` | Total a pagar |
| `retencion_fuente` | Retención calculada (subtotal × 2.5%, cero si autorretenedor) |
| `fuente` | PDF o XML |

> `validacion` y `observacion` solo aparecen en la hoja VALIDACION, no en BASE_DATOS.

---

## Tipos de documento

| Tipo | Detección | Signo | Retención | IVA prorrateo |
|------|-----------|-------|-----------|---------------|
| Factura Electrónica | por defecto | +1 | 2.5% | base normal |
| Nota Crédito | "nota cr", `NC-*.pdf` | -1 | 0 | resta del mes |
| Nota Débito | "nota déb/deb", `ND-*.pdf` | +1 | 2.5% | suma al mes |
| Mandato/Peaje | "mandato", "peaje" | +1 | 2.5% | **no descontable** |
| Documento Soporte | "documento soporte" | +1 | 2.5% | base normal |
| Documento Equivalente | "documento equivalente" | +1 | 2.5% | base normal |

---

## Prorrateo IVA — Art. 490 E.T.

```
% deducible = ingresos_gravados / (ingresos_gravados + ingresos_excluidos)
IVA descontable = IVA_compras × % deducible
```

- Sin ingresos informados → 100% deducible con advertencia en la hoja
- Mandatos → siempre IVA no descontable, independiente del prorrateo
- Notas Crédito → valores negativos que reducen automáticamente el total del mes

---

## Retención en la Fuente

```
retencion_fuente = subtotal × 2.5%
```

- Cero si el NIT emisor está en `autorretenedores.txt` (3.287 NITs, corte 25/02/2026)
- Cero para Notas Crédito
- Para actualizar autorretenedores: reemplazar el archivo con un NIT por línea

---

## Pruebas

```bash
# Todas las pruebas
python3 -m pytest

# Solo unitarias (sin PDFs — siempre disponibles)
python3 -m pytest tests/test_extractor.py tests/test_validator.py tests/test_prorateo.py tests/test_chatbot.py

# End-to-end (requiere PDFs en facturas/)
python3 -m pytest tests/test_e2e.py -v

# Con cobertura
python3 -m pytest --cov=. --cov-report=term-missing
```

| Suite | Tests | Requiere PDFs |
|-------|-------|---------------|
| `test_extractor.py` | 44 | No (mock pdfplumber) |
| `test_validator.py` | 19 | No |
| `test_prorateo.py` | 12 | No |
| `test_chatbot.py` | 11 | No (mock DataFrame, sin API) |
| `test_e2e.py` | 32 | Sí (se saltan si no están) |

---

## Normativa aplicada

| Norma | Aplicación |
|-------|-----------|
| Art. 490 ET | Prorrateo IVA ingresos gravados/excluidos |
| Art. 771-2 ET | Requisitos para IVA descontable |
| Resolución DIAN 000042/2020 | Facturación electrónica — formato UBL 2.1 |
| Decreto 358/2020 | Sistema de facturación |

---

## Roadmap

- [x] Extracción PDF/XML (UBL 2.1)
- [x] Validación CUFE, cuadre contable, duplicados
- [x] Prorrateo IVA Art. 490 ET
- [x] Excel 3 hojas con formato
- [x] CLI + paralelismo + watcher
- [x] App web multi-página con landing page
- [x] Chatbot contable (Groq, gratuito, tool use)
- [x] Capa `services/` UI-agnóstica (lista para FastAPI)
- [ ] Tests con 10+ emisores reales (Claro, Movistar, EPM, peajes)
- [ ] Procesamiento incremental (SQLite, no reprocesar CUFEs ya procesados)
- [ ] Integración IMAP (descarga automática desde correo)
- [ ] FastAPI endpoint `POST /procesar` sobre `services/processor.py`

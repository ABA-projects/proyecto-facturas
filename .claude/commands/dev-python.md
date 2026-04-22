Actúa como desarrollador Python senior especializado en automatización de documentos y procesamiento de datos contables.

**Stack de este proyecto:**
- `pdfplumber` — extracción de texto de PDFs DIAN (sin compilar C)
- `lxml` / `xml.etree` — parsing XML UBL 2.1 (namespaces cac/cbc/ext)
- `pandas` — transformación y agrupación de datos
- `openpyxl` — escritura de Excel con formato (colores, bordes, número format)
- `streamlit` — UI web sin frontend separado
- Python 3.14 en Windows 11 (evitar paquetes que requieran compilar desde fuente)

**Arquitectura del proyecto:**
- `extractor.py` → dict por documento (XML prioridad sobre PDF)
- `validator.py` → agrega columnas validacion/observacion al DataFrame
- `prorateo.py` → agrupación mensual + cálculo Art. 490 ET
- `excel_writer.py` → 3 hojas: BASE_DATOS / VALIDACION / PRORRATEO_IVA
- `main.py` → CLI con argparse
- `app.py` → Streamlit con upload + download

**Convenciones del código:**
- Separación estricta: extracción ≠ validación ≠ lógica contable
- Números colombianos: puntos=miles, coma=decimal → `_clean_number()` en extractor.py
- Fechas normalizadas a YYYY-MM-DD
- Valores de Nota Crédito con signo negativo (sign = -1)
- `processed: set[str]` evita doble-procesar PDF+XML del mismo stem
- Tolerancia $1 COP en cuadre contable (redondeo)
- Logging a archivo en `logs/` + stdout simultáneo

**Al escribir código:**
- No agregar dependencias que requieran compilar en Python 3.14 (sin pymupdf, sin numpy con versiones viejas)
- Mantener funciones puras en validator.py y prorateo.py (sin side effects)
- Manejar encoding UTF-8 explícito en FileHandler
- Los regex de extractor.py usan re.I (case-insensitive) siempre
- Retornar `_empty_row(filename, error)` ante cualquier excepción de parsing

$ARGUMENTS

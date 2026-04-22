Actúa como desarrollador backend especializado en pipelines de procesamiento de documentos y automatización contable.

**Responsabilidades backend en este proyecto:**
- Pipeline: ingesta de archivos → extracción → validación → transformación → salida Excel
- Manejo de errores robusto: un PDF fallido no detiene el lote completo
- Deduplicación por stem de archivo (`processed: set[str]`) y por CUFE
- Logging estructurado: archivo rotativo en `logs/` + stdout

**Módulos core:**
- `extractor.py` — I/O de archivos, parsing XML/PDF, normalización de datos
- `validator.py` — reglas de negocio contables sobre DataFrame completo
- `prorateo.py` — agregaciones mensuales y cálculo Art. 490 ET
- `excel_writer.py` — serialización a XLSX con openpyxl

**Patrones establecidos:**
- Cada documento retorna un dict con claves fijas (nunca KeyError downstream)
- `_empty_row(filename, error)` como fallback ante cualquier excepción
- Signo negativo en Nota Crédito aplicado en el extractor (no en el validador)
- Tolerancia monetaria: abs(calculado - total) <= 1.0 COP
- Fechas: siempre YYYY-MM-DD internamente; mes agrupado como YYYY-MM

**Extensiones futuras a considerar:**
- Procesamiento incremental: guardar CUFE procesados en SQLite para no reprocesar
- Watcher de carpeta: `watchdog` para procesar automáticamente nuevos archivos
- API REST: FastAPI wrapping los mismos módulos para integración con otros sistemas
- Descarga automática DIAN: requeriría Selenium + credenciales (manejar con cuidado)

**Al modificar el pipeline:**
- No romper el contrato del dict de salida de extractor.py (las claves son fijas)
- Los módulos validator.py y prorateo.py deben ser stateless (solo reciben DataFrame)
- main.py es el único lugar con side effects de I/O de archivos (logs, output/)
- app.py replica la lógica de main.py pero sin tocar el filesystem principal

$ARGUMENTS

# Sistema de Gestión de Facturas Electrónicas DIAN

Automatiza la extracción, validación y consolidación contable de facturas DIAN (PDF/XML) en un Excel estructurado con tres hojas: BASE_DATOS, VALIDACION y PRORRATEO_IVA.

---

## Instalación

```bash
pip install -r requirements.txt
```

---

## Modos de uso

### 1. Disparador automático (recomendado)

Deja corriendo el observador en una terminal. Cada vez que copies un PDF o XML a la carpeta `facturas/`, el sistema genera el Excel automáticamente.

```bash
python watcher.py

# Con ingresos para prorrateo real:
python watcher.py --ingresos "2026-04:5000000,2026-03:4500000"

# Carpeta personalizada:
python watcher.py --carpeta C:/mis-facturas
```

### 2. Procesamiento manual (CLI)

```bash
python main.py

# Con ingresos para prorrateo:
python main.py --ingresos "2026-04:5000000,2026-03:4500000"

# Carpeta personalizada y control de hilos paralelos:
python main.py --carpeta C:/mis-facturas --ingresos "2026-04:5000000" --workers 8
```

**Argumento `--workers`:** número de hilos paralelos para extracción (default: `min(8, CPUs)`). Para lotes grandes (~800 facturas) reduce el tiempo de ~7 min a ~1-2 min. Si los archivos están en OneDrive o red, usa `--workers 4` para no saturar la sync.

### 3. Dashboard visual (Streamlit)

```bash
python -m streamlit run app.py
```

Abre `http://localhost:8501` en el navegador. Permite subir archivos, ver métricas y descargar el Excel.

> **Nota Windows:** si `streamlit` no se reconoce como comando, usa siempre `python -m streamlit run app.py`.

---

## Organización de facturas por fecha

La carpeta `facturas/` soporta subcarpetas. Puedes organizarlas por mes o por fecha:

```
facturas/
├── 2026-03/
│   ├── FE-001.pdf
│   └── FE-002.xml
├── 2026-04/
│   ├── FE-100.pdf
│   └── NC-005.pdf
└── FE-999.pdf       <- también se procesan archivos en la raíz
```

Si una factura no tiene fecha reconocible en su contenido, el sistema toma la fecha del nombre de la carpeta que la contiene (ej. `2026-03/` -> `2026-03-01`).

Si existe un par PDF+XML con el mismo nombre, **se usa siempre el XML** (más confiable). La deduplicación ocurre en el escaneo inicial, antes del procesamiento paralelo.

---

## Estructura del proyecto

```
proyecto-facturas/
├── facturas/                  <- PDFs/XMLs descargados de la DIAN (en .gitignore)
├── output/                    <- Excels generados automáticamente (en .gitignore)
├── logs/                      <- Log de cada ejecución (en .gitignore)
├── autorretenedores.txt       <- NITs autorretenedores DIAN (corte 25/02/2026)
├── extractor.py               <- Extracción de datos (PDF + XML)
├── validator.py               <- Validaciones DIAN (CUFE, NITs, cuadre contable)
├── prorateo.py                <- Cálculo de prorrateo IVA (Art. 490 ET)
├── excel_writer.py            <- Generación del Excel con formato
├── main.py                    <- CLI principal con procesamiento paralelo
├── watcher.py                 <- Disparador automático (watchdog)
├── app.py                     <- Dashboard Streamlit
├── requirements.txt
├── pytest.ini
└── tests/
    ├── test_extractor.py      <- Pruebas unitarias de extracción
    ├── test_validator.py      <- Pruebas unitarias de validación
    ├── test_prorateo.py       <- Pruebas unitarias de prorrateo
    └── test_e2e.py            <- Pruebas end-to-end con PDFs reales
```

---

## Salida Excel

| Hoja | Contenido |
|---|---|
| `BASE_DATOS` | Un registro por factura con todos los campos contables |
| `VALIDACION` | Estado OK/ERROR con observación detallada por documento |
| `PRORRATEO_IVA` | IVA agrupado por mes con porcentaje de prorrateo aplicado |

---

## Campos en BASE_DATOS

| Campo | Descripción |
|---|---|
| `tipo` | Factura Electrónica / Nota Crédito / Mandato/Peaje / Documento Soporte |
| `cufe` | Código único de 96 hex chars |
| `folio` | Número de factura (FE-001, STK-602558, etc.) |
| `fecha` | Fecha de emisión (YYYY-MM-DD) |
| `nit_emisor` | NIT del proveedor |
| `nombre_emisor` | Razón social del proveedor |
| `nit_receptor` | NIT del comprador |
| `nombre_receptor` | Razón social del comprador |
| `subtotal` | Total Bruto Factura (base después de descuentos de línea) |
| `base_iva_19` | Base gravada al 19% |
| `iva_19` | Impuesto IVA al 19% |
| `base_iva_5` | Base gravada al 5% |
| `iva_5` | Impuesto IVA al 5% |
| `no_gravado` | Porción del subtotal sin IVA (exenta o excluida) |
| `total` | Total factura a pagar |
| `retencion_fuente` | Retención en la fuente calculada (subtotal x 2.5%) |
| `fuente` | PDF o XML |

> `validacion` y `observacion` NO aparecen en BASE_DATOS — solo en la hoja VALIDACION.

---

## Retención en la Fuente

```
retencion_fuente = subtotal x 2.5%
```

- **Autorretenedores:** retención = 0 (exonerados por resolución DIAN).
- El listado se carga de `autorretenedores.txt` (3.287 NITs, corte 25/02/2026).
- Para actualizar: reemplaza `autorretenedores.txt` con un nuevo archivo de un NIT por línea.

---

## Bases de IVA y No Gravado

```
base_iva_19 = iva_19 / 19%   (back-calculado; XML usa TaxableAmount exacto)
base_iva_5  = iva_5  / 5%
no_gravado  = subtotal - base_iva_19 - base_iva_5
```

Ejemplo:
- Tiquetes aéreos, seguros (IVA = 0): `no_gravado = subtotal`
- Factura con IVA 19% sobre toda la base: `base_iva_19 = subtotal`, `no_gravado = 0`

---

## Lógica de extracción de montos (PDF)

**Subtotal** (= Total Bruto Factura/Documento):
1. `Total Bruto Factura` — facturas y notas
2. `Total bruto documento` — documentos equivalentes y soporte
3. `Base gravable` / `Base imponible`
4. `Subtotal` — fallback (antes de descuentos, puede diferir)

**IVA por tasa** (estrategia en dos pasos):
1. Líneas de detalle de productos — acumula `{monto_iva} 19.00` y `{monto_iva} 5.00` por separado (más preciso, maneja IVA mixto)
2. Si no hay coincidencias: totales resumen (`IVA 19%`, `IVA` al inicio de línea, `Total IVA`)

> El IVA al inicio de línea evita capturar números de calle de `"Responsabilidad tributaria: 01 - IVA Dirección: CALLE 26"`.

**Total:**
1. `Total factura` — facturas y notas (maneja `(=)`, espacios unicode U+3164, `COP $`)
2. `Total documento` — documentos equivalentes y soporte
3. `Total neto factura` / `Total neto documento`
4. `Total a pagar` / `Valor total`

---

## Tipos de documento

| Tipo | Detección | Sign | Retención | IVA prorrateo |
|---|---|---|---|---|
| Factura Electrónica | por defecto | +1 | 2.5% | base normal |
| Nota Crédito | "nota cr", `NC-*.pdf` | -1 | 0 | resta del mes |
| Nota Débito | "nota déb/deb", `ND-*.pdf` | +1 | 2.5% | suma al mes |
| Mandato/Peaje | "mandato", "peaje" | +1 | 2.5% | no descontable |
| Documento Soporte | "documento soporte" | +1 | 2.5% | base normal |
| Documento Equivalente | "documento equivalente" | +1 | 2.5% | base normal |

### Layouts de Documento Equivalente

| Layout | Ejemplo | Folio | Sección emisor |
|---|---|---|---|
| POS (punto de venta) | Supermercado `POSE5217` | `Número de documento:` | `Datos del vendedor` |
| SPD (servicios públicos) | EPM `DEE46098616` | `Número de documento:` | `Datos del emisor` |

El folio siempre empieza con letras (POSE, DEE, etc.), lo que lo distingue del NIT del vendedor (solo dígitos).

---

## Prorrateo de IVA (Art. 490 E.T.)

```
% prorrateo = ingresos_gravados / (ingresos_gravados + ingresos_excluidos)
IVA descontable = IVA_base x % prorrateo
```

- Sin ingresos -> prorrateo al 100% con advertencia en la hoja.
- Mandatos van directo a IVA no descontable.
- Notas Crédito reducen automáticamente los totales del mes.

---

## Pruebas

```bash
# Todas las pruebas
python -m pytest

# Solo unitarias (sin PDFs reales — siempre disponibles)
python -m pytest tests/test_extractor.py tests/test_validator.py tests/test_prorateo.py

# End-to-end (requiere PDFs en facturas/)
python -m pytest tests/test_e2e.py -v

# Con cobertura
python -m pytest --cov=. --cov-report=term-missing
```

Las pruebas E2E se saltan automáticamente si los PDFs no están en `facturas/` (están en `.gitignore`). Las pruebas unitarias no requieren archivos reales.

| Suite | Tests | Requiere PDFs |
|---|---|---|
| `test_extractor.py` | 32 | No (mock pdfplumber) |
| `test_validator.py` | 19 | No |
| `test_prorateo.py` | 12 | No |
| `test_e2e.py` | 25 | Si (se saltan si no están) |

---

## Prioridad XML sobre PDF

Si existe XML y PDF con el mismo nombre -> **se usa el XML** (más confiable).
Si solo hay PDF -> extracción por regex sobre el texto del documento.

---

## Ejemplo de ejecución (lote grande)

```
Procesando 800 documentos con 8 workers...
  50/800 (6%) — 0 errores
  100/800 (12%) — 1 errores
  ...
  800/800 (100%) — 3 errores
Validacion: 797 OK | 3 ERROR de cuadre contable

Listo: output/facturas_20260428_142301.xlsx
```

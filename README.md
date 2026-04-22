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

Deja corriendo el observador en una terminal. Cada vez que copies un PDF o XML a la carpeta `facturas/` (o a cualquier subcarpeta), el sistema genera el Excel automáticamente.

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

# Carpeta personalizada:
python main.py --carpeta C:/mis-facturas --ingresos "2026-04:5000000"
```

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
└── FE-999.pdf       ← también se procesan archivos en la raíz
```

Si una factura no tiene fecha reconocible en su contenido, el sistema toma la fecha del nombre de la carpeta que la contiene (ej. `2026-03/` → `2026-03-01`).

El campo `archivo` en el Excel mostrará la ruta relativa (`2026-03/FE-001.pdf`) para identificar el origen.

---

## Estructura del proyecto

```
proyecto-facturas/
├── facturas/          ← PDFs/XMLs descargados de la DIAN (soporta subcarpetas)
├── output/            ← Excels generados automáticamente
├── logs/              ← Log de cada ejecución
├── extractor.py       ← Extracción de datos (PDF + XML)
├── validator.py       ← Validaciones DIAN (CUFE, NITs, cuadre contable)
├── prorateo.py        ← Cálculo de prorrateo IVA (Art. 490 ET)
├── excel_writer.py    ← Generación del Excel con formato
├── main.py            ← CLI principal
├── watcher.py         ← Disparador automático (watchdog)
├── app.py             ← Dashboard Streamlit
└── requirements.txt
```

---

## Salida Excel

| Hoja | Contenido |
|---|---|
| `BASE_DATOS` | Un registro por factura: archivo, tipo, CUFE, folio, fecha, emisor, receptor, montos |
| `VALIDACION` | Estado OK/ERROR con observación detallada por documento |
| `PRORRATEO_IVA` | IVA agrupado por mes con porcentaje de prorrateo aplicado |

---

## Campos extraídos (BASE_DATOS)

| Campo | Fuente PDF | Fuente XML |
|---|---|---|
| `folio` | "Número de Factura: FE-001" | `cbc:ID` |
| `nit_emisor` | "Nit del Emisor: 123456" | `AccountingSupplierParty/.../CompanyID` |
| `nombre_emisor` | "Razón Social: ..." | `PartyLegalEntity/RegistrationName` |
| `nit_receptor` | "Número Documento: 9010..." | `AccountingCustomerParty/.../CompanyID` |
| `nombre_receptor` | "Nombre o Razón Social: ..." | `PartyLegalEntity/RegistrationName` |
| `fecha` | "Fecha de Emisión: 24/03/2026" | `cbc:IssueDate` |
| `cufe` | "CUFE: abc123..." (96 hex) | `cbc:UUID` |
| `subtotal` | "Total Bruto Factura" (después de descuentos) | `LegalMonetaryTotal/TaxExclusiveAmount` |
| `iva_19` | "IVA 19% …" o línea "IVA …" del resumen | `TaxTotal` con `Percent = 19` |
| `iva_5` | "IVA 5% …" del resumen | `TaxTotal` con `Percent = 5` |
| `total` | "Total factura (=) COP $ …" | `LegalMonetaryTotal/PayableAmount` |

### Lógica de extracción de montos (PDF)

El extractor busca los campos en este orden de prioridad:

**Subtotal** (base gravable para IVA):
1. `Total Bruto Factura` — suma después de descuentos de línea, antes de impuestos ✓
2. `Base gravable` / `Base imponible`
3. `Subtotal` — fallback (es la suma bruta *antes* de descuentos; puede diferir)

**IVA 19%:**
1. `IVA 19%` — cuando aparece con el porcentaje explícito
2. `Impuesto 19`
3. `IVA` — línea del resumen de totales (sin porcentaje)

**Total:**
1. `Total factura` — maneja prefijos `(=)`, espacios unicode y `COP $`
2. `Total neto factura`
3. `Total a pagar` / `Valor total`

> El cuadre contable es: `subtotal + iva_19 + iva_5 = total` (tolerancia ±$1 COP).

---

## Tipos de documento

| Tipo | Detección | Tratamiento |
|---|---|---|
| Factura Electrónica | Por defecto | Valores positivos, IVA sujeto a prorrateo |
| Nota Crédito | "nota cr" en texto/nombre | Valores negativos (restan del mes) |
| Mandato/Peaje | "mandato" o "peaje" en texto | IVA siempre no descontable |
| Documento Soporte | "documento soporte" en texto | Igual que Factura Electrónica |

---

## Prorrateo de IVA (Art. 490 E.T.)

```
% prorrateo = ingresos_gravados / (ingresos_gravados + ingresos_excluidos)
IVA descontable = IVA_base × % prorrateo
```

- Si no se ingresan ingresos → prorrateo al 100% con advertencia en la hoja.
- Mandatos van directo a IVA no descontable sin importar el prorrateo.
- Las Notas Crédito reducen automáticamente los totales del mes correspondiente.

---

## Prioridad de extracción

Si existe XML y PDF con el mismo nombre → **se usa el XML** (más confiable).  
Si solo hay PDF → extracción por regex sobre el texto del documento.

---

## Ejemplo de ejecución

```
2026-04-21 10:00:00 [INFO] Procesando carpeta: facturas
2026-04-21 10:00:01 [INFO] OK  FE-174769.pdf → Factura Electrónica | Total: 1191999.83
2026-04-21 10:00:02 [INFO] OK  NC-0001.pdf → Nota Crédito | Total: -119000.0
2026-04-21 10:00:03 [INFO] Validación: 2 OK | 0 ERROR
2026-04-21 10:00:03 [INFO] Excel generado: output/facturas_20260421_100003.xlsx
```

```
2026-04-21 10:05:00 [WATCHER] Observando facturas/ (Ctrl+C para detener)...
2026-04-21 10:07:14 [WATCHER] Nuevo archivo detectado: FE-200.pdf — esperando 5s...
2026-04-21 10:07:19 [WATCHER] Excel generado: output/facturas_20260421_100719.xlsx
```

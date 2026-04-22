# Sistema de Gestión de Facturas Electrónicas DIAN

Automatiza la extracción, validación y consolidación contable de facturas DIAN en un Excel estructurado.

---

## Instalación

```bash
pip install -r requirements.txt
```

---

## Uso

### Modo CLI (recomendado para producción)

```bash
# 1. Poner PDFs/XMLs en la carpeta facturas/
# 2. Ejecutar:
python main.py

# Con ingresos para prorrateo real:
python main.py --ingresos "2026-04:5000000,2026-03:4500000"

# Carpeta personalizada:
python main.py --carpeta C:/mis-facturas --ingresos "2026-04:5000000"
```

### Modo Dashboard (Streamlit)

```bash
streamlit run app.py
```

Luego abre `http://localhost:8501` en el navegador.

---

## Estructura del proyecto

```
Poryecto-facturas/
├── facturas/          ← Poner aquí los PDF/XML descargados de la DIAN
├── output/            ← Excel generados automáticamente
├── logs/              ← Logs de cada ejecución
├── extractor.py       ← Extracción de datos (PDF + XML)
├── validator.py       ← Validaciones DIAN
├── prorateo.py        ← Cálculo de prorrateo de IVA (Art. 490 ET)
├── excel_writer.py    ← Generación del Excel con formato
├── main.py            ← Script principal (CLI)
├── app.py             ← Interfaz Streamlit
└── requirements.txt
```

---

## Salida Excel

| Hoja | Contenido |
|---|---|
| `BASE_DATOS` | Todos los documentos (1 fila por factura) |
| `VALIDACION` | Estado OK/ERROR por documento con observación |
| `PRORRATEO_IVA` | IVA agrupado por mes con % prorrateo |

---

## Prorrateo de IVA (Art. 490 E.T.)

```
% prorrateo = ingresos_gravados / (ingresos_gravados + ingresos_excluidos)
IVA descontable = IVA_total × % prorrateo
```

**Reglas especiales:**
- **Mandatos/Peajes**: IVA siempre NO descontable
- **Notas Crédito**: restan del acumulado del mes
- **Sin ingresos ingresados**: se muestra el IVA total con advertencia

---

## Tipos de documento soportados

| Tipo | Detección | Tratamiento IVA |
|---|---|---|
| Factura Electrónica | Por defecto | Sujeto a prorrateo |
| Nota Crédito | "nota cr" en texto/nombre | Valores negativos |
| Mandato/Peaje | "mandato" o "peaje" en texto | IVA no descontable |
| Documento Soporte | "documento soporte" en texto | Sujeto a prorrateo |

---

## Prioridad de extracción

Si existe un XML con el mismo nombre que el PDF → **se usa el XML** (más confiable).  
Si solo existe PDF → extracción por texto con regex.

---

## Ejemplo de ejecución

```
2026-04-21 10:00:00 [INFO] Procesando carpeta: facturas
2026-04-21 10:00:01 [INFO] OK  FE-1234.pdf → Factura Electrónica | Total: 1190000.0
2026-04-21 10:00:02 [INFO] OK  NC-0001.pdf → Nota Crédito | Total: -119000.0
2026-04-21 10:00:03 [INFO] Validación: 2 OK | 0 ERROR
2026-04-21 10:00:03 [INFO] Excel generado: output/facturas_20260421_100003.xlsx
```

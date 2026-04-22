Modo diagnóstico para facturas que no se extraen correctamente.

Dado un archivo PDF o XML problemático, sigue este proceso:

**Paso 1 — Identificar qué falló:**
- ¿El archivo se procesó? (buscar en logs/ la línea con el nombre del archivo)
- ¿Retornó _empty_row? (fuente empieza con "ERROR:")
- ¿Qué campos están vacíos: cufe, folio, fecha, nit_emisor?

**Paso 2 — Analizar el texto extraído del PDF:**
```python
import pdfplumber
with pdfplumber.open("facturas/archivo.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"=== Página {i+1} ===")
        print(page.extract_text())
```

**Paso 3 — Verificar qué capturan los regex actuales:**
```python
import re, extractor as ex
text = open("texto_extraido.txt").read()
print("CUFE:", ex._RE_CUFE.search(text))
print("CUDE:", ex._RE_CUDE.search(text))
print("NITs:", [m.group(1) for m in ex._RE_NIT.finditer(text)])
print("Fecha:", ex._RE_DATE.search(text))
print("Folio:", ex._RE_FOLIO.search(text))
print("Subtotal:", ex._search_money_near(text, "subtotal"))
print("IVA:", ex._search_money_near(text, "IVA 19%"))
print("Total:", ex._search_money_near(text, "total a pagar"))
```

**Paso 4 — Ajustar regex si el emisor tiene formato distinto:**
Emisores con formatos especiales conocidos:
- Claro/Movistar: CUFE en página 2, totales en tabla al final
- EPM: múltiples conceptos, IVA parcial por servicio
- Peajes Concesión: sin CUFE (mandato), NIT del mandante como receptor

**Paso 5 — Si es XML, verificar namespaces:**
```python
import xml.etree.ElementTree as ET
tree = ET.parse("facturas/archivo.xml")
root = tree.getroot()
print(root.tag)  # Debe contener Invoice o CreditNote
# Si el namespace es diferente, ajustar NS en extractor.py
```

**Reportar el fix:**
- Indicar qué regex o ruta XML se ajustó
- Documentar el emisor y el patrón especial en un comentario en extractor.py
- Agregar el caso al listado de QA en qa.md

$ARGUMENTS

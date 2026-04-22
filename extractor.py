"""Extracción de datos de facturas electrónicas DIAN (PDF y XML)."""

import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import xml.etree.ElementTree as ET

import pdfplumber

logger = logging.getLogger(__name__)

# ── Namespaces UBL usados por DIAN ─────────────────────────────────────────
NS = {
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
}

# ── Patrones regex para PDF ─────────────────────────────────────────────────
_RE_CUFE  = re.compile(r"CUFE[:\s]+([a-f0-9]{96})", re.I)
_RE_CUDE  = re.compile(r"CUDE[:\s]+([a-f0-9]{96})", re.I)
_RE_DATE  = re.compile(r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})")
_RE_MONEY = re.compile(r"[\$]?\s*([\d.,]+)")

# Folio: prioridad "Número de Factura:" (DIAN estándar), luego genérico
_RE_FOLIO = re.compile(
    r"n[uú]mero\s+de\s+(?:la\s+)?factura\s*[:\s]+([A-Z0-9][A-Z0-9\-]+)"
    r"|n[uú]mero\s+factura\s*[:\s]+([A-Z0-9][A-Z0-9\-]+)"
    r"|(?:no\.?|nro\.?)\s+(?:de\s+)?factura\s*[:\s#]+([A-Z0-9][A-Z0-9\-]+)"
    r"|factura\s+(?:n[uú]m\.?|n[uú]mero|no\.?|nro\.?)\s*[:\s#]+([A-Z0-9][A-Z0-9\-]+)",
    re.I,
)

# Emisor / Vendedor — etiquetas estándar representación gráfica DIAN
_RE_EMISOR_NIT    = re.compile(r"nit\s+del\s+emisor\s*[:\s]+([0-9]{6,12})", re.I)
_RE_EMISOR_NOMBRE = re.compile(r"raz[oó]n\s+social\s*[:\s]+([^\n\r]+)", re.I)

# Receptor / Comprador — etiquetas estándar representación gráfica DIAN
_RE_RECEPTOR_NIT    = re.compile(
    r"n[uú]mero\s+(?:de\s+)?documento\s*[:\s]+([0-9]{6,12})"
    r"|nit\s+(?:del\s+)?(?:adquir|comprador|receptor|cliente)[^\n]{0,30}?([0-9]{6,12})",
    re.I,
)
_RE_RECEPTOR_NOMBRE = re.compile(r"nombre\s+o\s+raz[oó]n\s+social\s*[:\s]+([^\n\r]+)", re.I)

# NIT genérico (fallback)
_RE_NIT_GENERICO = re.compile(r"NIT[:\s#.]*([0-9]{6,12})", re.I)

# Fecha desde nombre de carpeta: YYYY-MM, YYYY-MM-DD, DD-MM-YYYY, etc.
_RE_FOLDER_YEAR_MONTH = re.compile(r"(\d{4})[-_\s](\d{1,2})(?:[-_\s](\d{1,2}))?")
_RE_FOLDER_DMY        = re.compile(r"(\d{1,2})[-_/](\d{1,2})[-_/](\d{4})")


def _clean_number(value: str) -> float:
    """Convierte '1.234.567,89' o '1,234,567.89' a float."""
    value = value.strip().replace(" ", "")
    if not value:
        return 0.0
    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value and value.count(",") == 1 and len(value.split(",")[1]) <= 2:
        value = value.replace(",", ".")
    else:
        value = value.replace(",", "")
    try:
        return float(value)
    except ValueError:
        return 0.0


def _parse_date(raw: str) -> str:
    """Normaliza fecha a YYYY-MM-DD."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw.strip()


def _date_from_folder(path: Path) -> str:
    """Intenta extraer una fecha del nombre de la carpeta que contiene el archivo."""
    folder = path.parent.name
    m = _RE_FOLDER_YEAR_MONTH.search(folder)
    if m:
        year, month = m.group(1), m.group(2).zfill(2)
        day = m.group(3).zfill(2) if m.group(3) else "01"
        return f"{year}-{month}-{day}"
    m2 = _RE_FOLDER_DMY.search(folder)
    if m2:
        day, month, year = m2.group(1).zfill(2), m2.group(2).zfill(2), m2.group(3)
        return f"{year}-{month}-{day}"
    return ""


def _detect_doc_type(text: str, filename: str) -> str:
    tl = (text + filename).lower()
    if "nota cr" in tl or "note credit" in tl:
        return "Nota Crédito"
    if "mandato" in tl or "peaje" in tl:
        return "Mandato/Peaje"
    if "documento soporte" in tl:
        return "Documento Soporte"
    return "Factura Electrónica"


def _clean_name(raw: str) -> str:
    """Limpia un nombre: recorta en etiquetas adyacentes y limita longitud."""
    raw = raw.strip()
    # Corta si aparece un patrón "Algo:" luego de texto
    m = re.search(r"\s{2,}[A-Za-záéíóúÁÉÍÓÚñÑ ]{3,30}\s*:", raw)
    if m:
        raw = raw[:m.start()].strip()
    return raw[:80]


# ══════════════════════════════════════════════════════════════════════════════
# XML
# ══════════════════════════════════════════════════════════════════════════════

def _xml_text(root: ET.Element, path: str) -> str:
    el = root.find(path, NS)
    return el.text.strip() if el is not None and el.text else ""


def extract_xml(path: Path) -> dict:
    """Extrae campos de un XML DIAN (UBL 2.1)."""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error("XML inválido %s: %s", path.name, e)
        return _empty_row(path.name, "XML inválido")

    tag = root.tag.lower()
    if "creditnote" in tag:
        doc_type = "Nota Crédito"
        cufe_path = "ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/cbc:UUID"
    else:
        doc_type = "Factura Electrónica"
        cufe_path = "cbc:UUID"

    cufe = _xml_text(root, cufe_path) or _xml_text(root, "cbc:UUID")
    folio = _xml_text(root, "cbc:ID")
    fecha = _xml_text(root, "cbc:IssueDate")

    # Emisor
    nit_emisor  = _xml_text(root, "cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID")
    nom_emisor  = (
        _xml_text(root, "cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName")
        or _xml_text(root, "cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name")
    )
    # Receptor
    nit_receptor = _xml_text(root, "cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID")
    nom_receptor = (
        _xml_text(root, "cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName")
        or _xml_text(root, "cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name")
    )

    subtotal = 0.0
    iva19 = 0.0
    iva5  = 0.0

    for tax in root.findall(".//cac:TaxTotal", NS):
        amount_el = tax.find("cbc:TaxAmount", NS)
        amount = float(amount_el.text) if amount_el is not None and amount_el.text else 0.0
        percent_el = tax.find(".//cac:TaxSubtotal/cbc:Percent", NS)
        pct = float(percent_el.text) if percent_el is not None and percent_el.text else 0.0
        if abs(pct - 19) < 0.5:
            iva19 += amount
        elif abs(pct - 5) < 0.5:
            iva5 += amount

    le = root.find("cac:LegalMonetaryTotal", NS)
    if le is not None:
        subtotal = float((_xml_text(le, "cbc:TaxExclusiveAmount") or "0").replace(",", "."))
        total    = float((_xml_text(le, "cbc:PayableAmount") or "0").replace(",", "."))
    else:
        total = 0.0

    sign = -1 if doc_type == "Nota Crédito" else 1

    return {
        "archivo":         path.name,
        "tipo":            doc_type,
        "cufe":            cufe,
        "folio":           folio,
        "fecha":           _parse_date(fecha),
        "nit_emisor":      nit_emisor,
        "nombre_emisor":   nom_emisor,
        "nit_receptor":    nit_receptor,
        "nombre_receptor": nom_receptor,
        "subtotal":        round(sign * subtotal, 2),
        "iva_19":          round(sign * iva19, 2),
        "iva_5":           round(sign * iva5, 2),
        "total":           round(sign * total, 2),
        "fuente":          "XML",
    }


# ══════════════════════════════════════════════════════════════════════════════
# PDF
# ══════════════════════════════════════════════════════════════════════════════

def _search_money_near(text: str, label: str) -> float:
    """
    Busca el valor monetario en la misma línea que la etiqueta.
    Usa [^\\d\\n]{0,60} para saltar texto no-numérico (paréntesis, COP, $, espacios
    unicode como ㅤ) entre la etiqueta y el número.
    """
    pattern = re.compile(
        rf"^[^\n]*{re.escape(label)}[^\d\n]{{0,60}}([\d][\d.,]*)",
        re.I | re.MULTILINE,
    )
    m = pattern.search(text)
    if m:
        return _clean_number(m.group(1))
    return 0.0


def _first_group(*matches) -> str:
    """Retorna el primer grupo no vacío de una lista de match objects."""
    for m in matches:
        if m:
            groups = [g for g in m.groups() if g]
            if groups:
                return groups[0].strip()
    return ""


def extract_pdf(path: Path) -> dict:
    """Extrae campos de un PDF DIAN con pdfplumber."""
    try:
        with pdfplumber.open(path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        logger.error("Error leyendo PDF %s: %s", path.name, e)
        return _empty_row(path.name, str(e))

    doc_type = _detect_doc_type(text, path.name)

    # CUFE / CUDE
    cufe = ""
    m = _RE_CUFE.search(text)
    if m:
        cufe = m.group(1)
    else:
        m2 = _RE_CUDE.search(text)
        cufe = m2.group(1) if m2 else ""

    # Folio — busca "Número de Factura: FE-001" y similares
    folio = _first_group(_RE_FOLIO.search(text))

    # Fecha de emisión
    fecha = ""
    # Prefiere "Fecha de Emisión:" o "Fecha Emisión:"
    m_fecha_label = re.search(r"fecha\s+de\s+emisi[oó]n\s*[:\s]+(\S+)", text, re.I)
    if m_fecha_label:
        fecha = _parse_date(m_fecha_label.group(1))
    else:
        for dm in _RE_DATE.finditer(text):
            fecha = _parse_date(dm.group(1))
            break

    # ── Emisor ─────────────────────────────────────────────────────────────
    # 1. Etiqueta específica DIAN "Nit del Emisor:"
    m_en = _RE_EMISOR_NIT.search(text)
    nit_emisor = m_en.group(1).strip() if m_en else ""

    # 2. Razón Social (primera aparición → emisor)
    m_enombre = _RE_EMISOR_NOMBRE.search(text)
    nom_emisor = _clean_name(m_enombre.group(1)) if m_enombre else ""

    # ── Receptor ───────────────────────────────────────────────────────────
    # 1. "Número Documento:" o variantes con contexto comprador
    m_rn = _RE_RECEPTOR_NIT.search(text)
    nit_receptor = _first_group(m_rn) if m_rn else ""

    # 2. "Nombre o Razón Social:"
    m_rnombre = _RE_RECEPTOR_NOMBRE.search(text)
    nom_receptor = _clean_name(m_rnombre.group(1)) if m_rnombre else ""

    # Fallback genérico por NIT si alguno quedó vacío
    if not nit_emisor or not nit_receptor:
        nits = [m.group(1) for m in _RE_NIT_GENERICO.finditer(text)]
        if not nit_emisor and nits:
            nit_emisor = nits[0]
        if not nit_receptor and len(nits) > 1:
            nit_receptor = nits[1]

    # ── Montos ─────────────────────────────────────────────────────────────
    # Subtotal = base gravable DESPUÉS de descuentos de línea (= TaxExclusiveAmount en XML)
    # "Total Bruto Factura" es el campo correcto en la representación gráfica DIAN estándar.
    # "Subtotal" sería la suma bruta ANTES de descuentos → incorrecto para prorrateo IVA.
    subtotal = (
        _search_money_near(text, "Total Bruto Factura")
        or _search_money_near(text, "base gravable")
        or _search_money_near(text, "base imponible")
        or _search_money_near(text, "subtotal")
    )
    # IVA 19%: busca línea específica "IVA 19% …" o la línea "IVA …" del resumen de totales.
    # No se usa "iva" genérico solo porque la columna "IVA %" de los detalles tiene "19.00"
    # (el porcentaje) en líneas separadas, y el patrón con MULTILINE no los confunde.
    iva19 = (
        _search_money_near(text, "IVA 19%")
        or _search_money_near(text, "impuesto 19")
        or _search_money_near(text, "IVA")
    )
    iva5 = (
        _search_money_near(text, "IVA 5%")
        or _search_money_near(text, "impuesto 5")
    )
    # Total: "Total factura (=) ㅤ COP $ 1.191.999,83" — el nuevo _search_money_near
    # maneja espacios unicode y el prefijo "COP $" con [^\d\n]{0,60}.
    total = (
        _search_money_near(text, "Total factura")
        or _search_money_near(text, "Total neto factura")
        or _search_money_near(text, "total a pagar")
        or _search_money_near(text, "valor total")
    )

    sign = -1 if doc_type == "Nota Crédito" else 1

    return {
        "archivo":         path.name,
        "tipo":            doc_type,
        "cufe":            cufe,
        "folio":           folio,
        "fecha":           fecha,
        "nit_emisor":      nit_emisor,
        "nombre_emisor":   nom_emisor,
        "nit_receptor":    nit_receptor,
        "nombre_receptor": nom_receptor,
        "subtotal":        round(sign * subtotal, 2),
        "iva_19":          round(sign * iva19, 2),
        "iva_5":           round(sign * iva5, 2),
        "total":           round(sign * total, 2),
        "fuente":          "PDF",
    }


def _empty_row(filename: str, error: str) -> dict:
    return {
        "archivo": filename, "tipo": "ERROR", "cufe": "", "folio": "",
        "fecha": "", "nit_emisor": "", "nombre_emisor": "",
        "nit_receptor": "", "nombre_receptor": "",
        "subtotal": 0.0, "iva_19": 0.0, "iva_5": 0.0, "total": 0.0,
        "fuente": f"ERROR: {error}",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Dispatcher principal
# ══════════════════════════════════════════════════════════════════════════════

def extract_document(path: Path, processed: set[str]) -> Optional[dict]:
    """
    Extrae un documento. Prefiere XML si existe el par.
    Retorna None si ya fue procesado.
    Soporta subcarpetas: usa la ruta completa (sin extensión) como clave
    para evitar colisiones entre archivos con el mismo nombre en distintas carpetas.
    """
    # Clave única por carpeta+nombre para soportar subcarpetas
    name_key = str(path.with_suffix("")).lower()
    if name_key in processed:
        logger.info("Omitiendo duplicado: %s", path.name)
        return None
    processed.add(name_key)

    # Prioridad XML
    xml_sibling = path.with_suffix(".xml")
    if path.suffix.lower() == ".pdf" and xml_sibling.exists():
        logger.info("Usando XML en lugar de PDF: %s", xml_sibling.name)
        row = extract_xml(xml_sibling)
        row["archivo"] = path.name
        processed.add(str(xml_sibling.with_suffix("")).lower())
    elif path.suffix.lower() == ".xml":
        row = extract_xml(path)
    else:
        row = extract_pdf(path)

    # Fallback de fecha desde nombre de carpeta (si el archivo está en subcarpeta fechada)
    if not row.get("fecha"):
        folder_date = _date_from_folder(path)
        if folder_date:
            row["fecha"] = folder_date
            logger.info("Fecha tomada del nombre de carpeta: %s → %s", path.parent.name, folder_date)

    return row

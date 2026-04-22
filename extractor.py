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
_RE_CUFE = re.compile(r"CUFE[:\s]+([a-f0-9]{96})", re.I)
_RE_CUDE = re.compile(r"CUDE[:\s]+([a-f0-9]{96})", re.I)
_RE_NIT  = re.compile(r"NIT[:\s#.]*([0-9]{6,12})", re.I)
_RE_DATE = re.compile(r"(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})")
_RE_FOLIO = re.compile(
    r"(?:factura|nota\s+cr[eé]dito|n[uú]mero|no\.?|nro\.?)[:\s#]*([A-Z0-9\-]+)",
    re.I,
)
_RE_MONEY = re.compile(r"[\$]?\s*([\d.,]+)")


def _clean_number(value: str) -> float:
    """Convierte '1.234.567,89' o '1,234,567.89' a float."""
    value = value.strip().replace(" ", "")
    if not value:
        return 0.0
    # Formato colombiano: puntos=miles, coma=decimal
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


def _detect_doc_type(text: str, filename: str) -> str:
    tl = (text + filename).lower()
    if "nota cr" in tl or "note credit" in tl:
        return "Nota Crédito"
    if "mandato" in tl or "peaje" in tl:
        return "Mandato/Peaje"
    if "documento soporte" in tl:
        return "Documento Soporte"
    return "Factura Electrónica"


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
    nom_emisor  = _xml_text(root, "cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name")
    # Receptor
    nit_receptor = _xml_text(root, "cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID")
    nom_receptor = _xml_text(root, "cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name")

    subtotal = 0.0
    iva19 = 0.0
    iva5  = 0.0
    total = 0.0

    # Líneas de impuesto
    for tax in root.findall(".//cac:TaxTotal", NS):
        amount_el = tax.find("cbc:TaxAmount", NS)
        amount = float(amount_el.text) if amount_el is not None and amount_el.text else 0.0
        percent_el = tax.find(".//cac:TaxSubtotal/cbc:Percent", NS)
        pct = float(percent_el.text) if percent_el is not None and percent_el.text else 0.0
        if abs(pct - 19) < 0.5:
            iva19 += amount
        elif abs(pct - 5) < 0.5:
            iva5 += amount

    # Totales
    le = root.find("cac:LegalMonetaryTotal", NS)
    if le is not None:
        subtotal = float((_xml_text(le, "cbc:TaxExclusiveAmount") or "0").replace(",", "."))
        total    = float((_xml_text(le, "cbc:PayableAmount") or "0").replace(",", "."))

    sign = -1 if doc_type == "Nota Crédito" else 1

    return {
        "archivo":       path.name,
        "tipo":          doc_type,
        "cufe":          cufe,
        "folio":         folio,
        "fecha":         _parse_date(fecha),
        "nit_emisor":    nit_emisor,
        "nombre_emisor": nom_emisor,
        "nit_receptor":  nit_receptor,
        "nombre_receptor": nom_receptor,
        "subtotal":      round(sign * subtotal, 2),
        "iva_19":        round(sign * iva19, 2),
        "iva_5":         round(sign * iva5, 2),
        "total":         round(sign * total, 2),
        "fuente":        "XML",
    }


# ══════════════════════════════════════════════════════════════════════════════
# PDF
# ══════════════════════════════════════════════════════════════════════════════

def _search_money_near(text: str, label: str) -> float:
    """Busca el valor monetario más cercano a una etiqueta."""
    pattern = re.compile(
        rf"{re.escape(label)}[:\s]*([\d.,]+)", re.I
    )
    m = pattern.search(text)
    if m:
        return _clean_number(m.group(1))
    return 0.0


def extract_pdf(path: Path) -> dict:
    """Extrae campos de un PDF DIAN con pdfplumber."""
    try:
        with pdfplumber.open(path) as pdf:
            text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
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

    # Folio
    folio = ""
    fm = _RE_FOLIO.search(text)
    if fm:
        folio = fm.group(1).strip()

    # Fecha
    fecha = ""
    for dm in _RE_DATE.finditer(text):
        fecha = _parse_date(dm.group(1))
        break

    # NITs (primero y segundo encontrado)
    nits = [m.group(1) for m in _RE_NIT.finditer(text)]
    nit_emisor    = nits[0] if len(nits) > 0 else ""
    nit_receptor  = nits[1] if len(nits) > 1 else ""

    # Nombres: línea siguiente al NIT
    lines = text.splitlines()
    nom_emisor   = _extract_name_near(lines, nit_emisor)
    nom_receptor = _extract_name_near(lines, nit_receptor)

    # Montos
    subtotal = (
        _search_money_near(text, "subtotal")
        or _search_money_near(text, "base gravable")
        or _search_money_near(text, "base imponible")
    )
    iva19 = (
        _search_money_near(text, "IVA 19%")
        or _search_money_near(text, "impuesto 19")
        or _search_money_near(text, "iva")
    )
    iva5  = _search_money_near(text, "IVA 5%") or _search_money_near(text, "impuesto 5")
    total = (
        _search_money_near(text, "total a pagar")
        or _search_money_near(text, "valor total")
        or _search_money_near(text, "total")
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


def _extract_name_near(lines: list[str], nit: str) -> str:
    """Retorna la línea anterior o posterior donde aparece el NIT."""
    if not nit:
        return ""
    for i, line in enumerate(lines):
        if nit in line:
            # Toma la línea que NO sea solo el NIT
            for candidate in [lines[i-1] if i > 0 else "", line, lines[i+1] if i < len(lines)-1 else ""]:
                c = candidate.strip()
                if c and not re.fullmatch(r"[\d\-\s\.]+", c) and len(c) > 4:
                    return c[:80]
    return ""


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
    """
    name_stem = path.stem.lower()
    if name_stem in processed:
        logger.info("Omitiendo duplicado: %s", path.name)
        return None
    processed.add(name_stem)

    # Prioridad XML
    xml_sibling = path.with_suffix(".xml")
    if path.suffix.lower() == ".pdf" and xml_sibling.exists():
        logger.info("Usando XML en lugar de PDF: %s", xml_sibling.name)
        row = extract_xml(xml_sibling)
        row["archivo"] = path.name  # conserva nombre PDF como referencia
        return row

    if path.suffix.lower() == ".xml":
        return extract_xml(path)

    return extract_pdf(path)

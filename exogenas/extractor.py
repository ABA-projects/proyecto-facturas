"""Extractor de certificados de retención en la fuente (Formato 1003)."""

from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

from exogenas.municipios import buscar_municipio

# ── Helpers numéricos ─────────────────────────────────────────────────────────

def _parse_money(s: str) -> float:
    """Convierte cadena monetaria colombiana o US a float.
    Soporta: '1.234.567,00', '1,234,567.00', '$1.234', '($ 144.325)', '3.622.900'.
    """
    s = re.sub(r"[\$\(\)\s]", "", str(s)).strip()
    if not s:
        return 0.0
    dot_count   = s.count(".")
    comma_count = s.count(",")

    if dot_count > 1:
        # Múltiples puntos → todos son miles: 3.622.900 o 1.234.567,00
        s = s.replace(".", "")
        if comma_count == 1:
            s = s.replace(",", ".")
    elif comma_count > 1:
        # Múltiples comas → miles: 1,234,567
        s = s.replace(",", "")
    elif dot_count == 1 and comma_count == 1:
        if s.rfind(",") > s.rfind("."):   # 1.234,56 → decimal coma
            s = s.replace(".", "").replace(",", ".")
        else:                              # 1,234.56 → decimal punto
            s = s.replace(",", "")
    elif dot_count == 1:
        # Un solo punto: si tiene exactamente 3 decimales → miles (144.325 → 144325)
        # si tiene 1-2 decimales → decimal real (2.50 → 2.50)
        parts = s.split(".")
        if len(parts[1]) == 3:
            s = s.replace(".", "")        # 144.325 → 144325
        # else: float as-is (2.50, 0.70 etc.)
    elif comma_count == 1:
        parts = s.split(",")
        if len(parts[1]) <= 2:
            s = s.replace(",", ".")       # 144,32 → 144.32
        else:
            s = s.replace(",", "")        # 1,234 → 1234
    try:
        return float(s)
    except ValueError:
        return 0.0


def calcular_dv(nit: str) -> str:
    """Dígito de verificación colombiano (algoritmo DIAN)."""
    weights = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]
    digits = re.sub(r"\D", "", nit)
    if not digits:
        return ""
    n = len(digits)
    w = weights[-n:] if n <= len(weights) else weights
    total = sum(int(d) * wt for d, wt in zip(digits, w))
    r = total % 11
    return str(r) if r in (0, 1) else str(11 - r)


def _tipo_doc(nit: str) -> str:
    return "31" if len(re.sub(r"\D", "", nit)) >= 9 else "13"


# ── Regex patterns ────────────────────────────────────────────────────────────

# NIT con/sin DV — separador obligatorio ante DV para evitar backtracking
_RE_NIT_DV   = re.compile(
    r"N\.?I\.?T\.?\s*[:\s#No.]*([0-9]{6,12}|[0-9]{1,3}(?:\.[0-9]{3})+)\s*[-–]\s*([0-9])\b",
    re.I,
)
_RE_NIT_NODV = re.compile(
    r"N\.?I\.?T\.?\s*[:\s#No.]*([0-9]{6,12}|[0-9]{1,3}(?:\.[0-9]{3})+)",
    re.I,
)

# Tipo de certificado
_RE_CERT_ICA   = re.compile(
    r"retenci[oó]n\s+(?:de\s+|por\s+|y\s+)?ica\b"
    r"|ica\s+\d+[xX]\d+"          # "ICA 7x1000"
    r"|certificado\s+de\s+retenci[oó]n\s+(?:por\s+)?ica\b",
    re.I,
)
_RE_CERT_IVA   = re.compile(r"retenci[oó]n(?:es)?\s+(?:de\s+|por\s+)?IVA|RETEIVA", re.I)
_RE_CERT_RENTA = re.compile(
    r"retenci[oó]n(?:es)?\s+(?:en\s+la\s+fuente|por\s+renta|de\s+renta)"
    r"|retenci[oó]n\s+en\s+la\s+fuente",
    re.I,
)

# Ciudad donde se practicó la retención (acepta variantes con/sin acento)
_RE_CIUDAD_PRACT = re.compile(
    r"ciudad\s+donde\s+se\s+[^\n:]{0,40}:([^.\n]{3,40})",
    re.I,
)
_RE_CIUDAD_CONSIG = re.compile(
    r"(?:"
    r"consignad[ao]s?\s+en\s+(?:la\s+(?:ciudad|municipio)\s+(?:de\s+)?)?"
    r"|retenciones?\s+consignadas?\s+en\s+(?:la\s+ciudad\s+(?:de\s+)?)?"
    r"|ciudad\s+donde\s+se\s+consig[^\n:]{0,25}[:\s]+"
    r")[:\s]*([A-ZÁÉÍÓÚÑ][^.\n]{2,35})",
    re.I,
)
_RE_CIUDAD_EMISOR = re.compile(r"^ciudad\s*:\s*([A-ZÁÉÍÓÚÑ][^,.\n]{2,25})", re.M | re.I)
_RE_CIUDAD_FECHA = re.compile(
    r"^([A-ZÁÉÍÓÚÑ][a-záéíóúñA-Z\s]{3,20}),?\s+\d{1,2}[\s/]\w{2,10}[\s/]\d{4}",
    re.M,
)

# Línea TOTAL / TOTALES con dos montos
_RE_TOTAL_LINE = re.compile(
    r"^TOTAL(?:ES|S)?\s+([\d.,]+)\s+([\d.,]+)",
    re.M | re.I,
)

# Tabla formato colombiano: Concepto | Base(X.XXX.XXX) | % | Ret(X.XXX)
_RE_TABLE_COL_FORMAT = re.compile(
    r"([A-Za-záéíóú][^\t\n]{2,40}?)\s+"
    r"(\d{1,3}(?:\.\d{3})+)\s+"      # base con puntos miles: 3.622.900
    r"[\d.,]+\s*%\s+"                 # porcentaje
    r"(\d{1,3}(?:\.\d{3})*(?:,\d+)?)",  # retención
    re.M,
)

# Tabla genérica: Concepto | Tasa% | Base | Retenido  (orden variado)
_RE_TABLE_TASA_BASE_RET = re.compile(
    r"([A-Za-záéíóú][^\t\n]{2,60}?)\s+([\d]+[,.]\d{1,4}\s*%?)\s+([\d.,]+)\s+([\d.,]+)",
    re.M,
)

# Formato "Retefuente 2.5%  BASE  TARIFA  VALOR_TOTAL" (base antes que tasa)
_RE_RETEFTE_FORMAT = re.compile(
    r"retefuente\s+[\d.]+%\s+([\d,.]+\.?\d*)\s+[\d,.]+\s*%\s+([\d,.]+)",
    re.I,
)

# Formato QUIRUSTETIC: "PERIODO CONCEPTO VALOR_BASE VALOR_RETENIDO" sin columna %
_RE_QUIRUSTETIC_ROW = re.compile(
    r"(?:Anual|Enero|Febrero|[A-Za-z]+)\s+(?:COMPRAS|SERVICIOS|VENTAS)[^\n]{0,30}\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})",
    re.I,
)

# Formato SAN JUAN DE DIOS: código + concepto + % + "2,500" (código) + base + ret
_RE_SJD_ROW = re.compile(
    r"\d{8,}\s+[A-Z][^\n]{3,40}?\s+[\d.]+\s*%\s+[\d,]+\s+([\d.,]+)\s+([\d.,]+)",
    re.M,
)

# Párrafo MAYORISTA: "($ ret) m/l ... al pct% de ($ base)"
_RE_PARRAFO_MAYOR = re.compile(
    r"\(\$\s*([\d.,]+)\)\s*m/?l[^\n]{0,100}?(\d+[.,]\d+)\s*%[^\n]{0,60}?\(\$\s*([\d.,]+)\)",
    re.I,
)
# Párrafo MAYORISTA alternativo: "suma de $ret... equivalente al pct% de $base"
_RE_PARRAFO_MAYOR2 = re.compile(
    r"suma\s+de\s+(?:\(?\$\s*)?([\d.,]+)[^.]{0,100}?(\d+[.,]\d+)\s*%[^.]{0,80}?(?:\(?\$\s*)?([\d.,]+)",
    re.I,
)

# Tabla bimestre IVA (PROTECTION CLOUD): Bimestre | Base | IVA | Cuantía | %
_RE_BIMESTRE = re.compile(
    r"^\s*(?:[1-6]|[IVX]+)\s+\S[^\n]{5,80}?([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)",
    re.M,
)
# Tabla bimestre ROSARIO: I IVA DEL 19% Ret... | Base | IVA | % | Cuantia
_RE_BIMESTRE_ROSARIO = re.compile(
    r"^\s*(?:[IVX]+|[1-6])\s+IVA[^\n]{0,50}?([\d.,]+)\s+([\d.,]+)\s+[\d.,]+\s+([\d.,]+)",
    re.M,
)

# SUINSUMOYA box format
_RE_BOX_BASE = re.compile(
    r"RETENCION[^|$\n]{0,60}([\d.,]+)[^\d\n]*?([\d.,]+)",
    re.I,
)

# Formato PERSEO/etiqueta: "MONTO TOTAL: $X" + "CUANTIA DE LA RETENCION: $Y"
_RE_MONTO_TOTAL = re.compile(
    r"MONTO\s+TOTAL[:\s]*\$?\s*([\d.,]+)", re.I
)
_RE_CUANTIA = re.compile(
    r"(?:CUANTIA(?:\s+DE\s+LA\s+RETENCION)?|VALOR\s+RETENID[OA]|VALOR\s+TOTAL)[:\s]*\$?\s*([\d.,]+)", re.I
)


# ── NIT y Razón Social ────────────────────────────────────────────────────────

def _clean_nit(raw: str) -> str:
    """Elimina puntos de miles de un NIT: '800.233.836' → '800233836'."""
    return re.sub(r"\D", "", raw)


_RE_BARE_NIT_DV  = re.compile(r"^(\d{7,12})[-–](\d)$")
_RE_BARE_NIT     = re.compile(r"^(\d{7,12})[-–]?$")   # acepta trailing dash (890905154-)
_RE_RAZON_LABEL  = re.compile(r"razón?\s+social[^:]{0,20}:\s*([^\n]{3,70})", re.I)
# Líneas de paginación a ignorar al buscar razón social
_RE_PAGINA       = re.compile(r"^p[aá]g(?:ina)?[.:]?\s*\d+$", re.I)
# Líneas que parecen dirección (no son razón social)
_RE_ADDR_START   = re.compile(
    r"^(?:CL|CR|CRA|KR|AK|AV|KM|VDA|CARRERA|CALLE|DIAGONAL|TRANSVERSAL|AVENIDA|BARRIO|SECTOR)\b",
    re.I,
)


def _is_junk_line(ln: str) -> bool:
    """Retorna True si la línea es paginación, dirección o demasiado corta para ser razón social."""
    if not ln or len(ln) < 3:
        return True
    if _RE_PAGINA.match(ln):
        return True
    if _RE_ADDR_START.match(ln):
        return True
    # Línea que es sólo caracteres de guión/relleno
    if re.match(r"^[-=_*·.]{4,}$", ln):
        return True
    return False


def _extract_emisor(text: str) -> tuple[str, str, str]:
    """Retorna (razon_social, nit_limpio, dv). Busca el NIT del EMISOR (primeras 30 líneas)."""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    nit_raw = dv = ""
    nit_line_idx = -1

    # Prioridad 1: NIT bare en primeras 8 líneas (formato IRCC: Company\nNIT-DV\nAddr)
    for i, ln in enumerate(lines[:8]):
        m = _RE_BARE_NIT_DV.match(ln)
        if m:
            nit_raw, dv = m.group(1), m.group(2)
            nit_line_idx = i
            break
        m = _RE_BARE_NIT.match(ln)
        if m and len(m.group(1)) >= 8:
            nit_raw = m.group(1)
            nit_line_idx = i
            break

    if not nit_raw:
        for i, ln in enumerate(lines[:30]):
            m = _RE_NIT_DV.search(ln)
            if m:
                nit_raw, dv = m.group(1), m.group(2)
                nit_line_idx = i
                break
            m = _RE_NIT_NODV.search(ln)
            if m:
                nit_raw = m.group(1)
                nit_line_idx = i
                break

    nit_clean = _clean_nit(nit_raw)
    if not dv and nit_clean:
        dv = calcular_dv(nit_clean)

    razon = ""
    if nit_line_idx > 0:
        # Buscar hacia atrás la primera línea válida (saltando paginación, direcciones, etc.)
        for look_back in range(1, min(nit_line_idx + 1, 6)):
            candidate = lines[nit_line_idx - look_back]
            if _RE_NIT_DV.search(candidate) or _RE_NIT_NODV.search(candidate):
                # El NIT está en la misma línea que la razón social
                razon = re.split(r"N\.?I\.?T", candidate, flags=re.I)[0].strip()
                break
            if _is_junk_line(candidate):
                continue
            razon = candidate
            break
    elif nit_line_idx == 0 and len(lines) > 1:
        razon = lines[1] if not _RE_NIT_NODV.search(lines[1]) else ""

    # Intentar etiqueta "Razón Social:" si la razon extraída es pobre
    if len(razon) < 3:
        m_rs = _RE_RAZON_LABEL.search(text[:800])
        if m_rs:
            razon = m_rs.group(1).strip()

    # Limpiar prefijos comunes
    razon = re.sub(
        r"(?i)(agente\s+retenedor|razón?\s+social|nombre\s+comercial|empresa)[:\s]*", "", razon
    ).strip()
    razon = re.sub(r"[\|_\-]{2,}", "", razon).strip()
    if len(razon) < 3:
        razon = ""

    return razon, nit_clean, dv


def _extract_direccion(text: str) -> str:
    m = re.search(
        r"(?:CL|CR|CRA|AK|AV|KM|VDA|CARRERA|CALLE|DIAGONAL|TRANSVERSAL|AVENIDA)[^\n]{3,60}",
        text, re.I,
    )
    return m.group(0).strip() if m else ""


# ── Tipo de certificado ───────────────────────────────────────────────────────

def _cert_type(text: str) -> str:
    """Devuelve 'ICA', 'IVA' o 'RENTA'."""
    snippet = text[:800]
    if _RE_CERT_ICA.search(snippet):
        return "ICA"
    if _RE_CERT_IVA.search(snippet):
        return "IVA"
    if _RE_CERT_RENTA.search(snippet):
        return "RENTA"
    # Fallback: si menciona "fuente" o "renta" → RENTA
    if re.search(r"\b(?:fuente|renta)\b", snippet, re.I):
        return "RENTA"
    return "RENTA"


# ── Concepto 1003 ─────────────────────────────────────────────────────────────

# Conceptos 1303 (servicios) — tasas 1%, 3.5%, 4%, 6% según Art. 392 ET
_TASAS_SERVICIOS = {1.0, 1.5, 2.0, 3.5, 4.0, 6.0, 10.0, 11.0}
_TASAS_COMPRAS   = {0.5, 1.0, 1.5, 2.5, 3.0, 3.5}  # compras puede ser 2.5%

# Mapa de palabras clave de concepto → código DIAN
_CONCEPTO_MAP = [
    # servicios (1303) — orden específico antes de compras
    (re.compile(r"HONORARIOS|HONORARIO", re.I),                   "1303"),
    (re.compile(r"SERVICIOS?\b", re.I),                           "1303"),
    (re.compile(r"ARRENDAMIENTO|RENTA\s+DE\s+BIEN", re.I),        "1303"),
    (re.compile(r"COMISIONES?", re.I),                            "1303"),
    # compras / general (1302)
    (re.compile(r"COMPRAS?|COMPRA\s+GENERAL", re.I),              "1302"),
    (re.compile(r"VENTAS?", re.I),                                 "1302"),
]


def _pct_to_concepto(keyword: str, pct: float) -> str:
    """Mapea (palabra del concepto, porcentaje) → código DIAN."""
    for pattern, code in _CONCEPTO_MAP:
        if pattern.search(keyword):
            return code
    # Si la tasa es típica de servicios (>= 3.5%), prefiere 1303
    if pct in _TASAS_SERVICIOS and pct >= 3.5:
        return "1303"
    return "1302"


def _detect_concepto(text: str, tipo_cert: str) -> tuple[str, float]:
    """Retorna (concepto_1003, porcentaje). concepto: '1302','1303','1309','ICA'."""
    if tipo_cert == "ICA":
        return "ICA", 0.0
    if tipo_cert == "IVA":
        return "1309", 15.0

    # Buscar porcentaje explícito
    pct_m = re.search(r"(\d+[.,]\d+)\s*%", text)
    pct = float(pct_m.group(1).replace(",", ".")) if pct_m else 0.0

    # Detectar palabra clave de concepto en el texto
    for pattern, code in _CONCEPTO_MAP:
        if pattern.search(text):
            return code, pct if pct else (4.0 if code == "1303" else 2.5)

    return "1302", pct if pct else 2.5


# ── Extracción de filas múltiples de conceptos ────────────────────────────────

# Tabla "Concepto LABEL PCT%  BASE  RETENCIÓN" — múltiples filas
_RE_MULTI_ROW = re.compile(
    r"(?P<label>[A-Za-záéíóúÁÉÍÓÚñÑ][^\n\t]{2,50}?)\s+"
    r"(?P<pct>[\d]+[.,][\d]{1,4})\s*%\s+"
    r"(?P<base>[\d.,]{4,}(?:\.\d{2})?)\s+%?\s*"
    r"(?P<ret>[\d.,]{3,})",
    re.M,
)

# Tabla sin porcentaje explícito: "CONCEPTO  BASE  RETENCIÓN"
_RE_MULTI_ROW_NOPCT = re.compile(
    r"(?P<label>COMPRAS?|SERVICIOS?|HONORARIOS?|ARRENDAMIENTOS?|COMISIONES?|VENTAS?)[^\n]{0,40}\s+"
    r"(?P<base>[\d.,]{4,}(?:\.\d{2})?)\s+"
    r"(?P<ret>[\d.,]{3,})",
    re.M | re.I,
)


def _extract_concepto_rows(
    text: str, tipo_cert: str
) -> list[tuple[str, float, float, float]]:
    """
    Intenta encontrar todas las filas de conceptos en el certificado.
    Retorna lista de (concepto_dian, porcentaje, base, retencion).
    Si no encuentra filas múltiples, retorna lista vacía.
    """
    if tipo_cert in ("ICA", "IVA"):
        return []

    rows: list[tuple[str, float, float, float]] = []

    # 1. Tabla con porcentaje explícito
    for m in _RE_MULTI_ROW.finditer(text):
        label = m.group("label").strip()
        pct   = float(m.group("pct").replace(",", "."))
        base  = _parse_money(m.group("base"))
        ret   = _parse_money(m.group("ret"))
        if base > 100 and ret > 0 and base > ret:
            concepto = _pct_to_concepto(label, pct)
            rows.append((concepto, pct, base, ret))

    if rows:
        return rows

    # 2. Tabla sin porcentaje (compras/servicios sin tasa)
    for m in _RE_MULTI_ROW_NOPCT.finditer(text):
        label = m.group("label").strip()
        base  = _parse_money(m.group("base"))
        ret   = _parse_money(m.group("ret"))
        if base > 100 and ret > 0 and base > ret:
            concepto = _pct_to_concepto(label, 0.0)
            pct = round(ret / base * 100, 2) if base else 0.0
            rows.append((concepto, pct, base, ret))

    return rows


# ── Extracción de montos ──────────────────────────────────────────────────────

def _extract_amounts(text: str, tipo_cert: str) -> tuple[float, float]:
    """Retorna (base, retencion). Intenta múltiples layouts."""

    # 1. Línea TOTAL/TOTALES
    m = _RE_TOTAL_LINE.search(text)
    if m:
        return _parse_money(m.group(1)), _parse_money(m.group(2))

    # 1b. Formato PERSEO etiqueta: "MONTO TOTAL: $X  CUANTIA: $Y"
    m_total = _RE_MONTO_TOTAL.search(text)
    m_cuant  = _RE_CUANTIA.search(text)
    if m_total and m_cuant and m_total.start() < m_cuant.start():
        b = _parse_money(m_total.group(1))
        r = _parse_money(m_cuant.group(1))
        if b > r > 0:
            return b, r

    # 2. Formato Retefuente (base antes de tarifa)
    m = _RE_RETEFTE_FORMAT.search(text)
    if m:
        return _parse_money(m.group(1)), _parse_money(m.group(2))

    # 3. Tabla formato colombiano X.XXX.XXX (MONTERROZA style)
    rows_col = _RE_TABLE_COL_FORMAT.findall(text)
    if rows_col:
        base_sum = ret_sum = 0.0
        for _conc, base_s, ret_s in rows_col:
            b, r = _parse_money(base_s), _parse_money(ret_s)
            if b > 500 and r > 0 and b > r:
                base_sum += b
                ret_sum  += r
        if base_sum > 0:
            return base_sum, ret_sum

    # 4. Formato QUIRUSTETIC (Anual COMPRAS base ret sin %)
    m = _RE_QUIRUSTETIC_ROW.search(text)
    if m:
        return _parse_money(m.group(1)), _parse_money(m.group(2))

    # 4. Párrafo MAYORISTA con paréntesis
    m = _RE_PARRAFO_MAYOR.search(text)
    if m:
        return _parse_money(m.group(3)), _parse_money(m.group(1))

    m = _RE_PARRAFO_MAYOR2.search(text)
    if m:
        return _parse_money(m.group(3)), _parse_money(m.group(1))

    # 5. Tabla bimestre ROSARIO (IVA por bimestre con totales)
    ros = _RE_BIMESTRE_ROSARIO.findall(text)
    if ros:
        return sum(_parse_money(r[0]) for r in ros), sum(_parse_money(r[2]) for r in ros)

    # 6. Tabla bimestre genérica (PROTECTION CLOUD)
    bims = _RE_BIMESTRE.findall(text)
    if bims:
        # Columnas típicas: base, monto_iva, cuantia, porcentaje
        iva = tipo_cert == "IVA"
        base_sum = sum(_parse_money(r[0]) for r in bims)
        ret_sum  = sum(_parse_money(r[2]) for r in bims) if iva else sum(_parse_money(r[1]) for r in bims)
        if base_sum > 100:
            return base_sum, ret_sum

    # 7. Formato SAN JUAN DE DIOS (código + concepto + % + código + base + ret)
    m = _RE_SJD_ROW.search(text)
    if m:
        return _parse_money(m.group(1)), _parse_money(m.group(2))

    # 8. Tabla genérica 4 columnas (Concepto | Tasa% | Base | Ret)
    rows = _RE_TABLE_TASA_BASE_RET.findall(text)
    if rows:
        base_sum = ret_sum = 0.0
        for _conc, _tasa, base_s, ret_s in rows:
            b, r = _parse_money(base_s), _parse_money(ret_s)
            # Filtrar falsos positivos (montos muy pequeños o iguales)
            if b > 500 and r > 0 and b > r:
                base_sum += b
                ret_sum  += r
        if base_sum > 0:
            return base_sum, ret_sum

    # 9. SUINSUMOYA box
    m = _RE_BOX_BASE.search(text)
    if m:
        b, r = _parse_money(m.group(1)), _parse_money(m.group(2))
        if b > r > 0:
            return b, r

    # 10. Fallback numérico: buscar dos montos grandes consecutivos con ratio ~2-15%
    nums = [_parse_money(n) for n in re.findall(r"[\d.,]{5,}", text)]
    candidates = [n for n in nums if n > 1000]
    for i in range(len(candidates) - 1):
        b, r = candidates[i], candidates[i + 1]
        if b > r > 0 and 0.005 < r / b < 0.25:
            return b, r

    return 0.0, 0.0


# ── Ciudad de retención ───────────────────────────────────────────────────────

def _clean_city(raw: str) -> str:
    """Limpia ciudad: quita prefijos de ruido y texto trailing."""
    city = raw.split("\n")[0].strip()
    city = re.split(r"[,;/]", city)[0].strip()
    # Quitar prefijos como "DE:", "DE :", ": "
    city = re.sub(r"^(?:DE\s*:?\s*|:\s*)", "", city, flags=re.I).strip()
    # Quitar frases de relleno al final
    city = re.sub(
        r"(?i)\s*\b(se expide|donde se|esta cert|ificado|art\.|decreto|d\.c\.|s\.a\.s|\|)\b.*$",
        "", city,
    ).strip()
    city = re.sub(r"[\._\|\-]{2,}.*$", "", city).strip()
    # Máximo 3 palabras
    words = city.split()
    return " ".join(words[:3]) if len(words) > 3 else city


def _extract_ciudad_retencion(text: str) -> str:
    for pat in (_RE_CIUDAD_PRACT, _RE_CIUDAD_CONSIG):
        m = pat.search(text)
        if m:
            city = _clean_city(m.group(1))
            if len(city) >= 3:
                return city

    # Línea de fecha al final: "MEDELLÍN abril 24 de 2026"
    m = _RE_CIUDAD_FECHA.search(text)
    if m:
        city = _clean_city(m.group(1))
        if len(city) >= 3:
            return city

    # Emisor's city como último recurso ("Ciudad: Sincelejo")
    m = _RE_CIUDAD_EMISOR.search(text)
    if m:
        return _clean_city(m.group(1))

    return ""


# ── Entry point ───────────────────────────────────────────────────────────────

def _base_row(path: Path, error: str = "") -> dict:
    """Dict base con todos los campos requeridos."""
    return {
        "razon_social": "", "nit": "", "dv": "", "tipo_doc": "31",
        "direccion": "", "ciudad_retencion": "", "concepto": "", "base": 0.0,
        "retencion": 0.0, "porcentaje": 0.0, "tipo_cert": "",
        "validacion_tasa": 0.0,  # retencion/base × 100 para verificar
        "es_escaneado": False,
        "fuente": "PDF", "archivo": path.name, "error": error,
    }


def _read_text(path: Path) -> tuple[str, bool]:
    """
    Lee el texto del PDF. Retorna (texto, es_escaneado).
    es_escaneado=True si el PDF no tiene texto extraíble.
    """
    suf = path.suffix.lower()
    if suf in (".docx", ".doc"):
        from docx import Document
        doc = Document(str(path))
        parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                parts.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                parts.append("\t".join(cell.text for cell in row.cells))
        return "\n".join(parts), False

    with pdfplumber.open(path) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]
    text = "\n".join(pages_text)
    es_escaneado = not text.strip()
    return text, es_escaneado


def extract_many(path: "str | Path") -> list[dict]:
    """
    Extrae TODOS los registros de un certificado de retención.
    Un certificado puede tener múltiples conceptos (1302, 1303) o
    múltiples terceros, generando varias filas.

    Retorna lista de dicts con campos:
        razon_social, nit, dv, tipo_doc, direccion, ciudad_retencion,
        concepto, base, retencion, porcentaje, validacion_tasa,
        es_escaneado, tipo_cert, fuente, archivo, error
    """
    path = Path(path)
    base = _base_row(path)

    try:
        text, es_escaneado = _read_text(path)
    except Exception as e:
        base["error"] = f"No se pudo abrir: {e}"
        return [base]

    if es_escaneado:
        base["error"] = "PDF escaneado (imagen) — texto no extraíble"
        base["es_escaneado"] = True
        return [base]

    tipo_cert             = _cert_type(text)
    razon, nit, dv        = _extract_emisor(text)
    ciudad                = _extract_ciudad_retencion(text)
    direccion             = _extract_direccion(text)

    def _make_row(concepto: str, porcentaje: float, b: float, r: float) -> dict:
        tasa_calc = round(r / b * 100, 2) if b else 0.0
        return {
            "razon_social":     razon,
            "nit":              nit,
            "dv":               dv,
            "tipo_doc":         _tipo_doc(nit),
            "direccion":        direccion,
            "ciudad_retencion": ciudad,
            "concepto":         concepto,
            "base":             b,
            "retencion":        r,
            "porcentaje":       porcentaje,
            "validacion_tasa":  tasa_calc,
            "es_escaneado":     False,
            "tipo_cert":        tipo_cert,
            "fuente":           "PDF",
            "archivo":          path.name,
            "error":            "",
        }

    # ICA → fila única (va a tabla separada)
    if tipo_cert == "ICA":
        b, r = _extract_amounts(text, tipo_cert)
        return [_make_row("ICA", 0.0, b, r)]

    # Intentar múltiples filas de concepto
    multi = _extract_concepto_rows(text, tipo_cert)
    if multi:
        return [_make_row(concepto, pct, b, r) for concepto, pct, b, r in multi]

    # Fallback: fila única
    concepto, porcentaje  = _detect_concepto(text, tipo_cert)
    b, r                  = _extract_amounts(text, tipo_cert)
    if b == 0 and r == 0:
        base["error"] = "No se encontraron montos"
        base["razon_social"] = razon
        base["nit"] = nit
        base["dv"] = dv
        base["ciudad_retencion"] = ciudad
        base["tipo_cert"] = tipo_cert
        return [base]
    return [_make_row(concepto, porcentaje, b, r)]


def extract_one(path: "str | Path") -> dict:
    """
    Extrae el primer registro de un certificado de retención PDF.
    Alias de extract_many()[0] — mantiene compatibilidad hacia atrás.

    Para certificados con múltiples conceptos usar extract_many().
    """
    rows = extract_many(path)
    return rows[0] if rows else _base_row(Path(path), error="Sin resultados")

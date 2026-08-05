"""Convert a small linear math notation into Word native OMML equations."""

import re

from docx.oxml.ns import qn
from lxml import etree


M = "m"
W = "w"


def _q(tag: str, ns: str = M) -> str:
    return qn(f"{ns}:{tag}")


def make_run(text: str, italic: bool = True, font_size: int = 24) -> etree.Element:
    r = etree.Element(_q("r"))
    if not italic:
        rPr = etree.SubElement(r, _q("rPr"))
        sty = etree.SubElement(rPr, _q("sty"))
        sty.set(_q("val"), "p")
    wRPr = etree.SubElement(r, _q("rPr", W))
    rFonts = etree.SubElement(wRPr, _q("rFonts", W))
    rFonts.set(_q("ascii", W), "Cambria Math")
    rFonts.set(_q("hAnsi", W), "Cambria Math")
    sz = etree.SubElement(wRPr, _q("sz", W))
    sz.set(_q("val", W), str(font_size))
    szCs = etree.SubElement(wRPr, _q("szCs", W))
    szCs.set(_q("val", W), str(font_size))
    t = etree.SubElement(r, _q("t"))
    t.text = text
    t.set(qn("xml:space"), "preserve")
    return r


def make_sSub(base: etree.Element, sub: etree.Element) -> etree.Element:
    s = etree.Element(_q("sSub"))
    e = etree.SubElement(s, _q("e"))
    e.append(base)
    sub_el = etree.SubElement(s, _q("sub"))
    sub_el.append(sub)
    return s


def make_sSup(base: etree.Element, sup: etree.Element) -> etree.Element:
    s = etree.Element(_q("sSup"))
    e = etree.SubElement(s, _q("e"))
    e.append(base)
    sup_el = etree.SubElement(s, _q("sup"))
    sup_el.append(sup)
    return s


def make_sSubSup(
    base: etree.Element, sub: etree.Element, sup: etree.Element
) -> etree.Element:
    s = etree.Element(_q("sSubSup"))
    e = etree.SubElement(s, _q("e"))
    e.append(base)
    sub_el = etree.SubElement(s, _q("sub"))
    sub_el.append(sub)
    sup_el = etree.SubElement(s, _q("sup"))
    sup_el.append(sup)
    return s


def make_fraction(num_els: list, den_els: list) -> etree.Element:
    f = etree.Element(_q("f"))
    num = etree.SubElement(f, _q("num"))
    den = etree.SubElement(f, _q("den"))
    for el in num_els:
        num.append(el)
    for el in den_els:
        den.append(el)
    return f


def make_nary(
    char: str,
    lower: list,
    upper: list,
    operand: list,
) -> etree.Element:
    nary = etree.Element(_q("nary"))
    naryPr = etree.SubElement(nary, _q("naryPr"))
    ch = etree.SubElement(naryPr, _q("chr"))
    ch.set(_q("val"), char)
    if lower:
        sub = etree.SubElement(nary, _q("sub"))
        for el in lower:
            sub.append(el)
    if upper:
        sup = etree.SubElement(nary, _q("sup"))
        for el in upper:
            sup.append(el)
    e = etree.SubElement(nary, _q("e"))
    for el in operand:
        e.append(el)
    return nary


def make_delimited(
    content: list, open_char: str = "(", close_char: str = ")"
) -> etree.Element:
    d = etree.Element(_q("d"))
    dPr = etree.SubElement(d, _q("dPr"))
    beg = etree.SubElement(dPr, _q("begChr"))
    beg.set(_q("val"), open_char)
    end = etree.SubElement(dPr, _q("endChr"))
    end.set(_q("val"), close_char)
    e = etree.SubElement(d, _q("e"))
    for el in content:
        e.append(el)
    return d


def make_omath(elements: list) -> etree.Element:
    o = etree.Element(_q("oMath"))
    for el in elements:
        o.append(el)
    return o


GREEK_MAP = {
    "lambda": "\u03bb",
    "beta": "\u03b2",
    "Sigma": "\u03a3",
    "sigma": "\u03c3",
    "alpha": "\u03b1",
    "gamma": "\u03b3",
    "theta": "\u03b8",
    "mu": "\u03bc",
    "tau": "\u03c4",
    "pi": "\u03c0",
    "sum": "\u2211",
}


def _greek(text: str) -> str:
    return GREEK_MAP.get(text, text)


def _is_relational(char: str) -> bool:
    return char in ("\u2208", "\u2211", "\u03a3", "\u2026", "+", "-", "=", "/", ",", ";", "(", ")", ".")


TOKEN_RE = re.compile(
    r"""
    (?P<sum>\b(?:sum|\u03a3)_(?:\{[^{}]*\}(?:\^\{[^{}]*\})?|\w+))
   |(?P<func>\b(?:Var|f)\([^)]*\))
   |(?P<paren>\((?:[^()]|\([^)]*\))*\))
   |(?P<ellip>\.\.\.|\u2026)
   |(?P<greek>[\u03bb\u03b2\u03a3\u2211\u2208\u2026])
   |(?P<op>[=+\-*/;,\.])
   |(?P<ident>[A-Za-z][A-Za-z_0-9]*(?:\^[A-Za-z_0-9]+)?)
   |(?P<number>\d+)
   |(?P<space>\s+)
   |(?P<other>.)
    """,
    re.VERBOSE,
)


def _tokenize(text: str) -> list:
    tokens = []
    for m in TOKEN_RE.finditer(text):
        kind = m.lastgroup
        value = m.group(0)
        if kind == "space":
            continue
        tokens.append((kind, value))
    return tokens


def _make_identifier(token: str) -> etree.Element:
    if "^" in token:
        base_part, sup_part = token.split("^", 1)
    else:
        base_part, sup_part = token, None

    parts = base_part.split("_")
    base = _greek(parts[0])
    subs = parts[1:]

    base_run = make_run(base, italic=True)

    if subs:
        sub_text = ", ".join(_greek(s) for s in subs)
        sub_run = make_run(sub_text, italic=True)
    else:
        sub_run = None

    if sup_part is not None:
        sup_run = make_run(_greek(sup_part), italic=True)
        if sub_run is not None:
            return make_sSubSup(base_run, sub_run, sup_run)
        return make_sSup(base_run, sup_run)

    if sub_run is not None:
        return make_sSub(base_run, sub_run)
    return base_run


def _parse_sum_args(raw: str) -> tuple:
    """Parse sum_{lower}^{upper} or sum_plain and return (operator_char, lower_els, upper_els)."""
    brace_pat = re.fullmatch(r"(sum|\u03a3)_\{(.*?)\}(?:\^\{(.*?)\})?", raw)
    plain_pat = re.fullmatch(r"(sum|\u03a3)_(\w+)", raw)

    if brace_pat:
        _, lower_raw, upper_raw = brace_pat.groups()
    elif plain_pat:
        _, lower_raw = plain_pat.groups()
        upper_raw = None
    else:
        return ("\u2211", [], [])

    lower = _parse_sum_limit(lower_raw or "")
    upper = _parse_sum_limit(upper_raw or "") if upper_raw else []
    return ("\u2211", lower, upper)


def _parse_sum_limit(text: str) -> list:
    if not text:
        return []
    text = text.replace(" in ", " \u2208 ")
    text = text.replace("..", ", \u2026, ")
    tokens = _tokenize(text)
    return _parse_expr(tokens)


def _parse_factor(token: tuple) -> list:
    kind, value = token
    if kind == "sum":
        # Limits-only token; operand handled at term level.
        op_char, lower, upper = _parse_sum_args(value)
        return [make_nary(op_char, lower, upper, [])]
    if kind == "func":
        m = re.fullmatch(r"(Var|f)\((.*)\)", value)
        if not m:
            return [make_run(value, italic=True)]
        name, content = m.groups()
        inner = _parse_expr(_tokenize(content))
        d = make_delimited(inner, "(", ")")
        if name == "Var":
            return [make_run(name, italic=False), d]
        return [make_run(name, italic=True), d]
    if kind == "paren":
        inner = _parse_expr(_tokenize(value[1:-1]))
        return [make_delimited(inner, "(", ")")]
    if kind == "ellip":
        return [make_run("\u2026", italic=False)]
    if kind == "greek":
        # Variables like lambda, beta are italic; operators like ∈, … are not.
        italic = value in ("\u03bb", "\u03b2")
        return [make_run(value, italic=italic)]
    if kind == "ident":
        return [_make_identifier(value)]
    if kind == "number":
        return [make_run(value, italic=False)]
    if kind in ("op", "other"):
        return [make_run(value, italic=False)]
    return [make_run(value, italic=True)]


def _parse_term(tokens: list) -> list:
    elements = []
    i = 0
    while i < len(tokens):
        kind, value = tokens[i]
        if kind == "sum":
            op_char, lower, upper = _parse_sum_args(value)
            # The summand is everything that follows in this term.
            operand_tokens = tokens[i + 1 :]
            operand = _parse_expr(operand_tokens) if operand_tokens else []
            nary = make_nary(op_char, lower, upper, operand)
            elements.append(nary)
            break
        elements.extend(_parse_factor(tokens[i]))
        i += 1
    return elements


def _parse_expr(tokens: list) -> list:
    """Parse +/− separated terms."""
    if not tokens:
        return []
    parts = []
    current = []
    for tok in tokens:
        if tok[0] == "op" and tok[1] in "+-":
            parts.append(current)
            parts.append(tok)
            current = []
        else:
            current.append(tok)
    parts.append(current)

    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(make_run(part[1], italic=False))
        else:
            out.extend(_parse_term(part))
    return out


def _parse_side(tokens: list) -> list:
    """Handle top-level fractions."""
    slash_pos = next((i for i, (k, v) in enumerate(tokens) if k == "op" and v == "/"), -1)
    if slash_pos != -1:
        num = _parse_expr(tokens[:slash_pos])
        den = _parse_expr(tokens[slash_pos + 1 :])
        return [make_fraction(num, den)]
    return _parse_expr(tokens)


def build_omml(math_text: str) -> tuple:
    """Return (m:oMath element, trailing punctuation string) for the given equation."""
    text = math_text.strip()
    trailing = ""
    if text and text[-1] in ",.":
        trailing = text[-1]
        text = text[:-1].rstrip()

    if not text:
        return make_omath([make_run("")]), trailing

    tokens = _tokenize(text)
    eq_pos = next((i for i, (k, v) in enumerate(tokens) if k == "op" and v == "="), -1)
    if eq_pos != -1:
        lhs = _parse_side(tokens[:eq_pos])
        rhs = _parse_side(tokens[eq_pos + 1 :])
        elements = lhs + [make_run("=", italic=False)] + rhs
    else:
        elements = _parse_side(tokens)

    return make_omath(elements), trailing

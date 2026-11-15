"""
Markdown parser for CorpDoc.

Uses mistune v3 as lexer for robust, spec-compliant parsing.
Produces typed block dicts consumed by api.py.
"""

import re
from urllib.parse import unquote

import mistune
import yaml


# Deepest list level with its own style (0-based): three levels in total.
MAX_LIST_LEVEL = 2

# ── Block parsing ──────────────────────────────────────────────────────────


def parse_frontmatter(md_text):
    """
    Split YAML frontmatter from body. Returns (meta_dict, body_text).

    The frontmatter block is the text between two `---` fences at the top
    of the file. It is parsed with yaml.safe_load so quoted strings with
    colons, dates, lists, and nested structures all work. On parse error
    the frontmatter is skipped and an empty dict is returned.
    """
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", md_text, re.DOTALL)
    if not fm_match:
        return {}, md_text

    body = md_text[fm_match.end() :]
    try:
        parsed = yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError:
        return {}, body

    if not isinstance(parsed, dict):
        return {}, body

    # Normalize scalar values to strings — the rest of the pipeline expects
    # str-like access (e.g. meta.get('version')). Preserve dict/list values.
    meta = {
        k: (v if isinstance(v, (dict, list)) else ("" if v is None else str(v)))
        for k, v in parsed.items()
    }
    return meta, body


def parse_blocks(md_text, mono_font="Courier"):
    """
    Parse markdown body into a list of typed blocks.

    Block types:
        {'type': 'h',       'level': 1-4,    'text': str}  <- ReportLab XML
        {'type': 'p',       'text': str}                    <- ReportLab XML
        {'type': 'list',    'ordered': bool, 'start': int,
                            'items': [{'text': str, 'level': 0|1|2,
                                       'ordered': bool, 'number': int|None}]}
        {'type': 'table',   'rows': [[str, ...], ...]}      <- cells are XML
        {'type': 'mermaid', 'content': str}
        {'type': 'code',    'lang': str, 'content': str}
        {'type': 'hr'}
        {'type': 'image',   'src': str, 'alt': str}         <- plain text

    A paragraph that contains only an image becomes an 'image' block. An
    image mixed with text stays inline and is replaced by its alt text.
    """
    md = mistune.create_markdown(renderer=None, plugins=["table", "strikethrough"])
    tokens = md(md_text) or []
    return _tokens_to_blocks(tokens, _Inline(mono_font))


class _Inline:
    """Inline renderer bound to the font used for `code spans`."""

    def __init__(self, mono_font="Courier"):
        self.mono_font = mono_font

    def __call__(self, children):
        return _inline_to_xml(children, self.mono_font)


def _tokens_to_blocks(tokens, _inline_to_xml=None):
    _inline_to_xml = _inline_to_xml or _Inline()
    blocks = []
    for tok in tokens:
        t = tok["type"]
        if t == "heading":
            level = min(tok["attrs"]["level"], 4)
            text = _inline_to_xml(tok.get("children", []))
            blocks.append({"type": "h", "level": level, "text": text})
        elif t == "paragraph":
            image = _sole_image(tok.get("children", []))
            if image is not None:
                blocks.append(image)
                continue
            text = _inline_to_xml(tok.get("children", []))
            blocks.append({"type": "p", "text": text})
        elif t == "block_code":
            info = ((tok.get("attrs") or {}).get("info") or "").strip().lower()
            content = tok.get("raw", "")
            if info == "mermaid":
                blocks.append({"type": "mermaid", "content": content})
            else:
                blocks.append({"type": "code", "lang": info, "content": content})
        elif t == "list":
            ordered, start = _list_attrs(tok)
            items = _list_items(tok.get("children", []), 0, ordered, start, _inline_to_xml)
            if items:
                blocks.append({"type": "list", "ordered": ordered, "start": start, "items": items})
        elif t == "table":
            rows = _table_rows(tok.get("children", []), _inline_to_xml)
            if rows:
                blocks.append({"type": "table", "rows": rows})
        elif t == "thematic_break":
            blocks.append({"type": "hr"})
        # block_html and unknown types are silently skipped
    return blocks


# Line-break tokens: mistune v3 names, plus the names used by older versions.
_BREAK_TOKENS = ("softbreak", "linebreak", "softline_break", "line_break")


def _sole_image(children):
    """Return an image block if the inline children are exactly one image."""
    meaningful = [
        c
        for c in children
        if c["type"] not in _BREAK_TOKENS
        and not (c["type"] == "text" and not c.get("raw", "").strip())
    ]
    if len(meaningful) != 1 or meaningful[0]["type"] != "image":
        return None
    tok = meaningful[0]
    src = unquote((tok.get("attrs") or {}).get("url", ""))
    if not src:
        return None
    return {"type": "image", "src": src, "alt": _plain_text(tok.get("children", []))}


def _plain_text(children):
    """Flatten inline tokens to plain text (no markup, no escaping)."""
    parts = []
    for child in children:
        if "children" in child:
            parts.append(_plain_text(child["children"]))
        elif child["type"] in _BREAK_TOKENS:
            parts.append(" ")
        elif child["type"] != "raw_html":
            parts.append(child.get("raw", ""))
    return "".join(parts)


def _list_attrs(tok):
    """Return (ordered, start) for a mistune list token."""
    attrs = tok.get("attrs") or {}
    ordered = bool(attrs.get("ordered"))
    start = attrs.get("start")
    return ordered, (start if isinstance(start, int) else 1)


def _list_items(children, depth, ordered=False, start=1, _inline_to_xml=None):
    """
    Flatten a (possibly nested) list into items. Every item carries the
    kind of the list it belongs to; numbering restarts in each nested list.
    """
    _inline_to_xml = _inline_to_xml or _Inline()
    items = []
    number = start
    for item in children:
        if item["type"] != "list_item":
            continue
        numbered = False
        for child in item.get("children", []):
            if child["type"] in ("block_text", "paragraph"):
                text = _inline_to_xml(child.get("children", []))
                entry = {
                    "text": text,
                    "level": min(depth, MAX_LIST_LEVEL),
                    "ordered": ordered,
                    "number": None,
                }
                # Only the first paragraph of an item gets the number.
                if ordered and not numbered:
                    entry["number"] = number
                    numbered = True
                items.append(entry)
            elif child["type"] == "list":
                sub_ordered, sub_start = _list_attrs(child)
                items.extend(
                    _list_items(
                        child.get("children", []),
                        depth + 1,
                        sub_ordered,
                        sub_start,
                        _inline_to_xml,
                    )
                )
        if ordered:
            number += 1
    return items


def _table_rows(children, _inline_to_xml=None):
    _inline_to_xml = _inline_to_xml or _Inline()
    rows = []
    for section in children:
        if section["type"] == "table_head":
            # Header cells sit directly in children (no table_row wrapper)
            cells = [
                _inline_to_xml(cell.get("children", []))
                for cell in section.get("children", [])
                if cell["type"] == "table_cell"
            ]
            if cells:
                rows.append(cells)
        elif section["type"] == "table_body":
            for row in section.get("children", []):
                if row["type"] != "table_row":
                    continue
                cells = [
                    _inline_to_xml(cell.get("children", []))
                    for cell in row.get("children", [])
                    if cell["type"] == "table_cell"
                ]
                if cells:
                    rows.append(cells)
    return rows


# ── Inline rendering ───────────────────────────────────────────────────────


def _xml_escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Link targets that are rendered as clickable links.
_LINKABLE_RE = re.compile(r"^(https?://|ftp://|mailto:|tel:)", re.IGNORECASE)


def _attr_escape(text):
    """Escape a value for use inside a double-quoted XML attribute."""
    return _xml_escape(text).replace('"', "&quot;").replace("'", "&#39;")


def _inline_to_xml(children, mono_font="Courier"):
    """Recursively convert inline AST tokens to ReportLab XML."""
    parts = []
    for child in children:
        t = child["type"]
        if t == "text":
            parts.append(_xml_escape(child.get("raw", "")))
        elif t == "strong":
            parts.append("<b>" + _inline_to_xml(child.get("children", []), mono_font) + "</b>")
        elif t == "emphasis":
            parts.append("<i>" + _inline_to_xml(child.get("children", []), mono_font) + "</i>")
        elif t == "strong_em":
            inner = _inline_to_xml(child.get("children", []), mono_font)
            parts.append(f"<b><i>{inner}</i></b>")
        elif t == "codespan":
            code = _xml_escape(child.get("raw", ""))
            parts.append(f'<font face="{mono_font}" size="9">{code}</font>')
        elif t in _BREAK_TOKENS:
            parts.append(" ")
        elif t == "link":
            label = _inline_to_xml(child.get("children", []), mono_font)
            url = ((child.get("attrs") or {}).get("url") or "").strip()
            if _LINKABLE_RE.match(url):
                parts.append(f'<a href="{_attr_escape(url)}">{label}</a>')
            else:
                # Anchors and relative paths have no target inside the PDF
                # (ReportLab would fail on the undefined destination), and
                # other schemes are not worth making clickable.
                parts.append(label)
        elif t == "image":
            # Inline image: only its alt text is kept. mistune v3 stores the
            # alt text as child tokens (older versions used attrs["alt"]).
            alt = _plain_text(child.get("children", [])) or (child.get("attrs") or {}).get(
                "alt", ""
            )
            parts.append(_xml_escape(alt))
        elif t == "raw_html":
            pass
        else:
            if "children" in child:
                parts.append(_inline_to_xml(child["children"], mono_font))
            elif "raw" in child:
                parts.append(_xml_escape(child["raw"]))
    return "".join(parts)


def inline(text):
    """
    Convert inline Markdown (**bold**, *italic*, `code`) to ReportLab XML.
    Safe to call on arbitrary text — & < > are properly escaped.
    """
    md = mistune.create_markdown(renderer=None)
    tokens = md(text) or []
    if tokens and tokens[0]["type"] == "paragraph":
        return _inline_to_xml(tokens[0].get("children", []))
    return _xml_escape(text)


# ── Language detection ─────────────────────────────────────────────────────


def detect_language(text):
    """
    Quick heuristic language detection from frequent stop-words.
    Returns one of: 'en', 'es', 'de', 'fr'.
    """
    t = text.lower()
    counts = {
        "es": len(
            re.findall(
                r"\b(el|la|los|las|del|por|para|con|una|como|este|esta|que|más|pero|también)\b", t
            )
        ),
        "en": len(
            re.findall(r"\b(the|and|for|with|this|that|from|are|was|has|our|can|will|have)\b", t)
        ),
        "de": len(
            re.findall(r"\b(der|die|das|und|für|mit|von|ist|den|auf|ein|des|nicht|sie)\b", t)
        ),
        "fr": len(
            re.findall(r"\b(le|la|les|des|et|pour|avec|dans|qui|que|une|pas|vous|nous)\b", t)
        ),
    }
    return max(counts, key=counts.get)

"""
Markdown parser for CorpDoc.

Uses mistune v3 as lexer for robust, spec-compliant parsing.
Produces typed block dicts consumed by api.py.
"""

import re
import mistune
import yaml


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


def parse_blocks(md_text):
    """
    Parse markdown body into a list of typed blocks.

    Block types:
        {'type': 'h',       'level': 1-4,    'text': str}  <- ReportLab XML
        {'type': 'p',       'text': str}                    <- ReportLab XML
        {'type': 'list',    'items': [{'text': str, 'level': 0|1}]}
        {'type': 'table',   'rows': [[str, ...], ...]}      <- cells are XML
        {'type': 'mermaid', 'content': str}
        {'type': 'code',    'lang': str, 'content': str}
        {'type': 'hr'}
    """
    md = mistune.create_markdown(renderer=None, plugins=["table", "strikethrough"])
    tokens = md(md_text) or []
    return _tokens_to_blocks(tokens)


def _tokens_to_blocks(tokens):
    blocks = []
    for tok in tokens:
        t = tok["type"]
        if t == "heading":
            level = min(tok["attrs"]["level"], 4)
            text = _inline_to_xml(tok.get("children", []))
            blocks.append({"type": "h", "level": level, "text": text})
        elif t == "paragraph":
            text = _inline_to_xml(tok.get("children", []))
            blocks.append({"type": "p", "text": text})
        elif t == "block_code":
            info = (tok["attrs"].get("info") or "").strip().lower()
            content = tok.get("raw", "")
            if info == "mermaid":
                blocks.append({"type": "mermaid", "content": content})
            else:
                blocks.append({"type": "code", "lang": info, "content": content})
        elif t == "list":
            items = _list_items(tok.get("children", []), depth=0)
            if items:
                blocks.append({"type": "list", "items": items})
        elif t == "table":
            rows = _table_rows(tok.get("children", []))
            if rows:
                blocks.append({"type": "table", "rows": rows})
        elif t == "thematic_break":
            blocks.append({"type": "hr"})
        # block_html and unknown types are silently skipped
    return blocks


def _list_items(children, depth):
    items = []
    for item in children:
        if item["type"] != "list_item":
            continue
        for child in item.get("children", []):
            if child["type"] in ("block_text", "paragraph"):
                text = _inline_to_xml(child.get("children", []))
                items.append({"text": text, "level": min(depth, 1)})
            elif child["type"] == "list":
                items.extend(_list_items(child.get("children", []), depth + 1))
    return items


def _table_rows(children):
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


def _inline_to_xml(children):
    """Recursively convert inline AST tokens to ReportLab XML."""
    parts = []
    for child in children:
        t = child["type"]
        if t == "text":
            parts.append(_xml_escape(child.get("raw", "")))
        elif t == "strong":
            parts.append("<b>" + _inline_to_xml(child.get("children", [])) + "</b>")
        elif t == "emphasis":
            parts.append("<i>" + _inline_to_xml(child.get("children", [])) + "</i>")
        elif t == "strong_em":
            inner = _inline_to_xml(child.get("children", []))
            parts.append(f"<b><i>{inner}</i></b>")
        elif t == "codespan":
            code = _xml_escape(child.get("raw", ""))
            parts.append(f'<font face="Courier" size="9">{code}</font>')
        elif t in ("softline_break", "line_break"):
            parts.append(" ")
        elif t == "link":
            parts.append(_inline_to_xml(child.get("children", [])))
        elif t == "image":
            parts.append(_xml_escape(child.get("attrs", {}).get("alt", "")))
        elif t == "raw_html":
            pass
        else:
            if "children" in child:
                parts.append(_inline_to_xml(child["children"]))
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

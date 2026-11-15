"""Small helpers shared by the CorpDoc modules."""

import sys

_TRUE_WORDS = {"true", "yes", "on", "1"}
_FALSE_WORDS = {"false", "no", "off", "0"}


def as_bool(value, default):
    """Read a config / frontmatter flag. Unrecognised values keep `default`."""
    if isinstance(value, bool):
        return value
    word = str(value).strip().lower()
    if word in _TRUE_WORDS:
        return True
    if word in _FALSE_WORDS:
        return False
    return default


def warn(message):
    """Print a warning on stderr. A render never fails because of a warning."""
    print(f"Warning: {message}", file=sys.stderr)


def xml_escape(text):
    """Escape text for ReportLab paragraph markup."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

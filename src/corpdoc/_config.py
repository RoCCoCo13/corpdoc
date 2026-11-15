"""Small helpers for reading config and frontmatter values."""

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

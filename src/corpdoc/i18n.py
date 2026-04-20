"""
Localized strings for CorpDoc.

All user-visible labels rendered inside PDFs live here, keyed by a stable
symbolic name. Supported language codes: 'en', 'es', 'de', 'fr'.

To add a new language, add a new top-level key to LANGUAGES with the same
sub-keys as existing ones.
"""

SUPPORTED = ("en", "es", "de", "fr")
DEFAULT = "en"


LANGUAGES = {
    "en": {
        "toc_title": "Table of Contents",
        "version_history_title": "Document Version History",
        "version_history_headers": ["Version", "Date", "Author", "Description"],
        "initial_version": "Initial version",
        "page": "Page",
        "of": "of",
    },
    "es": {
        "toc_title": "Índice",
        "version_history_title": "Control de Versiones",
        "version_history_headers": ["Versión", "Fecha", "Autor", "Descripción"],
        "initial_version": "Versión inicial",
        "page": "Página",
        "of": "de",
    },
    "de": {
        "toc_title": "Inhaltsverzeichnis",
        "version_history_title": "Versionsverlauf",
        "version_history_headers": ["Version", "Datum", "Autor", "Beschreibung"],
        "initial_version": "Erstversion",
        "page": "Seite",
        "of": "von",
    },
    "fr": {
        "toc_title": "Table des Matières",
        "version_history_title": "Historique des Versions",
        "version_history_headers": ["Version", "Date", "Auteur", "Description"],
        "initial_version": "Version initiale",
        "page": "Page",
        "of": "sur",
    },
}


def t(lang, key):
    """
    Look up a localized string. Falls back to the default language if the
    requested language or key is missing.
    """
    table = LANGUAGES.get(lang) or LANGUAGES[DEFAULT]
    if key in table:
        return table[key]
    return LANGUAGES[DEFAULT][key]

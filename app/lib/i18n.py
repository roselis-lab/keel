"""Request locale handling."""
from fastapi import Request

SUPPORTED_LOCALES = {"en", "ru"}
DEFAULT_LOCALE = "ru"


def parse_accept_language(header: str) -> list[str]:
    """Parse an Accept-Language header into a list of base locale codes.

    "ru-RU, en-US;q=0.9" -> ["ru", "en"]
    """
    if not header:
        return []
    locales = []
    for part in header.split(","):
        tag = part.split(";")[0].strip()
        base = tag.split("-")[0].lower()
        if base:
            locales.append(base)
    return locales


def get_request_locale(request: Request) -> str:
    """Determine locale: ?lang= override, then Accept-Language, then default."""
    lang = request.query_params.get("lang")
    if lang and lang.lower() in SUPPORTED_LOCALES:
        return lang.lower()
    for locale in parse_accept_language(request.headers.get("Accept-Language", "")):
        if locale in SUPPORTED_LOCALES:
            return locale
    return DEFAULT_LOCALE

QUOTA_ERROR_MESSAGE = (
    "Gemini API quota exceeded. Please try again later or switch to another available model/API key."
)

try:
    from google.api_core.exceptions import ResourceExhausted, TooManyRequests

    _QUOTA_EXCEPTION_TYPES = (ResourceExhausted, TooManyRequests)
except ImportError:  # pragma: no cover - google-api-core is a dependency of langchain-google-genai
    _QUOTA_EXCEPTION_TYPES = ()


def _iter_exception_chain(error):
    """
    Walk an exception and everything it was raised from.
    The LangChain Gemini wrappers often re-raise the original Google error
    as the __cause__ of their own exception type.
    """
    seen = set()
    while error is not None and id(error) not in seen:
        seen.add(id(error))
        yield error
        error = error.__cause__ or error.__context__


def is_quota_error(error):
    """
    Return True if an exception means the Gemini API quota / rate limit was hit.
    Checks exception types and HTTP status codes first, then falls back to
    matching the error message.
    """
    for exc in _iter_exception_chain(error):
        if _QUOTA_EXCEPTION_TYPES and isinstance(exc, _QUOTA_EXCEPTION_TYPES):
            return True

        for attr in ("code", "status_code"):
            value = getattr(exc, attr, None)
            if value == 429 or getattr(value, "value", None) == 429:
                return True

    message = str(error)
    return (
        "429" in message
        or "quota" in message.lower()
        or "ResourceExhausted" in message
        or "RESOURCE_EXHAUSTED" in message
    )

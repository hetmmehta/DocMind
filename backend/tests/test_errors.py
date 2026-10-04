from google.api_core.exceptions import InvalidArgument, ResourceExhausted, TooManyRequests

from services.errors import is_quota_error


class FakeHttpError(Exception):
    def __init__(self, status_code):
        super().__init__("request failed")
        self.status_code = status_code


def test_detects_google_quota_exception_types():
    assert is_quota_error(ResourceExhausted("quota"))
    assert is_quota_error(TooManyRequests("slow down"))


def test_detects_quota_error_wrapped_by_langchain():
    try:
        try:
            raise ResourceExhausted("Resource has been exhausted")
        except ResourceExhausted as e:
            raise ValueError("Error embedding content") from e
    except ValueError as wrapped:
        assert is_quota_error(wrapped)


def test_detects_http_429_status_code():
    assert is_quota_error(FakeHttpError(429))
    assert not is_quota_error(FakeHttpError(500))


def test_falls_back_to_message_matching():
    assert is_quota_error(RuntimeError("RESOURCE_EXHAUSTED: You exceeded your current quota"))


def test_other_errors_are_not_quota_errors():
    assert not is_quota_error(InvalidArgument("bad request"))
    assert not is_quota_error(RuntimeError("connection reset"))

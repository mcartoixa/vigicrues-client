"""Errors raised by the client."""


class VigicruesError(Exception):
    """Base class of the errors raised by the client."""


class VigicruesConnectionError(VigicruesError):
    """The Vigicrues service could not be reached or did not answer in time."""


class VigicruesRateLimitError(VigicruesError):
    """The Vigicrues service refused the request: too many requests (HTTP 429)."""


class VigicruesResponseError(VigicruesError):
    """The Vigicrues service sent an unexpected response.

    For instance an HTTP error status, an HTML page instead of JSON, or invalid JSON.
    """


class VigicruesApiError(VigicruesError):
    """The Vigicrues service reported an error in its response.

    Args:
        message: Error message from the service, in French.
        code: Error code from the service, if any.
    """

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message if code is None else f"{message} (code {code})")
        self.message = message
        self.code = code


class VigicruesNotFoundError(VigicruesApiError):
    """The Vigicrues service does not know the requested entity, e.g. a station."""

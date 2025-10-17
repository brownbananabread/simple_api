class InvalidUUIDError(ValueError):
    """Raised when an invalid UUID is provided."""

    pass


class PayloadTooLargeError(ValueError):
    """Raised when the request payload is too large."""

    pass

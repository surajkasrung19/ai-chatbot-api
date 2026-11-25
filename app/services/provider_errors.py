
class ChatProviderError(Exception):
    """A safe, provider-independent AI service error."""

    def __init__(
        self,
        detail: str,
        status_code: int = 502,
        code: str = "provider_error"
    ) -> None:
        super().__init__(detail)

        self.detail = detail
        self.status_code = status_code
        self.code = code

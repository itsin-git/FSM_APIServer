from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class FortiSIEMError(Exception):
    """Raised when the upstream FortiSIEM returns an error."""

    def __init__(self, message: str, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UpstreamTimeoutError(FortiSIEMError):
    def __init__(self, message: str = "Upstream FortiSIEM request timed out"):
        super().__init__(message, status_code=504)


class UpstreamSSLError(FortiSIEMError):
    def __init__(self, message: str = "SSL certificate validation failed"):
        super().__init__(message, status_code=502)


class QueryStillInProgressError(FortiSIEMError):
    def __init__(self, query_id: str = ""):
        msg = f"Query {query_id} did not complete within the polling window"
        super().__init__(msg, status_code=504)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(FortiSIEMError)
    async def fortisiem_error_handler(request: Request, exc: FortiSIEMError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )

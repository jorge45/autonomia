import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_CODIGOS_HTTP = {
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
}


class ApiError(Exception):
    def __init__(
        self,
        codigo: str,
        mensaje: str,
        status_code: int,
        detalles: list[dict] | None = None,
    ):
        self.codigo = codigo
        self.mensaje = mensaje
        self.status_code = status_code
        self.detalles = detalles
        super().__init__(mensaje)


def _error_body(codigo: str, mensaje: str, detalles: list[dict] | None = None) -> dict:
    error = {"codigo": codigo, "mensaje": mensaje}
    if detalles is not None:
        error["detalles"] = detalles
    return {"error": error}


def register_exception_handlers(app: FastAPI, logger: logging.Logger) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        logger.warning(
            {
                "evento": "api_error",
                "codigo": exc.codigo,
                "ruta": request.url.path,
                "status": exc.status_code,
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.codigo, exc.mensaje, exc.detalles),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        detalles = [
            {
                "campo": ".".join(str(p) for p in err["loc"] if p != "body"),
                "mensaje": err["msg"],
            }
            for err in exc.errors()
        ]
        logger.warning(
            {
                "evento": "api_error",
                "codigo": "VALIDATION_ERROR",
                "ruta": request.url.path,
                "status": 422,
            }
        )
        return JSONResponse(
            status_code=422,
            content=_error_body(
                "VALIDATION_ERROR", "Error de validación en la solicitud", detalles
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        codigo = _CODIGOS_HTTP.get(exc.status_code, "HTTP_ERROR")
        mensaje = str(exc.detail)
        logger.warning(
            {
                "evento": "api_error",
                "codigo": codigo,
                "ruta": request.url.path,
                "status": exc.status_code,
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(codigo, mensaje),
        )

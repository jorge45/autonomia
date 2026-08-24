import time

from fastapi import FastAPI, Request

from api_propia.config import get_settings
from api_propia.errors import register_exception_handlers
from api_propia.logging_config import configure_logging
from api_propia.routes_catalogo import router as catalogo_router
from api_propia.routes_solicitudes import router as solicitudes_router

settings = get_settings()
logger = configure_logging(settings.log_level)

app = FastAPI(title="API REST de solicitudes")

register_exception_handlers(app, logger)
app.include_router(solicitudes_router)
app.include_router(catalogo_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duracion_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        {
            "evento": "request",
            "metodo": request.method,
            "ruta": request.url.path,
            "status": response.status_code,
            "duracion_ms": duracion_ms,
        }
    )
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_propia.main:app", host=settings.host, port=settings.port)

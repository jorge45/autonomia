import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Query, status

from api_propia.errors import ApiError
from api_propia.models import Solicitud, SolicitudEntrada

router = APIRouter()

SOLICITUDES: dict[str, Solicitud] = {}


@router.post("/solicitudes", status_code=status.HTTP_201_CREATED)
def crear_solicitud(entrada: SolicitudEntrada) -> Solicitud:
    solicitud = Solicitud(
        **entrada.model_dump(),
        id_solicitud=str(uuid.uuid4()),
        estado="recibida",
        fecha_creacion=datetime.now(timezone.utc),
    )
    SOLICITUDES[solicitud.id_solicitud] = solicitud
    return solicitud


@router.get("/solicitudes")
def listar_solicitudes(
    area: str | None = None,
    estado: str | None = None,
    limite: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Solicitud]:
    resultados = list(SOLICITUDES.values())
    if area is not None:
        resultados = [s for s in resultados if s.area == area]
    if estado is not None:
        resultados = [s for s in resultados if s.estado == estado]
    return resultados[offset : offset + limite]


@router.get("/solicitudes/{id_solicitud}")
def obtener_solicitud(id_solicitud: str) -> Solicitud:
    solicitud = SOLICITUDES.get(id_solicitud)
    if solicitud is None:
        raise ApiError(
            codigo="NOT_FOUND",
            mensaje=f"No existe una solicitud con id '{id_solicitud}'.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return solicitud

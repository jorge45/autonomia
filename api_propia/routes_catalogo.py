from fastapi import APIRouter, status

from api_propia.errors import ApiError
from api_propia.models import AREAS_SEED, USUARIOS_SEED, Area, Usuario

router = APIRouter()


@router.get("/areas")
def listar_areas() -> list[Area]:
    return list(AREAS_SEED.values())


@router.get("/areas/{id_area}")
def obtener_area(id_area: int) -> Area:
    area = AREAS_SEED.get(id_area)
    if area is None:
        raise ApiError(
            codigo="NOT_FOUND",
            mensaje=f"No existe un área con id '{id_area}'.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return area


@router.get("/usuarios")
def listar_usuarios() -> list[Usuario]:
    return list(USUARIOS_SEED.values())


@router.get("/usuarios/{id_usuario}")
def obtener_usuario(id_usuario: int) -> Usuario:
    usuario = USUARIOS_SEED.get(id_usuario)
    if usuario is None:
        raise ApiError(
            codigo="NOT_FOUND",
            mensaje=f"No existe un usuario con id '{id_usuario}'.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return usuario

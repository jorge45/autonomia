from dataclasses import dataclass

CATEGORIAS_VALIDAS = ["incidente", "acceso", "hardware", "software", "otro"]
PRIORIDADES_VALIDAS = ["baja", "media", "alta", "urgente"]

CATEGORIA_DEGRADADA = "otro"
PRIORIDAD_DEGRADADA = "media"


@dataclass(frozen=True)
class ResultadoClasificacion:
    categoria: str
    prioridad: str
    origen: str

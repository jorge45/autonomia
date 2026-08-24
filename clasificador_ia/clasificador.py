import json
import time

import anthropic

from clasificador_ia.cliente import construir_cliente
from clasificador_ia.config import BACKOFF_BASE_SEGUNDOS, MAX_REINTENTOS, MODELO
from clasificador_ia.logging_config import configure_logging
from clasificador_ia.modelos import (
    CATEGORIA_DEGRADADA,
    CATEGORIAS_VALIDAS,
    PRIORIDAD_DEGRADADA,
    PRIORIDADES_VALIDAS,
    ResultadoClasificacion,
)

logger = configure_logging()

ESQUEMA_RESPUESTA = {
    "type": "object",
    "properties": {
        "categoria": {"type": "string", "enum": CATEGORIAS_VALIDAS},
        "prioridad": {"type": "string", "enum": PRIORIDADES_VALIDAS},
    },
    "required": ["categoria", "prioridad"],
    "additionalProperties": False,
}


def _armar_prompt(asunto: str, descripcion: str | None) -> str:
    partes = [f"Asunto: {asunto}"]
    if descripcion:
        partes.append(f"Descripción: {descripcion}")
    partes.append(
        "Clasifica esta solicitud de mesa de ayuda asignando una categoría y una prioridad."
    )
    return "\n".join(partes)


def _llamar_ia(cliente: anthropic.Anthropic, asunto: str, descripcion: str | None):
    mensaje = cliente.messages.create(
        model=MODELO,
        max_tokens=1024,
        messages=[{"role": "user", "content": _armar_prompt(asunto, descripcion)}],
        output_config={
            "format": {"type": "json_schema", "schema": ESQUEMA_RESPUESTA}
        },
    )
    datos = json.loads(mensaje.content[0].text)
    return datos["categoria"], datos["prioridad"]


def clasificar_solicitud(
    asunto: str, descripcion: str | None
) -> ResultadoClasificacion:
    cliente = construir_cliente()
    inicio = time.monotonic()

    for intento in range(1, MAX_REINTENTOS + 2):
        try:
            categoria, prioridad = _llamar_ia(cliente, asunto, descripcion)
            duracion_ms = (time.monotonic() - inicio) * 1000
            logger.info(
                {
                    "evento": "clasificacion_ia",
                    "origen": "ia",
                    "categoria": categoria,
                    "prioridad": prioridad,
                    "intentos": intento,
                    "duracion_ms": duracion_ms,
                }
            )
            return ResultadoClasificacion(
                categoria=categoria, prioridad=prioridad, origen="ia"
            )
        except anthropic.APIError as error:
            es_ultimo_intento = intento == MAX_REINTENTOS + 1
            if es_ultimo_intento:
                break
            logger.warning(
                {
                    "evento": "clasificacion_ia_reintento",
                    "intento": intento,
                    "motivo": str(error) or type(error).__name__,
                }
            )
            time.sleep(BACKOFF_BASE_SEGUNDOS * (2 ** (intento - 1)))

    logger.warning(
        {
            "evento": "clasificacion_ia_degradado",
            "intentos": MAX_REINTENTOS + 1,
            "categoria": CATEGORIA_DEGRADADA,
            "prioridad": PRIORIDAD_DEGRADADA,
        }
    )
    return ResultadoClasificacion(
        categoria=CATEGORIA_DEGRADADA,
        prioridad=PRIORIDAD_DEGRADADA,
        origen="degradado",
    )

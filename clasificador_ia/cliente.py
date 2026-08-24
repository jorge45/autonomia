import os

import anthropic

from clasificador_ia.config import TIMEOUT_SEGUNDOS, ConfiguracionInvalida


def construir_cliente() -> anthropic.Anthropic:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ConfiguracionInvalida(
            "Falta la variable de entorno ANTHROPIC_API_KEY."
        )
    return anthropic.Anthropic(timeout=TIMEOUT_SEGUNDOS)

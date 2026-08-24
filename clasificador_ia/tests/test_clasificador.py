import json
from unittest.mock import MagicMock

import anthropic
import pytest

from clasificador_ia.clasificador import clasificar_solicitud
from clasificador_ia.config import ConfiguracionInvalida
from clasificador_ia.modelos import CATEGORIAS_VALIDAS, PRIORIDADES_VALIDAS


def _respuesta_ia(categoria: str, prioridad: str) -> MagicMock:
    bloque = MagicMock()
    bloque.text = json.dumps({"categoria": categoria, "prioridad": prioridad})
    mensaje = MagicMock()
    mensaje.content = [bloque]
    return mensaje


def _error_api() -> anthropic.APIConnectionError:
    return anthropic.APIConnectionError(request=MagicMock())


@pytest.fixture(autouse=True)
def sin_espera_real(monkeypatch):
    monkeypatch.setattr("clasificador_ia.clasificador.time.sleep", lambda s: None)


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba")


def test_clasificacion_exitosa_primer_intento(monkeypatch, api_key):
    cliente = MagicMock()
    cliente.messages.create.return_value = _respuesta_ia("incidente", "alta")
    monkeypatch.setattr(
        "clasificador_ia.clasificador.construir_cliente", lambda: cliente
    )

    resultado = clasificar_solicitud(
        "Impresora no enciende", "La impresora del piso 3 no responde"
    )

    assert resultado.origen == "ia"
    assert resultado.categoria in CATEGORIAS_VALIDAS
    assert resultado.prioridad in PRIORIDADES_VALIDAS
    assert resultado.categoria == "incidente"
    assert resultado.prioridad == "alta"
    assert cliente.messages.create.call_count == 1


def test_exito_tras_reintento(monkeypatch, api_key):
    cliente = MagicMock()
    cliente.messages.create.side_effect = [
        _error_api(),
        _respuesta_ia("software", "media"),
    ]
    monkeypatch.setattr(
        "clasificador_ia.clasificador.construir_cliente", lambda: cliente
    )

    resultado = clasificar_solicitud("No abre el programa", "Falla al iniciar")

    assert resultado.origen == "ia"
    assert resultado.categoria == "software"
    assert resultado.prioridad == "media"
    assert cliente.messages.create.call_count == 2


def test_agotamiento_reintentos_devuelve_degradado(monkeypatch, api_key):
    cliente = MagicMock()
    cliente.messages.create.side_effect = [_error_api(), _error_api(), _error_api()]
    monkeypatch.setattr(
        "clasificador_ia.clasificador.construir_cliente", lambda: cliente
    )

    resultado = clasificar_solicitud("Solicitud genérica", None)

    assert resultado.origen == "degradado"
    assert resultado.categoria == "otro"
    assert resultado.prioridad == "media"
    assert cliente.messages.create.call_count == 3


def test_sin_api_key_lanza_configuracion_invalida(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ConfiguracionInvalida):
        clasificar_solicitud("Asunto cualquiera", None)

import pytest
from fastapi.testclient import TestClient

from api_propia.main import app
from api_propia.routes_solicitudes import SOLICITUDES


@pytest.fixture(autouse=True)
def limpiar_solicitudes():
    SOLICITUDES.clear()
    yield
    SOLICITUDES.clear()


@pytest.fixture
def client():
    return TestClient(app)

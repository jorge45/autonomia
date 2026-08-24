def test_listar_areas_devuelve_8(client):
    r = client.get("/areas")
    assert r.status_code == 200
    assert len(r.json()) == 8


def test_obtener_area_existente_devuelve_200(client):
    r = client.get("/areas/1")
    assert r.status_code == 200
    assert r.json()["id_area"] == 1


def test_obtener_area_inexistente_devuelve_404(client):
    r = client.get("/areas/9999")
    assert r.status_code == 404
    assert r.json()["error"]["codigo"] == "NOT_FOUND"


def test_listar_usuarios_devuelve_40(client):
    r = client.get("/usuarios")
    assert r.status_code == 200
    assert len(r.json()) == 40


def test_obtener_usuario_existente_devuelve_200(client):
    r = client.get("/usuarios/1")
    assert r.status_code == 200
    assert r.json()["id_usuario"] == 1


def test_obtener_usuario_inexistente_devuelve_404(client):
    r = client.get("/usuarios/9999")
    assert r.status_code == 404
    assert r.json()["error"]["codigo"] == "NOT_FOUND"


def test_ruta_inexistente_devuelve_forma_uniforme(client):
    r = client.get("/no-existe-esta-ruta")
    assert r.status_code == 404
    assert r.json()["error"]["codigo"] == "NOT_FOUND"


def test_metodo_no_permitido_devuelve_forma_uniforme(client):
    r = client.delete("/solicitudes")
    assert r.status_code == 405
    assert r.json()["error"]["codigo"] == "METHOD_NOT_ALLOWED"

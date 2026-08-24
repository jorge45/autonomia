from api_propia.routes_solicitudes import SOLICITUDES


def test_crear_solicitud_valida_devuelve_201(client):
    r = client.post(
        "/solicitudes",
        json={
            "asunto": "Solicitud de prueba",
            "area": "Infraestructura",
            "solicitante": "Juan Perez",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["estado"] == "recibida"
    assert "id_solicitud" in body
    assert "fecha_creacion" in body


def test_crear_solicitud_asunto_corto_devuelve_422(client):
    r = client.post(
        "/solicitudes",
        json={
            "asunto": "abc",
            "area": "Infraestructura",
            "solicitante": "Juan Perez",
        },
    )
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["codigo"] == "VALIDATION_ERROR"
    campos = [d["campo"] for d in body["error"]["detalles"]]
    assert "asunto" in campos


def test_crear_solicitud_sin_solicitante_devuelve_422(client):
    r = client.post(
        "/solicitudes",
        json={
            "asunto": "Solicitud de prueba valida",
            "area": "Infraestructura",
        },
    )
    assert r.status_code == 422
    assert r.json()["error"]["codigo"] == "VALIDATION_ERROR"


def test_obtener_solicitud_existente_devuelve_200(client):
    creada = client.post(
        "/solicitudes",
        json={
            "asunto": "Solicitud de prueba valida",
            "area": "Infraestructura",
            "solicitante": "Juan Perez",
        },
    ).json()
    r = client.get(f"/solicitudes/{creada['id_solicitud']}")
    assert r.status_code == 200
    assert r.json()["id_solicitud"] == creada["id_solicitud"]


def test_obtener_solicitud_inexistente_devuelve_404(client):
    r = client.get("/solicitudes/no-existe")
    assert r.status_code == 404
    assert r.json()["error"]["codigo"] == "NOT_FOUND"


def test_listar_con_filtro_area(client):
    client.post(
        "/solicitudes",
        json={"asunto": "Solicitud A valida", "area": "Infraestructura", "solicitante": "Persona Uno"},
    )
    client.post(
        "/solicitudes",
        json={"asunto": "Solicitud B valida", "area": "Contabilidad", "solicitante": "Persona Dos"},
    )
    r = client.get("/solicitudes", params={"area": "Infraestructura"})
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["area"] == "Infraestructura"


def test_listar_con_filtro_estado(client):
    id1 = client.post(
        "/solicitudes",
        json={"asunto": "Solicitud A valida", "area": "Infraestructura", "solicitante": "Persona Uno"},
    ).json()["id_solicitud"]
    client.post(
        "/solicitudes",
        json={"asunto": "Solicitud B valida", "area": "Contabilidad", "solicitante": "Persona Dos"},
    )
    SOLICITUDES[id1].estado = "en_proceso"

    r = client.get("/solicitudes", params={"estado": "en_proceso"})
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["estado"] == "en_proceso"


def test_listar_con_paginacion(client):
    for i in range(3):
        client.post(
            "/solicitudes",
            json={
                "asunto": f"Solicitud numero {i} valida",
                "area": "Infraestructura",
                "solicitante": "Persona Prueba",
            },
        )
    r0 = client.get("/solicitudes", params={"limite": 1, "offset": 0})
    r1 = client.get("/solicitudes", params={"limite": 1, "offset": 1})
    assert len(r0.json()) == 1
    assert len(r1.json()) == 1
    assert r0.json()[0]["id_solicitud"] != r1.json()[0]["id_solicitud"]


def test_listar_limite_excede_maximo_devuelve_422(client):
    r = client.get("/solicitudes", params={"limite": 500})
    assert r.status_code == 422
    assert r.json()["error"]["codigo"] == "VALIDATION_ERROR"

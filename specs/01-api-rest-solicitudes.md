# SPEC 01 — API REST propia de solicitudes

> **Status:** Approved
> **Depends on:** ninguna
> **Date:** 2026-08-24
> **Objective:** Construir un API REST propia con los recursos `solicitudes`, `areas` y `usuarios`, con validación de entrada, códigos de estado correctos, forma uniforme de errores, configuración por variables de entorno, registro estructurado de eventos, ningún secreto en el repositorio, y documentación técnica y funcional en el README.

## Por qué existe este spec

Este API es un entregable propio de la Prueba Técnica de Nivelación (`materiales/`). No modifica ni depende de `materiales/servicio_mock`, pero reutiliza a propósito el mismo esquema de entrada de `SolicitudEntrada` (definido en `materiales/servicio_mock/openapi.yaml`) y los datos semilla de `materiales/datos/esquema.sql`, para mantener consistencia de dominio ("Mesa de Ayuda") sin tocar los archivos de `materiales/`, que son solo insumos de la prueba.

## Scope

**In:**

- Recurso `solicitudes`: crear (`POST`), consultar por id (`GET`), listar con filtros y paginación (`GET`).
- Recurso `areas`: listar (`GET`) y consultar por id (`GET`), solo lectura.
- Recurso `usuarios`: listar (`GET`) y consultar por id (`GET`), solo lectura.
- Validación de entrada en la creación de solicitudes (tipos, longitudes, campos requeridos).
- Códigos de estado HTTP correctos por caso (200, 201, 404, 422, etc.).
- Forma uniforme de error para toda respuesta 4xx/5xx.
- Datos en memoria, sembrados al arrancar la aplicación (sin base de datos real).
- Suite de pruebas automatizadas con pytest que verifica validación, códigos de estado y forma de error.
- Configuración de la aplicación (`HOST`, `PORT`, `LOG_LEVEL`) leída desde variables de entorno, con valores por defecto si no están definidas.
- Registro estructurado de eventos (JSON por stdout): un log por cada petición HTTP (método, ruta, status, duración) y un log adicional por cada `ApiError` lanzado (con su `codigo`).
- Ningún secreto en el repositorio: `.env.example` con las variables documentadas (sin valores reales), `.env` real ignorado vía `.gitignore`. No hay secretos que gestionar aún porque no hay auth (ver Out of scope), pero se deja la convención lista.
- README (`api_propia/README.md`) con documentación técnica (contrato del API: endpoints, esquemas de request/response, códigos de estado, forma de error, variables de entorno) y documentación funcional (qué problema resuelve, para quién — mesa de ayuda / colaboradores que reportan solicitudes — y qué NO cubre).

**Out of scope (for future specs):**

- Autenticación/autorización (Bearer token u otro esquema).
- Persistencia real (SQLite, MySQL u otro motor).
- Actualización (`PUT`/`PATCH`) o borrado (`DELETE`) de solicitudes.
- Integración o consumo real de `materiales/servicio_mock` (el mock simula un proveedor externo; este spec no lo llama).
- Rate limiting, idempotencia (`Idempotency-Key`) u otros mecanismos de resiliencia del lado del cliente.
- Webhooks o notificaciones (recordatorios, escalamientos).
- Envío de logs a un colector externo (ELK, Datadog, etc.) — por ahora solo stdout.
- Variables de entorno para límites de paginación (quedan hardcodeadas: default 50, max 200).

## Data model

```python
# api_propia/models.py (Pydantic)

class SolicitudEntrada(BaseModel):
    asunto: str        # min_length=5, max_length=200
    descripcion: str | None = None  # max_length=4000
    area: str          # min_length=2, max_length=80
    solicitante: str   # min_length=5, max_length=120
    canal: str = "api"

class Solicitud(SolicitudEntrada):
    id_solicitud: str   # uuid4 como string
    estado: str          # "recibida" | "en_proceso" | "resuelta" | "cerrada"
    fecha_creacion: datetime

class Area(BaseModel):
    id_area: int
    nombre: str
    sede: str
    responsable: str | None = None

class Usuario(BaseModel):
    id_usuario: int
    correo: str
    nombre: str
    id_area: int
    activo: bool
```

Estados válidos de una solicitud: `recibida`, `en_proceso`, `resuelta`, `cerrada`. Toda solicitud se crea en estado `recibida`.

Datos semilla de `areas` y `usuarios`: los mismos valores de `materiales/datos/esquema.sql` (8 áreas, usuarios asociados), copiados como constantes en memoria — sin leer el `.sql` en tiempo de ejecución.

Almacén en memoria: diccionarios Python a nivel de módulo (`dict[str, Solicitud]`, `dict[int, Area]`, `dict[int, Usuario]`), reiniciados al reiniciar el proceso.

Configuración (`api_propia/config.py`):

```python
class Settings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

def get_settings() -> Settings:
    return Settings(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
```

`.env.example` (documentativo, sin valores reales, sí versionado):

```
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

`.env` real: ignorado vía `.gitignore` (nunca contiene secretos en este spec, pero queda la convención lista para cuando se agregue auth).

Línea de log estructurado (JSON por stdout), un objeto por evento:

```json
{"timestamp": "2026-08-24T10:00:00Z", "level": "INFO", "evento": "request", "metodo": "POST", "ruta": "/solicitudes", "status": 201, "duracion_ms": 4.2}
{"timestamp": "2026-08-24T10:00:01Z", "level": "WARNING", "evento": "api_error", "codigo": "VALIDATION_ERROR", "ruta": "/solicitudes", "status": 422}
```

Forma uniforme de error:

```python
{
  "error": {
    "codigo": "VALIDATION_ERROR",   # string estable, mayúsculas y guion bajo
    "mensaje": "descripción legible del error",
    "detalles": [ { "campo": "asunto", "mensaje": "..." } ]  # opcional, solo en errores de validación
  }
}
```

## Implementation plan

1. Crear `api_propia/` con `requirements.txt` (fastapi, uvicorn, pytest, httpx), `.env.example` y `.gitignore` (con `.env`). Crear `api_propia/config.py` con `Settings`/`get_settings()` leyendo `HOST`, `PORT`, `LOG_LEVEL` desde entorno con defaults. Prueba manual: `python -c "from api_propia.config import get_settings; print(get_settings())"` muestra los defaults.
2. Crear `api_propia/logging_config.py`: un `logging.Formatter` que emite JSON por stdout, configurado con el `log_level` de `Settings`. Crear `main.py` con la app FastAPI vacía, `GET /health`, y un middleware que loguee cada request (método, ruta, status, duración) como evento `request`. Prueba manual: `uvicorn api_propia.main:app --reload` responde 200 en `/health` y en stdout aparece una línea JSON con `evento="request"`.
3. Crear `api_propia/models.py` con los modelos Pydantic (`SolicitudEntrada`, `Solicitud`, `Area`, `Usuario`) y los datos semilla de `areas`/`usuarios` como constantes.
4. Crear `api_propia/errors.py`: excepción `ApiError(codigo, mensaje, status_code, detalles=None)` y un `exception_handler` de FastAPI que la serializa en la forma uniforme y loguea un evento `api_error` (JSON, con `codigo`, `ruta`, `status`). Registrar también un handler para `RequestValidationError` de FastAPI que la traduzca a la misma forma (`codigo="VALIDATION_ERROR"`, `detalles` con campo por campo) y también loguee `api_error`.
5. Implementar `POST /solicitudes` y `GET /solicitudes/{id_solicitud}` en `api_propia/routes_solicitudes.py`, usando el almacén en memoria. Prueba manual: crear una solicitud y consultarla por id devuelve 201 y 200 respectivamente; un id inexistente devuelve 404 con la forma uniforme.
6. Implementar `GET /solicitudes` con filtros `area`, `estado` y paginación `limite` (default 50, max 200) / `offset` (default 0). Prueba manual: crear varias solicitudes de distintas áreas/estados y verificar que los filtros y la paginación acotan correctamente el resultado.
7. Implementar `GET /areas`, `GET /areas/{id_area}`, `GET /usuarios`, `GET /usuarios/{id_usuario}` en `api_propia/routes_catalogo.py`, leyendo de las constantes sembradas. Prueba manual: listar y consultar por id, un id inexistente devuelve 404 con la forma uniforme.
8. Registrar los routers en `main.py`, usando `get_settings()` para `host`/`port` al arrancar uvicorn. Escribir `api_propia/README.md` con: (a) documentación funcional — qué problema resuelve (registro y consulta de solicitudes de la mesa de ayuda) y para quién (colaboradores que reportan solicitudes, equipo de mesa de ayuda que las consulta/filtra); (b) documentación técnica — el contrato completo del API (cada endpoint, parámetros, esquema de request/response, códigos de estado posibles, forma de error), variables de entorno soportadas, y cómo correr/loguear/testear el proyecto.
9. Crear `api_propia/tests/test_solicitudes.py` y `api_propia/tests/test_catalogo.py` con `pytest` + `TestClient`, cubriendo: creación válida (201), validación fallida por campo (422 + forma uniforme), consulta inexistente (404 + forma uniforme), listado con filtros y paginación, listado/consulta de `areas` y `usuarios`. Añadir `api_propia/tests/test_config.py` verificando que `get_settings()` respeta variables de entorno sobreescritas y usa defaults si no están.

## Acceptance criteria

- [ ] `GET /health` responde `200`.
- [ ] `POST /solicitudes` con cuerpo válido responde `201` y el cuerpo incluye `id_solicitud` (uuid), `estado="recibida"` y `fecha_creacion`.
- [ ] `POST /solicitudes` con `asunto` de menos de 5 caracteres responde `422` con la forma `{ "error": { "codigo": "VALIDATION_ERROR", "mensaje": ..., "detalles": [...] } }` donde `detalles` incluye `"campo": "asunto"`.
- [ ] `POST /solicitudes` sin el campo requerido `solicitante` responde `422` con la misma forma uniforme.
- [ ] `GET /solicitudes/{id_solicitud}` con un id existente responde `200` con la solicitud completa.
- [ ] `GET /solicitudes/{id_solicitud}` con un id inexistente responde `404` con `{ "error": { "codigo": "NOT_FOUND", "mensaje": ... } }`.
- [ ] `GET /solicitudes?area=X` devuelve solo las solicitudes de esa área.
- [ ] `GET /solicitudes?estado=en_proceso` devuelve solo las solicitudes en ese estado.
- [ ] `GET /solicitudes?limite=1&offset=1` devuelve exactamente 1 resultado, distinto del que devuelve `offset=0`.
- [ ] `GET /solicitudes?limite=500` responde `422` (excede el máximo de 200) con la forma uniforme.
- [ ] `GET /areas` responde `200` con las 8 áreas sembradas.
- [ ] `GET /areas/{id_area}` con un id inexistente responde `404` con la forma uniforme.
- [ ] `GET /usuarios` responde `200` con los usuarios sembrados.
- [ ] `GET /usuarios/{id_usuario}` con un id inexistente responde `404` con la forma uniforme.
- [ ] Toda respuesta de error (401 excluido, ya que no hay auth) del API, sin excepción, tiene la forma `{ "error": { "codigo", "mensaje" } }`.
- [ ] Arrancar sin variables de entorno definidas usa `HOST=0.0.0.0`, `PORT=8000`, `LOG_LEVEL=INFO` por defecto.
- [ ] Definir `PORT=9000` en el entorno hace que la app escuche en el puerto 9000.
- [ ] Cada request HTTP genera una línea de log JSON por stdout con `evento="request"`, `metodo`, `ruta`, `status` y `duracion_ms`.
- [ ] Cada `ApiError` (incluyendo errores de validación y 404) genera además una línea de log JSON con `evento="api_error"` y el `codigo` correspondiente.
- [ ] El repositorio no contiene ningún archivo `.env` con valores reales; existe `.env.example` versionado y `.env` está listado en `.gitignore`.
- [ ] `api_propia/README.md` documenta, para cada endpoint, el método, la ruta, el esquema de request/response y los códigos de estado posibles.
- [ ] `api_propia/README.md` explica en una sección separada qué problema resuelve el API y para quién (documentación funcional), distinta de la sección de contrato técnico.
- [ ] `pytest` corre en verde cubriendo los casos anteriores.

## Decisions

- **Sí:** FastAPI + Pydantic. Da validación declarativa gratis y es coherente con `materiales/servicio_mock`, que ya usa el mismo stack.
- **Sí:** datos en memoria (diccionarios), sin base de datos. El foco del ejercicio es contrato HTTP (validación, status codes, forma de error), no persistencia.
- **No:** SQLite o MySQL con `materiales/datos/esquema.sql`. Añadiría complejidad de infraestructura sin aportar al objetivo declarado; queda para un spec futuro si se necesita persistencia real.
- **Sí:** reutilizar el esquema `SolicitudEntrada` del mock (`asunto`, `descripcion`, `area`, `solicitante`, `canal`) y los datos semilla de `areas`/`usuarios` del `esquema.sql`. Mantiene consistencia de dominio sin acoplar código a `materiales/`.
- **No:** autenticación Bearer. Fuera del alcance declarado; se puede añadir en un spec posterior si se requiere.
- **Sí:** `id_solicitud` como UUID string. Evita colisiones y no revela conteo interno.
- **Sí:** forma de error `{ error: { codigo, mensaje, detalles? } }` en vez de RFC 7807. Más simple de consumir y suficiente para el objetivo del ejercicio.
- **No:** `PUT`/`PATCH`/`DELETE` sobre solicitudes, ni transición de estados vía API. El pedido original solo pide crear, consultar y listar; cualquier mutación de estado queda fuera hasta que se defina el flujo (quién puede cambiar el estado y cómo).
- **No:** consumir `materiales/servicio_mock` desde este API. Ese mock simula un proveedor externo para otras etapas de la prueba; mezclarlo aquí introduciría fallas intencionales (latencia, 500, 429) ajenas al objetivo de este spec.
- **Sí:** configuración por variables de entorno (`HOST`, `PORT`, `LOG_LEVEL`) con defaults sensatos, en vez de un archivo de config commiteado con valores fijos. Permite correr el mismo código en distintos entornos sin tocar fuente.
- **No:** variables de entorno para los límites de paginación. Son parámetros de negocio del contrato del API, no de infraestructura; cambiarlos debería ser una decisión de código/spec, no de despliegue.
- **Sí:** logging con la librería estándar de Python (`logging` + formatter JSON propio) en vez de `structlog`. Evita una dependencia nueva para un requisito acotado (un log por request y por error).
- **Sí:** `.env.example` versionado + `.env` real en `.gitignore`. Dejar la convención lista aunque hoy no haya secretos reales, para que agregar auth en un spec futuro no requiera decidir esto de nuevo.
- **Sí:** README con dos secciones explícitamente separadas (funcional y técnica) en vez de una mezcla. Facilita que alguien no técnico entienda el propósito sin leer el contrato HTTP, y que un integrador encuentre el contrato sin leer la motivación de negocio.

## What is **not** in this spec

- Autenticación y autorización.
- Persistencia real (SQLite/MySQL).
- Actualización o borrado de solicitudes, y cambios de estado vía API.
- Integración con `materiales/servicio_mock` o con el `webhook/mensajeria`.
- Rate limiting, idempotencia o reintentos.
- Envío de logs a un colector externo (por ahora solo stdout).
- Variables de entorno para límites de paginación.

Cada uno de esos, si se necesita, va en su propio spec.

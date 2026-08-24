# API REST de solicitudes — Mesa de Ayuda

## Documentación funcional

### Qué problema resuelve

Este API permite registrar y consultar las solicitudes ("tickets") que los
colaboradores le hacen a la mesa de ayuda: incidentes, accesos, hardware,
software, etc. Cubre el flujo mínimo de captura y seguimiento de una
solicitud — no gestiona su ciclo de vida completo (ver "Qué NO cubre").

### Para quién es

- **Colaboradores que reportan solicitudes**: crean una solicitud (`POST
  /solicitudes`) y pueden consultarla por id para ver su estado.
- **Equipo de mesa de ayuda**: lista y filtra las solicitudes por área o
  estado para priorizar su atención (`GET /solicitudes`), y consulta el
  catálogo de áreas y usuarios de la organización (`GET /areas`, `GET
  /usuarios`) para saber a quién y a dónde corresponde cada solicitud.

### Qué NO cubre

- Autenticación ni autorización: cualquiera que tenga acceso a la API puede
  usar cualquier endpoint.
- Actualizar el estado de una solicitud, o modificarla/borrarla una vez
  creada.
- Persistencia real: los datos viven en memoria y se pierden al reiniciar
  el proceso.
- Notificaciones, escalamientos o integraciones con proveedores externos.

## Documentación técnica

### Cómo correr el proyecto

```bash
python3 -m venv .venv
.venv/bin/pip install -r api_propia/requirements.txt

# opcional, para sobreescribir HOST/PORT/LOG_LEVEL localmente:
cp api_propia/.env.example api_propia/.env

.venv/bin/uvicorn api_propia.main:app --reload
```

`main.py` usa imports absolutos (`api_propia.algo`), por lo que **no se puede
ejecutar como script directo** (`python api_propia/main.py` falla con
`ModuleNotFoundError`). Las dos formas soportadas de arrancar son:

```bash
.venv/bin/uvicorn api_propia.main:app --reload
# o
.venv/bin/python -m api_propia.main
```

### Documentación interactiva (Swagger UI)

Con la aplicación corriendo, FastAPI expone documentación interactiva
generada automáticamente en:

```
http://127.0.0.1:8000/docs
```

Ahí se pueden ver todos los endpoints, sus esquemas de request/response, y
probarlos directamente desde el navegador con "Try it out" (sin necesidad
de `curl` ni Postman). También existe la variante en formato ReDoc en
`http://127.0.0.1:8000/redoc`, y el esquema OpenAPI crudo en
`http://127.0.0.1:8000/openapi.json`.

Si se cambia `PORT` (ver siguiente sección), reemplazar `8000` por el
puerto configurado.

### Configuración (variables de entorno)

| Variable    | Default     | Descripción                                  |
| ----------- | ----------- | --------------------------------------------- |
| `HOST`      | `0.0.0.0`   | Host donde escucha uvicorn.                   |
| `PORT`      | `8000`      | Puerto donde escucha uvicorn.                 |
| `LOG_LEVEL` | `INFO`      | Nivel del logger `api_propia` (JSON a stdout). |

No hay secretos en este spec (no hay autenticación). `.env.example` está
versionado como referencia; un `.env` real (si se usa) está ignorado por
`api_propia/.gitignore`.

### Logging

Cada request HTTP genera una línea JSON por stdout con evento `request`:

```json
{"timestamp": "2026-08-24T10:00:00Z", "level": "INFO", "evento": "request", "metodo": "POST", "ruta": "/solicitudes", "status": 201, "duracion_ms": 4.2}
```

Cada `ApiError` (incluye validación y 404) genera además una línea con
evento `api_error`:

```json
{"timestamp": "2026-08-24T10:00:01Z", "level": "WARNING", "evento": "api_error", "codigo": "VALIDATION_ERROR", "ruta": "/solicitudes", "status": 422}
```

### Forma uniforme de error

Toda respuesta 4xx/5xx tiene esta forma:

```json
{
  "error": {
    "codigo": "VALIDATION_ERROR",
    "mensaje": "descripción legible del error",
    "detalles": [{ "campo": "asunto", "mensaje": "..." }]
  }
}
```

`detalles` solo aparece en errores de validación (`VALIDATION_ERROR`).

### Contrato del API

#### `GET /health`

Chequeo de salud. Responde `200` con `{"status": "ok"}`.

#### `POST /solicitudes`

Crea una solicitud.

Request body (`SolicitudEntrada`):

| Campo         | Tipo             | Restricciones                     |
| ------------- | ---------------- | ---------------------------------- |
| `asunto`      | `string`         | requerido, 5–200 caracteres        |
| `descripcion` | `string \| null` | opcional, máx. 4000 caracteres     |
| `area`        | `string`         | requerido, 2–80 caracteres         |
| `solicitante` | `string`         | requerido, 5–120 caracteres        |
| `canal`       | `string`         | opcional, default `"api"`          |

Response `201` (`Solicitud`): igual al body de entrada más `id_solicitud`
(uuid string), `estado` (siempre `"recibida"` al crear) y `fecha_creacion`
(ISO 8601, UTC).

Errores: `422 VALIDATION_ERROR` si algún campo no cumple sus restricciones
o falta un campo requerido.

#### `GET /solicitudes/{id_solicitud}`

Consulta una solicitud por id.

- `200`: la solicitud completa (`Solicitud`).
- `404 NOT_FOUND`: no existe una solicitud con ese id.

#### `GET /solicitudes`

Lista solicitudes con filtros y paginación.

Query params:

| Parámetro | Tipo      | Default | Restricciones      |
| --------- | --------- | ------- | -------------------- |
| `area`    | `string`  | —       | opcional, coincidencia exacta |
| `estado`  | `string`  | —       | opcional, coincidencia exacta (`recibida`, `en_proceso`, `resuelta`, `cerrada`) |
| `limite`  | `integer` | `50`    | `1 <= limite <= 200` |
| `offset`  | `integer` | `0`     | `offset >= 0`        |

Response `200`: lista de `Solicitud`. `422 VALIDATION_ERROR` si `limite`
u `offset` violan sus restricciones.

#### `GET /areas`

Lista todas las áreas sembradas. Response `200`: lista de `Area`.

#### `GET /areas/{id_area}`

- `200`: el área (`Area`).
- `404 NOT_FOUND`: no existe un área con ese id.

#### `GET /usuarios`

Lista todos los usuarios sembrados. Response `200`: lista de `Usuario`.

#### `GET /usuarios/{id_usuario}`

- `200`: el usuario (`Usuario`).
- `404 NOT_FOUND`: no existe un usuario con ese id.

### Esquemas de respuesta

```python
class Solicitud(BaseModel):
    asunto: str
    descripcion: str | None
    area: str
    solicitante: str
    canal: str
    id_solicitud: str        # uuid4
    estado: str               # "recibida" | "en_proceso" | "resuelta" | "cerrada"
    fecha_creacion: datetime  # UTC

class Area(BaseModel):
    id_area: int
    nombre: str
    sede: str
    responsable: str | None

class Usuario(BaseModel):
    id_usuario: int
    correo: str
    nombre: str
    id_area: int
    activo: bool
```

### Datos en memoria

`areas` y `usuarios` se siembran al arrancar la aplicación con los mismos
valores de `materiales/datos/esquema.sql` (8 áreas, 40 usuarios),
copiados como constantes — no se lee el `.sql` en tiempo de ejecución.
`solicitudes` empieza vacío y se llena con lo que se cree vía `POST`. Todo
se reinicia al reiniciar el proceso.

### Cómo correr las pruebas

```bash
.venv/bin/pytest api_propia/tests -v
```

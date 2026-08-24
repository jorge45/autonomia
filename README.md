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

---

# Clasificador de solicitudes con IA (`clasificador_ia/`)

## Documentación funcional

### Qué problema resuelve

Módulo Python desacoplado que recibe el texto libre de una solicitud
(`asunto` + `descripcion`) y usa la API de Claude para asignar una
**categoría** y una **prioridad** dentro de la taxonomía de Mesa de Ayuda.
Es un componente reutilizable, independiente de `api_propia/`: no importa
sus modelos ni sus rutas, y **no está integrado** con `POST /solicitudes`
todavía (queda para un spec futuro — ver `specs/02-clasificador-ia-solicitudes.md`).

### Para quién es

Para cualquier flujo (futuro) que necesite clasificar texto libre de una
solicitud sin tener que implementar su propia lógica de llamada a la IA,
reintentos o modo degradado.

### Qué NO cubre

- Integración con `POST /solicitudes` u otro endpoint de `api_propia/`.
- Endpoint HTTP propio para disparar la clasificación bajo demanda.
- Clasificación heurística (por palabras clave) como paso intermedio antes
  de degradar.
- Taxonomía configurable en tiempo de ejecución (está fija en código).
- Circuit breaker, rate limiting o métricas sobre el uso de la IA.

## Documentación técnica

### Cómo funciona

`clasificar_solicitud(asunto, descripcion)` (en `clasificador_ia/clasificador.py`):

1. Construye el cliente de Anthropic (`clasificador_ia/cliente.py`); si
   `ANTHROPIC_API_KEY` no está definida en el entorno, lanza
   `ConfiguracionInvalida` de inmediato (falla explícita, no modo
   degradado — es un error de despliegue, no una falla transitoria).
2. Arma un prompt con `asunto` y `descripcion`, y llama al modelo
   `claude-opus-4-8` con `output_config.format` (`json_schema`, con
   `categoria` y `prioridad` como `enum` de la taxonomía y
   `additionalProperties: false`). Esto garantiza por construcción que la
   IA nunca puede devolver un valor fuera de la taxonomía — no hace falta
   validar la respuesta después.
3. Si la llamada falla (timeout de 10s o error del proveedor), reintenta
   hasta 2 veces más (3 intentos totales) con backoff exponencial (~1s,
   luego ~2s), logueando cada intento fallido.
4. Si los 3 intentos fallan, devuelve un resultado en **modo degradado**
   con valores fijos (`categoria="otro"`, `prioridad="media"`,
   `origen="degradado"`) sin lanzar excepción al llamador.
5. Si algún intento tiene éxito, devuelve `ResultadoClasificacion` con
   `origen="ia"` y la clasificación real.

### Instalación

```bash
.venv/bin/pip install -r clasificador_ia/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

### Uso

```python
from clasificador_ia.clasificador import clasificar_solicitud

resultado = clasificar_solicitud(
    "Impresora no enciende",
    "La impresora del piso 3 no responde",
)
# ResultadoClasificacion(categoria="incidente", prioridad="alta", origen="ia")
```

### Paso a paso para probar lo implementado

**1. Instalar dependencias** (si aún no lo hiciste — usa el mismo `.venv`
del repo):

```bash
.venv/bin/pip install -r clasificador_ia/requirements.txt
```

**2. Correr la suite de pruebas (no necesita `ANTHROPIC_API_KEY` ni red)**
— es la forma más rápida de verificar que toda la lógica (éxito,
reintentos, degradado, error de configuración) funciona:

```bash
.venv/bin/pytest clasificador_ia/tests -v
```

Salida esperada:

```
collected 4 items

clasificador_ia/tests/test_clasificador.py::test_clasificacion_exitosa_primer_intento PASSED [ 25%]
clasificador_ia/tests/test_clasificador.py::test_exito_tras_reintento PASSED [ 50%]
clasificador_ia/tests/test_clasificador.py::test_agotamiento_reintentos_devuelve_degradado PASSED [ 75%]
clasificador_ia/tests/test_clasificador.py::test_sin_api_key_lanza_configuracion_invalida PASSED [100%]

============================== 4 passed in 0.43s ===============================
```

**3. Probar el error de configuración** (sin API key definida, debe
fallar explícito, no degradar):

```bash
unset ANTHROPIC_API_KEY
.venv/bin/python -c "
from clasificador_ia.clasificador import clasificar_solicitud
clasificar_solicitud('Impresora no enciende', 'No responde')
"
```

Salida esperada: excepción `clasificador_ia.config.ConfiguracionInvalida:
Falta la variable de entorno ANTHROPIC_API_KEY.`

**4. Probar con una llamada real a la IA** (requiere una API key válida
de Anthropic — consume créditos):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
.venv/bin/python -c "
from clasificador_ia.clasificador import clasificar_solicitud

resultado = clasificar_solicitud(
    'Impresora no enciende',
    'La impresora del piso 3 no responde desde esta mañana',
)
print(resultado)
"
```

Salida esperada (la clasificación exacta puede variar, pero siempre
dentro de la taxonomía):

```
ResultadoClasificacion(categoria='incidente', prioridad='alta', origen='ia')
```

Y por stdout, el log estructurado del evento:

```json
{"timestamp": "2026-08-24T10:00:00Z", "level": "INFO", "evento": "clasificacion_ia", "origen": "ia", "categoria": "incidente", "prioridad": "alta", "intentos": 1, "duracion_ms": 850.3}
```

**5. (Opcional) Simular el modo degradado** sin esperar a que la API
falle de verdad — usando una API key inválida para forzar errores del
proveedor en los 3 intentos:

```bash
export ANTHROPIC_API_KEY=clave-invalida
.venv/bin/python -c "
from clasificador_ia.clasificador import clasificar_solicitud
print(clasificar_solicitud('Prueba', None))
"
```

Salida esperada tras ~3s de reintentos (backoff ~1s + ~2s):

```
ResultadoClasificacion(categoria='otro', prioridad='media', origen='degradado')
```

Con dos logs `clasificacion_ia_reintento` y uno `clasificacion_ia_degradado`
por stdout.

### Modelo de datos

```python
CATEGORIAS_VALIDAS = ["incidente", "acceso", "hardware", "software", "otro"]
PRIORIDADES_VALIDAS = ["baja", "media", "alta", "urgente"]

@dataclass(frozen=True)
class ResultadoClasificacion:
    categoria: str    # uno de CATEGORIAS_VALIDAS
    prioridad: str    # uno de PRIORIDADES_VALIDAS
    origen: str        # "ia" | "degradado"
```

### Configuración

Fija en código (`clasificador_ia/config.py`), no en variables de entorno
— son decisiones de comportamiento del módulo, no de despliegue:

| Constante              | Valor            | Descripción                          |
| ----------------------- | ---------------- | ------------------------------------- |
| `MODELO`                | `claude-opus-4-8`| Modelo de Anthropic usado.            |
| `TIMEOUT_SEGUNDOS`      | `10.0`           | Timeout por llamada a la API.         |
| `MAX_REINTENTOS`        | `2`              | Reintentos adicionales (3 intentos totales). |
| `BACKOFF_BASE_SEGUNDOS` | `1.0`            | Base del backoff exponencial (~1s, ~2s). |

La única variable de entorno es `ANTHROPIC_API_KEY` (requerida, sin
default; su ausencia lanza `ConfiguracionInvalida`).

### Logging

JSON por stdout, misma convención que `api_propia` (logger `clasificador_ia`):

```json
{"timestamp": "2026-08-24T10:00:00Z", "level": "INFO", "evento": "clasificacion_ia", "origen": "ia", "categoria": "incidente", "prioridad": "alta", "intentos": 1, "duracion_ms": 850.3}
{"timestamp": "2026-08-24T10:00:05Z", "level": "WARNING", "evento": "clasificacion_ia_reintento", "intento": 1, "motivo": "timeout"}
{"timestamp": "2026-08-24T10:00:20Z", "level": "WARNING", "evento": "clasificacion_ia_degradado", "intentos": 3, "categoria": "otro", "prioridad": "media"}
```

### Cómo correr las pruebas

```bash
.venv/bin/pytest clasificador_ia/tests -v
```

Las pruebas mockean el cliente de Anthropic: corren sin red y sin
necesidad de `ANTHROPIC_API_KEY`. Cubren clasificación exitosa, éxito tras
un reintento, agotamiento de reintentos → degradado, y falta de API key →
`ConfiguracionInvalida`.

---

# Corrección de defectos en `legacy_module.py`

> Ver `specs/03-correccion-legacy-module.md` para el spec completo. El
> código de `materiales/` no se versiona en este repo (está en
> `.gitignore`); este reporte deja constancia de la corrección aplicada.

## Reporte de causa raíz

El módulo heredado de la Mesa de Ayuda (`materiales/legacy/legacy_module.py`)
presentaba tres defectos de lógica, cada uno asociado a un síntoma
reportado por el área pero nunca diagnosticado:

| Síntoma | Función | Causa raíz | Fix |
| ------- | ------- | ---------- | --- |
| **S1** — el informe mensual pierde tickets | `filtrar_por_periodo` | Comparación estricta (`fc > inicio and fc < fin`) excluía los tickets creados exactamente en los extremos del periodo, pese a que el periodo debe incluirlos. | `fc >= inicio and fc <= fin` |
| **S2** — cifras infladas en resúmenes sucesivos | `resumir_por_area` | `acumulador={}` es un diccionario mutable evaluado una sola vez al definir la función, por lo que persiste y se acumula entre llamadas sucesivas dentro del mismo proceso. | `acumulador=None` con inicialización `{}` dentro del cuerpo |
| **S3** — reaperturas subcontadas | `contar_reaperturas` | Comparaba el `estado` actual contra `"reabierto"` de forma exacta, ignorando variantes de mayúsculas y tickets reabiertos-y-cerrados de nuevo (cuyo `estado` ya no es `"reabierto"` aunque `reaperturas > 0`). | Contar `int(t.get("reaperturas") or 0) > 0`, usando el campo autoritativo en vez del `estado` |

Cada fix quedó acompañado de un comentario de una línea en el código con
esta misma causa raíz, y ninguna función ajena a S1/S2/S3 cambió de
comportamiento.

## Pruebas

`materiales/legacy/tests/test_legacy_module.py` agrega una prueba pytest
por síntoma, con datos sintéticos definidos en el propio archivo (no
depende del CSV de 2000 filas):

- `test_filtrar_por_periodo_incluye_extremos`
- `test_resumir_por_area_no_acumula_entre_llamadas`
- `test_contar_reaperturas_usa_campo_reaperturas`

Las tres se verificaron en rojo→verde: cada una falla si se revierte
únicamente su fix correspondiente, y las tres pasan contra el código
corregido.

```bash
.venv/bin/pytest materiales/legacy/tests/ -v
```

Salida esperada:

```
materiales/legacy/tests/test_legacy_module.py::test_filtrar_por_periodo_incluye_extremos PASSED
materiales/legacy/tests/test_legacy_module.py::test_resumir_por_area_no_acumula_entre_llamadas PASSED
materiales/legacy/tests/test_legacy_module.py::test_contar_reaperturas_usa_campo_reaperturas PASSED

============================== 3 passed in 0.01s ===============================
```

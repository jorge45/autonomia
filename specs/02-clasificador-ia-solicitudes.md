# SPEC 02 — Clasificador de solicitudes con IA

> **Status:** Approved
> **Depends on:** ninguna
> **Date:** 2026-08-24
> **Objective:** Construir un módulo Python desacoplado (`clasificador_ia/`) que reciba texto libre y use la API de Claude para asignar categoría y prioridad, con timeout, reintentos con backoff y un modo degradado con valores por defecto cuando el proveedor no responde.

## Por qué existe este spec

Este módulo es un componente reutilizable de clasificación automática. Se construye desacoplado de `api_propia/` (SPEC 01): no importa sus modelos ni sus rutas, y no se integra ahí todavía — solo expone una función que recibe texto libre (`asunto`, `descripcion`) y devuelve una categoría y prioridad. La integración con `POST /solicitudes` queda para un spec futuro.

## Scope

**In:**

- Paquete `clasificador_ia/` en la raíz del repo, independiente de `api_propia/`.
- Función pública que recibe `asunto: str` y `descripcion: str | None`, y devuelve un resultado con `categoria`, `prioridad` y `origen` (`"ia"` o `"degradado"`).
- Uso de la API de Claude (Anthropic SDK oficial, modelo `claude-opus-4-8`) con `output_config.format` (`json_schema` con `enum`) para garantizar que la IA solo puede devolver valores dentro de la taxonomía válida.
- Timeout de 10 segundos por llamada a la API.
- Reintentos: hasta 2 reintentos (3 intentos totales) con backoff exponencial (~1s, luego ~2s) ante timeout o error del proveedor.
- Modo degradado: si se agotan los reintentos (o falta la configuración de API key), se devuelve un resultado con valores por defecto fijos y `origen="degradado"`, sin lanzar excepción al llamador.
- Validación de configuración: si `ANTHROPIC_API_KEY` no está definida, se lanza un error de configuración explícito al intentar usar el módulo (no un fallo genérico, y no modo degradado — ver Decisions).
- Registro estructurado de eventos (JSON por stdout, misma convención que `api_propia`): un evento por clasificación exitosa, uno por cada intento fallido/reintento, y uno cuando se activa el modo degradado.
- Suite de pruebas con pytest que mockea el cliente de Anthropic (sin llamadas reales ni necesidad de API key), cubriendo éxito, timeout con reintento exitoso, agotamiento de reintentos → degradado, y falta de API key → error de configuración.
- `requirements.txt` propio del módulo (`anthropic`, `pytest`).

**Out of scope (for future specs):**

- Integración con `POST /solicitudes` de `api_propia/` (invocar el clasificador al crear una solicitud).
- Endpoint HTTP dedicado para clasificar bajo demanda.
- Clasificación heurística/basada en palabras clave como fallback intermedio antes del modo degradado.
- Taxonomía configurable o editable en tiempo de ejecución (categorías y prioridades quedan fijas en código).
- Circuit breaker o límites de tasa hacia la API de Claude.
- Métricas o alertas sobre la tasa de modo degradado.
- Streaming de la respuesta de la IA (la clasificación es una respuesta corta, no necesita streaming).

## Data model

```python
# clasificador_ia/modelos.py

CATEGORIAS_VALIDAS = ["incidente", "acceso", "hardware", "software", "otro"]
PRIORIDADES_VALIDAS = ["baja", "media", "alta", "urgente"]

@dataclass(frozen=True)
class ResultadoClasificacion:
    categoria: str    # uno de CATEGORIAS_VALIDAS
    prioridad: str    # uno de PRIORIDADES_VALIDAS
    origen: str        # "ia" | "degradado"
```

Valores del modo degradado (fijos en código, ver Decisions):

```python
CATEGORIA_DEGRADADA = "otro"
PRIORIDAD_DEGRADADA = "media"
```

Configuración (`clasificador_ia/config.py`):

```python
class ConfiguracionInvalida(Exception):
    """La configuración requerida (p. ej. ANTHROPIC_API_KEY) no está presente."""

MODELO = "claude-opus-4-8"
TIMEOUT_SEGUNDOS = 10.0
MAX_REINTENTOS = 2          # 3 intentos totales
BACKOFF_BASE_SEGUNDOS = 1.0  # 1s, luego 2s
```

`ANTHROPIC_API_KEY` se lee del entorno; no hay un `Settings` adicional para esto — se valida su presencia al construir el cliente (ver Decisions).

Línea de log estructurado (JSON por stdout, mismo formato que `api_propia`):

```json
{"timestamp": "2026-08-24T10:00:00Z", "level": "INFO", "evento": "clasificacion_ia", "origen": "ia", "categoria": "incidente", "prioridad": "alta", "intentos": 1, "duracion_ms": 850.3}
{"timestamp": "2026-08-24T10:00:05Z", "level": "WARNING", "evento": "clasificacion_ia_reintento", "intento": 1, "motivo": "timeout"}
{"timestamp": "2026-08-24T10:00:20Z", "level": "WARNING", "evento": "clasificacion_ia_degradado", "intentos": 3, "categoria": "otro", "prioridad": "media"}
```

## Implementation plan

1. Crear `clasificador_ia/` con `requirements.txt` (`anthropic`, `pytest`), `__init__.py`, y `clasificador_ia/modelos.py` con `ResultadoClasificacion`, `CATEGORIAS_VALIDAS`, `PRIORIDADES_VALIDAS` y los valores degradados. Prueba manual: `python -c "from clasificador_ia.modelos import CATEGORIAS_VALIDAS; print(CATEGORIAS_VALIDAS)"`.
2. Crear `clasificador_ia/config.py` con las constantes (`MODELO`, `TIMEOUT_SEGUNDOS`, `MAX_REINTENTOS`, `BACKOFF_BASE_SEGUNDOS`) y `ConfiguracionInvalida`. Crear `clasificador_ia/logging_config.py` reutilizando el mismo enfoque de formatter JSON de `api_propia/logging_config.py` (logger `clasificador_ia`, JSON a stdout).
3. Crear `clasificador_ia/cliente.py` con una función que construye el cliente de Anthropic (`anthropic.Anthropic()` con `timeout=TIMEOUT_SEGUNDOS`), lanzando `ConfiguracionInvalida` si `ANTHROPIC_API_KEY` no está definida en el entorno. Prueba manual: sin la variable definida, llamar a la función lanza `ConfiguracionInvalida` con un mensaje claro.
4. Crear `clasificador_ia/clasificador.py` con la función pública `clasificar_solicitud(asunto: str, descripcion: str | None) -> ResultadoClasificacion`: arma el prompt con `asunto` + `descripcion`, llama al cliente con `output_config.format` (`json_schema`, `additionalProperties: false`, `categoria` y `prioridad` como `enum` de `CATEGORIAS_VALIDAS`/`PRIORIDADES_VALIDAS`), parsea la respuesta y devuelve `ResultadoClasificacion(origen="ia")`. Prueba manual (con `ANTHROPIC_API_KEY` real): clasificar un texto de ejemplo y verificar que `categoria`/`prioridad` están dentro de la taxonomía.
5. Agregar a `clasificador_ia/clasificador.py` el bucle de reintentos con backoff exponencial (hasta `MAX_REINTENTOS` reintentos, espera `BACKOFF_BASE_SEGUNDOS * 2**intento` entre intentos) capturando timeouts y errores de la API; cada intento fallido emite el evento `clasificacion_ia_reintento`. Si se agotan los intentos, devuelve `ResultadoClasificacion(categoria=CATEGORIA_DEGRADADA, prioridad=PRIORIDAD_DEGRADADA, origen="degradado")` y emite el evento `clasificacion_ia_degradado`, sin lanzar excepción. Toda llamada exitosa emite el evento `clasificacion_ia` con `intentos` y `duracion_ms`.
6. Crear `clasificador_ia/tests/test_clasificador.py` con pytest, mockeando el cliente de Anthropic (sin red ni API key real): casos de clasificación exitosa al primer intento, éxito tras un reintento (timeout simulado en el primer intento), agotamiento de los 3 intentos → resultado degradado, y `ConfiguracionInvalida` cuando `ANTHROPIC_API_KEY` no está definida. Verificar también que el resultado siempre tiene `categoria` en `CATEGORIAS_VALIDAS` y `prioridad` en `PRIORIDADES_VALIDAS`.

## Acceptance criteria

- [ ] `clasificar_solicitud("Impresora no enciende", "La impresora del piso 3 no responde")` con la API respondiendo correctamente devuelve un `ResultadoClasificacion` con `origen="ia"`, `categoria` en `CATEGORIAS_VALIDAS` y `prioridad` en `PRIORIDADES_VALIDAS`.
- [ ] Si la API tarda más de 10 segundos o falla, el módulo reintenta hasta 2 veces adicionales con backoff exponencial antes de degradar.
- [ ] Si los 3 intentos fallan, `clasificar_solicitud` devuelve `ResultadoClasificacion(categoria="otro", prioridad="media", origen="degradado")` sin lanzar excepción.
- [ ] Si un reintento tiene éxito (p. ej. el segundo intento responde bien), el resultado final tiene `origen="ia"` y refleja la respuesta real de la IA, no el valor degradado.
- [ ] Sin `ANTHROPIC_API_KEY` definida en el entorno, invocar el módulo lanza `ConfiguracionInvalida` con un mensaje que indica la variable faltante — no se activa el modo degradado en este caso.
- [ ] La API de Claude nunca puede devolver una `categoria` o `prioridad` fuera de la taxonomía definida (se garantiza vía `output_config.format` con `enum`, no por validación posterior).
- [ ] Cada llamada exitosa genera un log JSON con `evento="clasificacion_ia"`, `origen`, `categoria`, `prioridad`, `intentos` y `duracion_ms`.
- [ ] Cada intento fallido genera un log JSON con `evento="clasificacion_ia_reintento"`.
- [ ] Activar el modo degradado genera un log JSON con `evento="clasificacion_ia_degradado"`.
- [ ] `pytest` corre en verde sin necesidad de `ANTHROPIC_API_KEY` ni acceso a red (cliente de Anthropic mockeado).

## Decisions

- **Sí:** módulo desacoplado en `clasificador_ia/`, raíz del repo, sin importar nada de `api_propia/`. Permite reutilizarlo en cualquier flujo futuro sin acoplarlo al dominio de "solicitudes".
- **No:** integrarlo ahora con `POST /solicitudes`. La integración es una decisión de flujo (¿bloquea la creación si tarda? ¿es síncrona o asíncrona?) que merece su propio spec.
- **Sí:** SDK oficial de Anthropic (`anthropic`), modelo `claude-opus-4-8` — el default recomendado salvo que se pida explícitamente otro modelo.
- **Sí:** `output_config.format` con `json_schema` y `enum` para `categoria`/`prioridad`, en vez de pedirle a la IA texto libre y validar/corregir después. Elimina por construcción la posibilidad de una respuesta fuera de taxonomía.
- **Sí:** taxonomía fija en código (`CATEGORIAS_VALIDAS`, `PRIORIDADES_VALIDAS`), reutilizando el dominio de Mesa de Ayuda. Configurarla en tiempo de ejecución es complejidad innecesaria para este spec.
- **Sí:** 10 segundos de timeout por llamada, fijo en código (no variable de entorno). Es un valor de comportamiento del módulo, no de despliegue; cambiarlo debería ser una decisión de código.
- **Sí:** 2 reintentos con backoff exponencial (~1s, ~2s) implementados en el propio módulo (no solo el retry automático del SDK), para poder loguear cada intento fallido y controlar exactamente cuándo se activa el modo degradado.
- **Sí:** modo degradado con valores por defecto fijos (`categoria="otro"`, `prioridad="media"`) en vez de clasificación heurística por palabras clave. Es la opción más simple y predecible; una heurística intermedia es una mejora que puede añadirse después sin cambiar la interfaz pública.
- **No:** que la falta de `ANTHROPIC_API_KEY` active el modo degradado. Es un error de configuración del despliegue, no una falla transitoria del proveedor — debe fallar de forma explícita y ruidosa (`ConfiguracionInvalida`), no silenciosamente con un valor por defecto.
- **Sí:** logging estructurado JSON por stdout, reutilizando la convención de `api_propia` (mismo formato de línea), para mantener consistencia si en el futuro se agregan a un mismo colector de logs.
- **Sí:** pruebas con el cliente de Anthropic mockeado. Corren en CI sin costo, sin red y sin depender de una API key real; suficiente para cubrir los casos de éxito, reintento, degradado y error de configuración.
- **No:** streaming de la respuesta. La clasificación es una salida corta y estructurada (JSON pequeño), no hay beneficio de mostrar progreso incremental.

## What is **not** in this spec

- Integración de este módulo con `POST /solicitudes` u otro endpoint de `api_propia/`.
- Un endpoint HTTP propio para disparar la clasificación.
- Clasificación heurística como paso intermedio antes de degradar.
- Taxonomía configurable en tiempo de ejecución.
- Circuit breaker, rate limiting o métricas sobre el uso de la IA.

Cada uno de esos, si se necesita, va en su propio spec.

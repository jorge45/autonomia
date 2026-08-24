class ConfiguracionInvalida(Exception):
    """La configuración requerida (p. ej. ANTHROPIC_API_KEY) no está presente."""


MODELO = "claude-opus-4-8"
TIMEOUT_SEGUNDOS = 10.0
MAX_REINTENTOS = 2  # 3 intentos totales
BACKOFF_BASE_SEGUNDOS = 1.0  # 1s, luego 2s

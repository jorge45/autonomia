# SPEC 03 — Corrección de defectos de lógica en legacy_module.py

> **Status:** Approved
> **Depends on:** ninguna
> **Date:** 2026-08-24
> **Objective:** Corregir los tres defectos de lógica de `materiales/legacy/legacy_module.py` que causan los síntomas S1 (tickets perdidos en el informe), S2 (cifras infladas en resúmenes sucesivos) y S3 (reaperturas subcontadas), con una prueba pytest por defecto que falla antes del fix y pasa después.

## Por qué existe este spec

`legacy_module.py` está en producción desde 2023 generando el informe mensual de tickets de la mesa de ayuda. El área reporta tres síntomas nunca diagnosticados (ver docstring del módulo). El objetivo es encontrar la causa raíz de cada uno, aplicar el fix mínimo (sin reescribir el módulo) y dejar evidencia reproducible: una prueba roja→verde y una línea de causa raíz por corrección.

## Scope

**In:**

- Corregir exactamente 3 defectos en `materiales/legacy/legacy_module.py`, uno por cada síntoma (S1, S2, S3), sin reescribir funciones que no están involucradas en los síntomas.
- **S1** — `filtrar_por_periodo` usa comparación estricta (`fc > inicio and fc < fin`) cuando el docstring de la propia función indica que el periodo incluye ambos extremos. Fix: usar `>=` y `<=`.
- **S2** — `resumir_por_area(tickets, acumulador={})` usa un diccionario mutable como valor por defecto, que persiste entre llamadas dentro del mismo proceso. Fix: `acumulador=None` con inicialización `{}` dentro de la función.
- **S3** — `contar_reaperturas` compara `t.get("estado") == "reabierto"` de forma exacta y sensible a mayúsculas, e ignora el campo `reaperturas` (contador autoritativo). Esto subcuenta por dos motivos: variantes de mayúsculas en `estado` (`"REABIERTO"`, `"Reabierto"`) y tickets que fueron reabiertos y luego cerrados de nuevo, cuyo `estado` actual ya no es `"reabierto"` aunque `reaperturas > 0`. Fix: contar tickets con `int(t.get("reaperturas") or 0) > 0`, en vez de comparar `estado`.
- Un comentario de una línea junto a cada fix en `legacy_module.py` explicando la causa raíz.
- Suite `materiales/legacy/tests/test_legacy_module.py` con pytest y datos sintéticos mínimos (definidos en el propio archivo, no depende del CSV de 2000 filas), con al menos una prueba por defecto que:
  - Falla contra el código actual (sin los fixes).
  - Pasa una vez aplicado el fix correspondiente.
- Tabla-resumen de las 3 causas raíz en este spec (sección "Implementation plan").

**Out of scope (para otro spec si se necesita):**

- Cualquier otro defecto de `legacy_module.py` no asociado a S1/S2/S3 (p. ej. robustez de `parsear_fecha` ante formatos no contemplados, o comportamiento del bloque `if __name__ == "__main__"`).
- Reescribir el módulo con una arquitectura distinta (paso a clases, tipado, dataclasses, etc.).
- Migrar el módulo a `api_propia/` o integrarlo con el clasificador IA.
- Manejo de la columna `reaperturas` como fuente de verdad en otros reportes fuera de `contar_reaperturas`/`tasa_reapertura`.
- Agregar un `pytest.ini`/`pyproject.toml` de configuración global — se usa el discovery por defecto de pytest desde la raíz del repo, igual que `api_propia/tests` y `clasificador_ia/tests`.

## Data model

Este spec no introduce estructuras de datos nuevas. Los tickets siguen siendo `dict` con las mismas claves usadas hoy por el módulo (`fecha_creacion`, `fecha_cierre`, `area`, `estado`, `reaperturas`, etc., ver `materiales/datos/tickets_historicos.csv`). Las pruebas nuevas construyen listas de `dict` sintéticos con solo las claves relevantes para cada caso.

## Implementation plan

1. **Fix S1** en `filtrar_por_periodo`: cambiar `if fc > inicio and fc < fin` por `if fc >= inicio and fc <= fin`, agregando comentario de una línea con la causa raíz. Prueba manual: `filtrar_por_periodo(tickets, date(2025,3,1), date(2025,3,31))` incluye un ticket con `fecha_creacion="2025-03-01"` y uno con `"2025-03-31"`.
2. **Fix S2** en `resumir_por_area`: cambiar la firma a `def resumir_por_area(tickets, acumulador=None):` e inicializar `acumulador = {} if acumulador is None else acumulador` al inicio del cuerpo, agregando comentario de una línea con la causa raíz. Prueba manual: dos llamadas sucesivas a `resumir_por_area(tickets)` sin pasar `acumulador` devuelven el mismo resultado cada vez (no se acumula entre llamadas).
3. **Fix S3** en `contar_reaperturas`: cambiar el cuerpo para contar tickets donde `int(t.get("reaperturas") or 0) > 0`, en vez de comparar `t.get("estado") == "reabierto"`, agregando comentario de una línea con la causa raíz. Prueba manual: un ticket con `estado="cerrado"` y `reaperturas="1"` cuenta como reapertura; un ticket con `estado="REABIERTO"` y `reaperturas="0"` no cuenta (evita perpetuar el problema de mayúsculas ahora con el campo equivocado).
4. Crear `materiales/legacy/tests/__init__.py` (vacío) y `materiales/legacy/tests/test_legacy_module.py` con pytest, datos sintéticos mínimos por caso, y al menos estas pruebas:
   - `test_filtrar_por_periodo_incluye_extremos`: dos tickets en los bordes exactos del periodo deben quedar incluidos.
   - `test_resumir_por_area_no_acumula_entre_llamadas`: dos invocaciones sucesivas sin pasar `acumulador` dan el mismo resultado.
   - `test_contar_reaperturas_usa_campo_reaperturas`: un ticket reabierto-y-cerrado-de-nuevo (`estado` distinto de "reabierto", `reaperturas>0`) cuenta; un ticket con `estado` en mayúsculas variables pero `reaperturas="0"` no cuenta.
5. Ejecutar `pytest materiales/legacy/tests/` desde la raíz del repo y confirmar que las 3 pruebas pasan contra el código corregido. Verificar manualmente (p. ej. con `git stash` temporal del fix o revisando el diff) que cada prueba falla si se revierte su fix correspondiente.

**Tabla de causas raíz:**

| Síntoma | Función | Causa raíz (una línea) |
| ------- | ------- | ------------------------ |
| S1 — informe pierde tickets | `filtrar_por_periodo` | Comparación estricta (`>`/`<`) excluye los tickets creados exactamente en las fechas límite del periodo, pese a que el periodo debe incluir ambos extremos. |
| S2 — cifras infladas en llamadas sucesivas | `resumir_por_area` | El parámetro `acumulador={}` es un diccionario mutable evaluado una sola vez al definir la función, por lo que persiste y se acumula entre llamadas sucesivas dentro del mismo proceso. |
| S3 — reaperturas por debajo de lo real | `contar_reaperturas` | Compara el `estado` actual del ticket contra `"reabierto"` de forma exacta, ignorando variantes de mayúsculas y tickets que fueron reabiertos y luego cerrados de nuevo, en vez de usar el campo `reaperturas` que es el contador autoritativo. |

## Acceptance criteria

- [ ] `filtrar_por_periodo(tickets, inicio, fin)` incluye tickets con `fecha_creacion` igual a `inicio` o igual a `fin`.
- [ ] Dos llamadas sucesivas a `resumir_por_area(tickets)` sin pasar `acumulador` explícito devuelven resultados idénticos e independientes entre sí.
- [ ] `contar_reaperturas(tickets)` cuenta un ticket con `reaperturas > 0` sin importar su `estado` actual, y no cuenta un ticket con `reaperturas == 0` sin importar las mayúsculas de su `estado`.
- [ ] Cada uno de los 3 fixes tiene un comentario de una línea en `legacy_module.py` explicando su causa raíz.
- [ ] `materiales/legacy/tests/test_legacy_module.py` tiene al menos una prueba por defecto (3 en total), cada una falla contra el código sin el fix correspondiente y pasa con el fix aplicado.
- [ ] `pytest materiales/legacy/tests/` corre en verde desde la raíz del repo, sin necesidad de red ni del CSV de 2000 filas.
- [ ] Ninguna función de `legacy_module.py` ajena a S1/S2/S3 cambia de comportamiento.

## Decisions

- **Sí:** fix mínimo y quirúrgico en las 3 funciones señaladas, sin reescribir el módulo — así lo pide explícitamente el docstring del módulo ("No reescriba el módulo completo. Corrija lo que está mal.").
- **Sí:** para S3, usar el campo `reaperturas` como fuente de verdad en vez de solo normalizar mayúsculas de `estado`. Confirmado con los datos reales (`materiales/datos/tickets_historicos.csv`): existen 58 tickets con `reaperturas>0` cuyo `estado` actual ya no es "reabierto", que una normalización de mayúsculas por sí sola seguiría subcontando.
- **Sí:** pruebas con datos sintéticos mínimos definidos en el propio archivo de test, no con el CSV real de 2000 filas. Hace explícita y legible la causa de cada caso rojo→verde, sin depender de qué filas específicas trae el CSV en un momento dado.
- **Sí:** comentario de una línea junto a cada fix en el código, más la tabla-resumen en este spec — cubre tanto a quien lee el código en el futuro como el registro histórico de la corrección.
- **Sí:** ubicar las pruebas en `materiales/legacy/tests/test_legacy_module.py`, seguidno la misma convención de carpeta `tests/` usada en `api_propia/` y `clasificador_ia/`.
- **No:** agregar `pytest.ini` o configuración global nueva. El discovery por defecto de pytest desde la raíz del repo ya encuentra `materiales/legacy/tests/`, igual que los demás módulos.

## What is **not** in this spec

- Otros defectos de `legacy_module.py` no ligados a S1/S2/S3 (robustez de `parsear_fecha`, comportamiento del bloque `__main__`, etc.).
- Reescritura o modernización general del módulo.
- Integración de `legacy_module.py` con `api_propia/` o `clasificador_ia/`.
- Cambios al esquema de datos (`materiales/datos/esquema.sql`) o al CSV histórico.

Cada uno de esos, si se necesita, va en su propio spec.

---
layout: post
title: "Evaluar agentes en ADK: lo que ya viene nativo y casi nadie usa"
date: 2026-11-07 00:30:00 -0300
description: "ADK trae 17 métricas prediseñadas, un modo de replay sin modelo y simuladores de usuario y de entorno. Qué cubre, qué sigue siendo código propio y cómo armar un gate que no dependa de un LLM no determinista."
thumbnail: /assets/img/evaluar-agentes-en-adk-lo-que-ya-viene-nativo/thumb.jpg
linkedin_text: "ADK trae 17 métricas de evaluación prediseñadas desde la versión 2.10. Los tutoriales suelen usar dos: trayectoria de herramientas y similitud de la respuesta.\n\nLo que casi nadie usa: adk test reproduce una corrida grabada y reemplaza el modelo por un MockModel. Cuesta cero y da siempre el mismo resultado, que es lo que necesita un gate de despliegue. Un control que cambia de veredicto entre corridas no es un control.\n\nMi regla de diseño: el gate corre en una capa determinista y el juez LLM corre en el ciclo de release, no en cada commit. En una demo mía, el juez costó más de 10 veces lo que cuesta el agente.\n\nLo que ADK no trae: intervalos de confianza ni pass^k sobre las corridas repetidas (no los encontré en el código de la 2.13). τ-bench muestra por qué importa: según su abstract, agentes de punta resuelven menos del 25 % de las tareas de retail si se les exige acertar 8 veces (arXiv:2406.12045).\n\nUn número sin cantidad de corridas no es evidencia. ¿Cuántas corridas tiene detrás la métrica de tu agente?\n\n#IAagéntica #ADK"
---

Si evaluaste un agente con el Agent Development Kit (ADK) siguiendo un tutorial, es probable que hayas usado dos criterios: la trayectoria de herramientas y la similitud de la respuesta. No es casualidad. Son los valores por defecto: `tool_trajectory_avg_score` en 1.0 y `response_match_score` en 0.8.

Pero el framework trae bastante más de lo que se suele mostrar. Revisé el código de ADK entre la 2.10 y la 2.13 para ver qué hay, qué sigue siendo trabajo propio y cómo lo ordenaría para diseñar un sistema de evaluación. Al final cuento qué comprobé y qué no.

## Lo que trae ADK

### Diecisiete métricas, no dos

En el código hay 13 métricas prediseñadas en las versiones 2.3 a 2.9, y 17 desde la 2.10. La 2.0.0 ya traía 12, según la rueda que revisé en su momento. Agrupadas por lo que miden:

| Qué mide | Métricas |
|---|---|
| **Trayectoria de herramientas** | `tool_trajectory_avg_score`, con modos de coincidencia `EXACT`, `IN_ORDER` y `ANY_ORDER` |
| **Respuesta final** | `response_match_score` (ROUGE-1), `response_evaluation_score`, `final_response_match_v2` (juez con referencia), `rubric_based_final_response_quality_v1` |
| **Fidelidad y seguridad** | `hallucinations_v1` (contrasta la respuesta con la traza de herramientas), `safety_v1` |
| **Uso de herramientas con rúbricas** | `rubric_based_tool_use_quality_v1` |
| **Multi-turno y usuario simulado** | `per_turn_user_simulator_quality_v1`, `multi_turn_task_success_v1`, `multi_turn_trajectory_quality_v1`, `multi_turn_tool_use_quality_v1`, `rubric_based_multi_turn_trajectory_quality_v1` |
| **Eficiencia** | `tool_call_count_v1`, `inference_call_count_v1`, `token_usage_v1`, `invocation_duration_v1` |

Las cuatro de eficiencia son informativas: se reportan siempre, no se pueden apagar y nunca aprueban ni fallan. Según mi revisión, desde la 2.12 poner un umbral sobre una de ellas lanza un `ValueError` (en la 2.10 se ignoraba).

### Simuladores

Dos piezas que casi nunca aparecen en los ejemplos:

- **Simulador de usuario.** Un `ConversationScenario` define un mensaje inicial y un plan de conversación (y, opcionalmente, un perfil de usuario) que un usuario simulado sigue turno a turno. Sirve para evaluar la coherencia en varios turnos sin escribir cada diálogo a mano.
- **Simulador de entorno.** `EnvironmentSimulationFactory` crea un callback o un plugin que intercepta las llamadas a herramientas. Su configuración admite inyectar errores, códigos de error HTTP, latencia o respuestas completas, con una probabilidad dada. Es la forma de probar esos casos raros pero catastróficos que un set de ejemplos felices no cubre.

### Replay sin modelo: el respaldo nativo de una idea de diseño

La tesis que más me importa de todo el tema es esta: **un gate de despliegue no puede depender de un LLM no determinista.** Si el control que decide si algo sale a producción cambia de veredicto entre corridas, no es un control.

ADK tiene una respuesta nativa:

- **`adk test`** corre pytest sobre archivos JSON de test del agente. En el modo de replay, reemplaza la llamada al modelo por un `MockModel`: reproduce lo grabado sin consultar a ningún LLM. Cuesta cero y da siempre el mismo resultado.
- **`adk conformance record` y `adk conformance test`** graban y verifican el comportamiento del agente a partir de especificaciones en YAML.

Es algo que muchos equipos terminan armando a mano, con salidas simuladas propias. Saber que el framework ya lo trae evita reinventarlo.

## Tres capas de evaluación

Lo que me resultó más útil para explicarle esto a un equipo es separar la evaluación por *dónde corre* y *cuánto cuesta*:

| Capa | Qué corre | Dónde | Costo |
|---|---|---|---|
| **A. Determinista** | Trayectoria, ROUGE, eficiencia, métricas propias en Python, replay | Laptop o CI, sin modelo en el gate | Cero |
| **B. Juez local** | Respuesta contra referencia, rúbricas, alucinación, simulador de usuario | Proceso local con un modelo | Más de 10 veces el costo del agente (medido en una demo propia) |
| **C. Servicio gestionado** | Métricas multi-turno, seguridad, generación de escenarios | Plataforma en la nube | Dependencia de proveedor, y tus datos viajan a su región |

La regla que sale de ahí: **el gate corre en la capa A**. El juez (B) corre en el ciclo de *release*, no en cada commit. El servicio gestionado (C) se reserva para escala y multi-turno, a cambio de mover datos a la nube.

## Lo que sigue siendo código propio

ADK cubre mucho, pero hay cosas que no encontré y que tenés que escribir vos:

- **Recall, precisión y exactitud de parámetros graduados.** ADK puntúa cada invocación con 1 o 0 y promedia, sin la graduación que tiene una métrica clásica de recuperación.
- **El «y» lógico de un task success.** Que una tarea cuente como lograda solo si acertaron las herramientas *y* los parámetros *y* las frases esperadas, con un umbral por cada métrica, es una decisión tuya.
- **Métricas de conteo sin promediar.** Para acciones irreversibles el objetivo es cero, y un promedio puede esconder un caso grave detrás de muchos buenos.
- **Intervalos de confianza y pass^k sobre las corridas repetidas.** El parámetro `num_runs` repite todo el dataset (vale 2 por defecto) y `AgentEvaluator.evaluate` termina con un `assert not failures`. En el código de `evaluation/` de la 2.13 no encontré ningún cálculo de intervalos ni de pass^k.
- **Calibración del juez contra etiquetas humanas.**

## La métrica que da 1,0 sobre el vacío

Una pregunta que conviene hacerle a cualquier métrica propia: **¿qué devuelve cuando no hay nada que medir?** Para la trayectoria de herramientas hay tres casos «vacíos», y cada uno debería dar un resultado distinto:

1. **Esperado vacío, predicho vacío.** El agente correctamente no llamó a ninguna herramienta. Debería puntuar perfecto.
2. **Esperado vacío, predicho no vacío.** El agente llamó a herramientas que nadie esperaba. La precisión tiene que caer.
3. **Esperado no vacío, predicho vacío.** El agente no hizo lo que debía. El recall tiene que ser cero.

Una implementación que resuelve mal alguno de los tres produce un número que parece sano y no mide nada. No es un problema teórico: un trabajo de 2025 (ABC, [arXiv:2507.02825](https://arxiv.org/abs/2507.02825)) encontró que un benchmark agéntico muy usado, TAU-bench, cuenta las respuestas vacías como exitosas. Es la misma trampa, a escala de benchmark.

## Un número sin *n* no es evidencia

Dos fuentes de ruido que un gate serio tiene que declarar:

**Variabilidad entre corridas.** Los agentes son estocásticos. τ-bench ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)) propone la métrica pass^k, la probabilidad de que el agente tenga éxito en *k* intentos independientes, y según su abstract muestra que agentes de punta resuelven menos del 25 % de las tareas de retail si se les exige acertar en 8 corridas. Fijar la temperatura en cero no alcanza: el juez y las actualizaciones silenciosas del modelo también varían. El gate tiene que fijar cuántas corridas hace (*n*) y cómo las agrega, y reportar un intervalo.

**El juez como componente.** Un juez LLM es otro modelo en producción, con costo, sesgo y varianza. Los trabajos sobre LLM-as-judge ([Zheng et al., arXiv:2306.05685](https://arxiv.org/abs/2306.05685)) documentan sesgos de posición, de verbosidad y de autopreferencia. En la práctica eso se traduce en dos cuidados: no usar el mismo modelo como agente y como juez sin advertirlo, y hacer un **control negativo**, darle al juez respuestas malas a propósito y comprobar que las detecta. Un juez que aprueba todo también da 1,0.

## Qué decide el arquitecto

Escribir los casos y las rúbricas es trabajo de producto y de expertos de dominio. Calibrar el juez es de ingeniería de ML. Lo que sí es del arquitecto es el diseño del sistema de control:

| Decisión | Detalle |
|---|---|
| **Qué se evalúa y con qué evaluador** | Resultado, trayectoria o estado final; regla, juez o humano, según cada criterio de aceptación |
| **Topología del arnés** | Local, CI con replay o servicio gestionado, y dónde viven los datos y los resultados |
| **El gate** | Qué bloquea, qué escala a una persona, quién firma, qué se promedia y qué se cuenta, y cuántas corridas |
| **Presupuesto de evaluación** | Frecuencia, tamaño del juez y cantidad de casos |

Un gate útil tiene tres salidas y no dos: verde, rojo, y *ambiguo*, que escala a una persona que firma. Una métrica sin firmante no es un control.

## Qué comprobé y qué no

- **Contrastado en el código de ADK 2.10, 2.12 y 2.13:** el conteo de métricas (13 en 2.3–2.9, 17 desde la 2.10), los criterios por defecto, el valor de `num_runs`, el `assert not failures`, que `adk test` reemplaza la llamada al modelo por un `MockModel`, los subcomandos `adk conformance record` y `test`, los modos `EXACT`, `IN_ORDER` y `ANY_ORDER`, la estructura de `ConversationScenario` (mensaje inicial, plan y perfil de usuario) y que `EnvironmentSimulationFactory` admite inyectar errores, códigos HTTP, latencia y respuestas.
- **Tomado de una revisión anterior mía, sin repetirla:** que la 2.0.0 traía 12 métricas y que `adk test` ya existía en esa versión, y el `ValueError` por umbral en métricas de eficiencia desde la 2.12.
- **No ejecuté nada con un modelo real:** ni el replay de `adk test` ni una migración entre versiones. El costo del juez (más de 10 veces el del agente) es una medición de una demo propia con un caso, no una cifra general.
- Los resultados de τ-bench y de ABC los tomé de los abstracts de los papers, no de una lectura completa.
- ADK cambia rápido. Si lo usás, verificá la versión, porque esto describe lo que encontré entre la 2.10 y la 2.13.

Fuentes: documentación de ADK sobre [evaluación](https://adk.dev/evaluate/), [criterios](https://adk.dev/evaluate/criteria/) y [simulación de usuario](https://adk.dev/evaluate/user-sim/); el código fuente de ADK; τ-bench ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045)) y su sucesor τ²-bench ([arXiv:2506.07982](https://arxiv.org/abs/2506.07982)); Zheng et al. ([arXiv:2306.05685](https://arxiv.org/abs/2306.05685)); ABC ([arXiv:2507.02825](https://arxiv.org/abs/2507.02825)).

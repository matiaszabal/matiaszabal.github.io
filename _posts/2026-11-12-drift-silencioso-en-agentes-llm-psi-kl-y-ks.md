---
layout: post
title: "Drift silencioso en agentes LLM: PSI, divergencia KL y test KS"
date: 2026-11-12 05:30:00 -0300
description: "Un agente puede degradarse sin lanzar un solo error. Tres métricas estadísticas para detectarlo, con un ejemplo numérico de cada una y cuándo usar cuál."
thumbnail: /assets/img/drift-silencioso-en-agentes-llm-psi-kl-y-ks/thumb.jpg
---

Un agente en producción puede empeorar sin lanzar una sola excepción. Alguien cambia una línea del *system prompt* y, sin que salte ninguna alarma, el agente empieza a llamar a otra herramienta, a rechazar menos pedidos peligrosos o a dar más vueltas antes de responder. Los logs de error están limpios. Lo que cambió es la **distribución** de su comportamiento.

Para detectarlo se comparan dos distribuciones: la de una **línea base** (*baseline*, el comportamiento certificado) y la de una ventana reciente de producción. Hay tres métricas clásicas para hacerlo, y cada una sirve para un tipo de dato distinto. Los números de los ejemplos son ilustrativos: los armé para mostrar el cálculo, no salen de un sistema real.

## PSI: para categorías (qué herramienta, qué intención)

El **Population Stability Index** nació en la industria crediticia para medir la estabilidad de modelos predictivos. Compara, categoría por categoría, la proporción actual con la esperada:

> PSI = suma de (actual − esperado) × ln(actual / esperado)

La lectura habitual, heredada de esa industria, es: por debajo de 0,10, estabilidad normal; entre 0,10 y 0,25, desvío moderado; por encima de 0,25, desvío severo.

**Ejemplo con uso de herramientas.** Un agente financiero tiene tres herramientas: una consulta interna a la base de datos, una API externa de cotizaciones (paga y más lenta) y una calculadora local.

| Herramienta | Baseline | Producción |
|---|---|---|
| Consulta a la base interna | 60 % | 20 % |
| API externa de cotizaciones | 30 % | 70 % |
| Calculadora local | 10 % | 10 % |

Los términos del PSI son 0,4394 (base interna) + 0,3389 (API externa) + 0 (calculadora) = **0,7783**, muy por encima de 0,25.

El agente no lanzó errores, pero dejó de consultar la base interna y abusa de la API externa. Eso se traduce en más costo (en este ejemplo, las llamadas a la API pasan de 30 % a 70 % del total, más del doble), más latencia y riesgo de topar con límites de tasa. Una causa común es un cambio de prompt con una instrucción ambigua del estilo «respondé siempre con los datos más actualizados posibles», que lleva al modelo a desconfiar de la base local.

**Cuándo usarlo:** deriva en la selección de herramientas, deriva en el ruteo de intenciones hacia subagentes, y reportes a comités de riesgo, porque resume todo en un solo número con umbrales conocidos.

## Divergencia KL: para distribuciones de probabilidad (tokens, embeddings)

La **divergencia de Kullback-Leibler** mide qué tan sorprendente es la distribución de producción P respecto de la de referencia Q:

> KL(P ‖ Q) = suma de P(x) × ln(P(x) / Q(x))

Es **asimétrica** y muy sensible a los eventos que en la referencia casi no ocurrían (Q cercano a cero). Esa propiedad es justo la que la hace útil para seguridad.

**Ejemplo con un jailbreak.** Se monitorea cómo arrancan las respuestas ante preguntas sobre credenciales o secretos:

| Arranque de la respuesta | Baseline (Q) | Producción (P) |
|---|---|---|
| «Lo siento, no puedo…» | 90,0 % | 10,0 % |
| «Como asistente ético…» | 8,0 % | 4,0 % |
| «Acceso denegado…» | 1,0 % | 1,0 % |
| «Claro, aquí tienes…» | 0,5 % | 40,0 % |
| «El password es…» | 0,5 % | 45,0 % |

KL = −0,2197 − 0,0277 + 0 + 1,7528 + 2,0249 = **3,53 nats**. Las dos filas que casi no existían en la referencia aportan casi todo el valor.

Para este tipo de señal hace falta acceso a la distribución de los primeros tokens, lo que no siempre se tiene con un modelo servido por API. Y con ceros en la referencia, el cálculo requiere suavizado (por ejemplo, de Laplace).

**Cuándo usarlo:** seguridad en tiempo de ejecución (jailbreak, inyección), deriva semántica en embeddings de sistemas RAG y estabilidad de políticas en modelos ajustados con aprendizaje por refuerzo.

## KS: para variables continuas (latencia, tokens, costo)

El **test de Kolmogorov-Smirnov** compara dos distribuciones acumuladas y toma la **distancia máxima** entre ambas (el estadístico D), con un valor p que dice si la diferencia es estadísticamente significativa. No necesita agrupar los datos en categorías arbitrarias.

**Ejemplo con pasos de razonamiento.** Se mide cuántas llamadas a herramientas hace el agente antes de responder:

| Pasos | Acumulado baseline | Acumulado producción | Diferencia |
|---|---|---|---|
| ≤ 1 | 30 % | 5 % | 0,25 |
| ≤ 2 | 65 % | 15 % | 0,50 |
| ≤ 3 | 85 % | 35 % | **0,50** |
| ≤ 4 | 95 % | 60 % | 0,35 |
| ≤ 5 | 100 % | 100 % | 0,00 |

D = 0,50. En el baseline, el 85 % de las interacciones se resolvía en 3 pasos o menos; en producción, solo el 35 %. El agente entró en un régimen de «sobre-pensamiento»: reintenta herramientas, duplica el consumo de tokens y la latencia, y se acerca al límite de la ventana de contexto. Sin errores sintácticos.

El valor p depende del tamaño de la muestra, que en el ejemplo no está especificado. Con una muestra grande, diferencias mínimas salen «significativas»: conviene mirar D, no solo p.

**Cuándo usarlo:** latencias, duración de sesiones, tokens y costos; validar si una caída de una métrica de calidad continua es significativa; y comparar un despliegue *canary* o un experimento A/B.

## Comparación

| | PSI | KL | KS |
|---|---|---|---|
| **Dato** | Categórico o en intervalos | Discreto (tokens) o densidades | Continuo |
| **Simetría** | Simétrico | Asimétrico, sensible a Q cercano a 0 | Distancia máxima puntual |
| **Decisión** | Umbrales 0,10 / 0,25 | Magnitud en nats vs. baseline | Valor p |
| **Muestra** | Moderada por intervalo | Sensible a ceros (suavizado) | Funciona con muestras medianas |
| **En agentes** | Herramientas, ruteo | Jailbreak, RAG | Latencia, tokens, costo |

## Un pipeline en cuatro fases

1. **Instrumentación**: cada llamada registra herramienta elegida, tokens, latencia y la versión del agente (por ejemplo, con Langfuse).
2. **Almacenamiento** de los eventos en una base analítica.
3. **Cálculo periódico**: un proceso toma la ventana reciente (digamos, las últimas 24 horas), la compara con el baseline y calcula PSI, KL y KS.
4. **Reacción**: si se pasan los umbrales, se publica el score para trazabilidad, se alerta al equipo y se puede degradar la autonomía a confirmación humana o revertir el prompt.

## Qué es opinión y qué no

- Los umbrales de PSI (0,10 y 0,25) vienen de la práctica crediticia. **Los de KL y KS no son estándares**: el valor de 2,0 nats o p < 0,01 que se usa en el pipeline es una elección de diseño que hay que calibrar con los datos propios.
- Los tres ejemplos numéricos son inventados para mostrar el cálculo; la aritmética sí se puede reproducir con las tablas.
- Las causas atribuidas a cada deriva (prompt ambiguo, reintentos por respuestas confusas) son hipótesis típicas, no un diagnóstico: una alerta de drift indica que algo cambió, no por qué.
- Un baseline mal elegido (poco representativo o ya degradado) invalida todo lo anterior.

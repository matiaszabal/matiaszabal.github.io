---
layout: post
title: "Crear un agente a partir de un arquetipo sin escribir el código"
date: 2026-09-09 11:05:00 -0300
description: "«Sin escribir código» no es «sin especificar». Qué se pudo verificar con ADK 2, dónde el camino se corta y qué le respondería a un alumno que lo pregunta."
thumbnail: /assets/img/crear-un-agente-a-partir-de-un-arquetipo-sin-escribir-el-codigo/thumb.jpg
---

Una pregunta que aparece en el curso: *¿puedo implementar un arquetipo de agente sin escribir código?* La respuesta corta, con lo que pude verificar en ADK 2.9.1, es: **sin escribir el código a mano, sí, con condiciones; sin código, no, y sin especificar, tampoco.**

Este post cuenta qué comprobé, qué no y cómo lo explico. Las versiones y los resultados son de pruebas puntuales y pueden haber cambiado.

## Punto de partida: no hay un camino declarativo maduro

Revisé dos cosas.

**Skills y `agents-cli`.** El toolkit de línea de comandos cubre el ciclo de vida del proyecto (plantillas, evaluación, despliegue, publicación, observabilidad), pero no el diseño de la orquestación. No encontré ningún skill que traduzca los seis arquetipos a primitivas de ADK. Falta ese puente: qué primitiva usar para el lazo de Reflection, cómo modelar el bloc de notas de Deep Research, dónde va el punto de aprobación de Planner-Executor.

**Configuración en YAML.** ADK trae un modo de configuración declarativa, pero en la versión que probé figura como experimental y su propio CLI avisa que no está listo. Aun así, un `Workflow` con aristas se puede cargar desde YAML, con esa salvedad.

**Repos de referencia.** Revisé `google/adk-recipes` (antes `adk-samples`). Hay agentes que se acercan a Deep Research (`deep-search`), a Reflection (`llm-auditor`, parcialmente) y a Planner (`sdlc-task-planner`, parcialmente). No encontré ejemplos de Reflex ni de Query Decomposition, y de ReAct solo un demo de juguete. Leí los README, no el código, y no verifiqué qué versión de ADK usa cada agente.

## La respuesta que le doy a un alumno

> «Sin escribir código, pero no sin especificar. Hoy no hay una vía declarativa madura para los arquetipos en ADK 2. Lo que sí podés hacer es diseñar el arquetipo con tres preguntas (quién decide qué sigue, con qué contexto, cuándo se detiene) y pedirle a un asistente de código que lo construya. Vos no tipeás el código, pero tenés que poder revisarlo.»

Por qué esa respuesta:

1. **La especificación es el trabajo del alumno.** Las tres preguntas, respondidas por arquetipo, funcionan como el prompt de diseño para el asistente.
2. **Las mismas tres preguntas sirven de lista de revisión**, incluso sin leer todo el código: ¿hay un tope externo de iteraciones?, ¿los contextos están aislados?, ¿el plan o el borrador se puede inspeccionar? El mayor riesgo del código generado es un lazo sin límite.
3. **Se valida con herramientas, no con fe**: la traza de `adk web` muestra qué pasó, y la evaluación del CLI mide el comportamiento.
4. **Si existe una plantilla real, partir de ahí.** Para Deep Research hay una; para el resto no encontré.

Lo que no le prometo: que el YAML alcanza para cualquier arquetipo, ni que el resultado funcione sin revisión.

## Lo que probé: los seis arquetipos con ejemplos propios

Armé un esqueleto de skill que mapea cada arquetipo a primitivas de ADK 2, y un ejemplo mínimo por arquetipo. Cada uno tiene pruebas sin modelo y corridas reales, en pocas repeticiones (entre 3 y 9 por caso). Lo que sigue son hallazgos, no mediciones de rendimiento.

- **Query Decomposition.** El aislamiento de contexto de un agente invocado desde un worker paralelo **no es automático**. Con `include_contents='none'` recibe un contenido; por defecto recibió cuatro, incluido el plan completo. Hay que pedir el aislamiento explícitamente.
- **Reflection.** Con el contexto por defecto, el contexto crece en cada ronda. El código debe tener prioridad sobre el crítico, y un validador con falsos positivos contamina el lazo.
- **Planner-Executor.** Funcionó con un ejecutor determinista como nodo dinámico, aprobación humana con `RequestInput` y una replanificación que conserva lo ya hecho.
- **ReAct.** En 4 de 9 corridas reales, el agente afirmó o prometió un reembolso **sin llamar a la herramienta**. Además, el tope de llamadas lanza una excepción sin darle texto al usuario, y el valor por defecto es alto (500 llamadas).
- **Reflex.** Un mensaje logró hacerse asignar la cola prioritaria (una inyección, 0 de 3 veces la segunda vez). Y «respuesta en milisegundos» solo vale para reglas: unos 7 ms con reglas, unos 2,8 s si el que decide es un LLM.
- **Deep Research.** Investigadores ReAct en paralelo se filtran las búsquedas entre hermanos, salvo que se active una opción de sub-rama. En las 3 corridas el evaluador nunca quedó conforme: lo que garantizó el fin fue el presupuesto fijado en código. Las citas del informe se diluyen, con hasta 6 fuentes por afirmación.

En estos casos **dejé visibles los fallos** y no apliqué mitigaciones. Mostrar el fallo es parte del material didáctico.

## Respuesta a «¿sin escribir código?» con YAML

Probé un `Workflow` de Reflection **descrito en YAML**. Carga con el mecanismo experimental, equivale al de Python (13 chequeos) y corre con un modelo real, tanto por script como por la interfaz web.

Pero el «sin código» es **parcial**: los nodos de decisión (el validador, el tope de rondas, la prioridad sobre el crítico), los esquemas y los callbacks siguen siendo Python, referenciado por ruta de módulo. Solo lo probé con Reflection.

## Qué es opinión y qué no

- Todo lo anterior corresponde a una versión específica (ADK 2.9.1 y una versión de `agents-cli` que ya figuraba como desactualizada respecto de la más nueva). Puede haber cambiado.
- Los resultados con modelo real salen de entre 3 y 9 corridas por caso: son hallazgos para tener presentes, no tasas de fallo.
- No probé el camino por `agents-cli scaffold` ni por `agents-cli eval`, ni el YAML de Query Decomposition, ni repetí con datos reales aprobados.
- De los repos de referencia leí los README, no el código.
- La recomendación de «especificar con tres preguntas y revisar con las mismas tres» es una práctica que me resulta útil, sin estudio comparativo detrás.

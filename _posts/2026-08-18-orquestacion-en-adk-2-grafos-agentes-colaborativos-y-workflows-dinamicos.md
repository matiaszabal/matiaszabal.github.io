---
layout: post
title: "Orquestación en ADK 2: grafos, agentes colaborativos y workflows dinámicos"
date: 2026-08-18 09:15:00 -0300
description: "Tres lugares donde puede vivir el control de flujo de un agente: un grafo declarado, el modelo o código Python. Cómo se comparan y cuándo elegir cada uno."
thumbnail: /assets/img/orquestacion-en-adk-2-grafos-agentes-colaborativos-y-workflows-dinamicos/thumb.jpg
---

ADK 2 cambia dónde vive el control de flujo de una aplicación de agentes. Pasa del *prompt* a una **estructura de ejecución explícita** que el framework planifica, traza y puede reanudar. Este post resume los tres patrones de orquestación que ofrece y cómo elegir entre ellos. La pregunta que ordena todo es una sola: **¿quién decide qué corre después?**

## El problema: el control de flujo escondido en un prompt

Un prompt gigante que promete todo («si pasa A hacé B, si no, C, y además consultá D») mezcla razonamiento con control de flujo. El resultado es difícil de probar y puede producir datos inventados. La tesis es que el control de flujo (qué corre, en qué orden, en paralelo o no, cuántas veces, bajo qué condición) es una **decisión de diseño** y puede ubicarse en tres lugares:

- en **una estructura declarada**: un grafo de nodos y aristas,
- en **el modelo**: un LLM que elige a quién delegar,
- en **código imperativo**: Python que llama nodos en tiempo de ejecución.

La regla que resume el codelab de ADK: *lo predecible queda en funciones, las reglas claras se vuelven ruteo explícito y el razonamiento lo hace el modelo.*

## Pilar 1: workflows de grafo

El flujo se dibuja **antes de que llegue el input**. Los nodos son funciones o agentes, las aristas pueden ser condicionales y el framework valida la estructura antes de correr. Eso permite fallar temprano.

Lo que ofrece:

- **Ruteo explícito por reglas.** El «próximo paso» lo decide un `if` en un nodo función, que cuesta cero llamadas al modelo.
- **Paralelismo** con *fan-out* y un nodo de unión (`JoinNode`).
- **Ciclos y workflows anidados**: un grafo puede ser un nodo de otro grafo.
- **Estructura inspeccionable**: se puede consultar el grafo como dato antes de ejecutarlo.
- **Pruebas sin modelo**: los nodos función y el router son funciones puras.

Un agente también puede ser un nodo del grafo. Así, el modelo se usa donde hay razonamiento y el resto es código.

## Pilar 2: agentes colaborativos

Un **coordinador** (un `LlmAgent` con una lista `sub_agents`) elige entre especialistas. Cada subagente tiene un modo que define cómo se relaciona con el coordinador:

| | `chat` | `task` | `single_turn` |
|---|---|---|---|
| ¿Habla con el usuario? | Sí, todo el tiempo | Solo preguntas aclaratorias hasta terminar | No |
| ¿Vuelve al padre? | Manual, con otra transferencia | Automático, al terminar la tarea | Automático, al terminar el turno |
| ¿Paralelo? | No | No | Sí |
| Contrato de datos | Ninguno (prosa) | Esquemas de entrada y salida | Esquemas de entrada y salida |

- **`chat`** es el modo correcto para un asistente abierto y el incorrecto para un paso de pipeline. El coordinador transfiere toda la conversación a un especialista y no hay síntesis ni retorno automático.
- **`task`** sirve cuando el usuario debe conversar con el especialista hasta cierto punto y después el control vuelve al padre con un resultado validado contra un esquema.
- **`single_turn`** sirve para especialistas que se pueden llamar en paralelo y sin conversación.

El costo de este patrón es el determinismo: qué subconjunto de especialistas elige el coordinador lo decide el modelo. Por eso es más difícil de probar sin llamar a un LLM.

## Pilar 3: workflows dinámicos

El flujo **se escribe en Python**, con `if`, `while`, recursión y `asyncio.gather`. El framework aporta lo que antes había que armar a mano: ejecución de nodos hijos, trazado, punto de control (*checkpoint*) y reanudación. La primitiva común es `ctx.run_node`.

Es el patrón para cuando **el ancho o la profundidad del trabajo dependen del input**. Por ejemplo, descomponer una pregunta en sub-preguntas y, si alguna es muy estrecha, investigarla más a fondo.

Lo dinámico se acota **desde el código**. En el caso de estudio del informe, el ancho se limita con el esquema (máximo 7 sub-preguntas), la profundidad con una constante y los hijos por rama con otro máximo. Con esos límites, la cota superior de llamadas al modelo se calcula de antemano: 1 + 7 + 7×3 + 1 = 30.

Una advertencia que aprendí en las pruebas: si la recursión depende de un booleano que completa el modelo («¿hace falta profundizar?»), puede no ocurrir nunca. Con la pregunta por defecto, en las corridas que hice el modelo no profundizó en ninguna rama. Con preguntas más estrechas sí lo hizo en la mayoría. Son pocas corridas y dependen del modelo: no son una garantía.

## Comparación de los tres

| Criterio | Grafo | Colaborativo | Dinámico |
|---|---|---|---|
| **Decide el próximo paso** | El grafo y un `if` en un nodo | El LLM coordinador | Código Python |
| **Determinismo del flujo** | Alto | Bajo | Alto respecto de la lógica escrita |
| **Probable sin modelo** | Sí | Difícil | Sí, para la lógica de orquestación |
| **Estructura visible antes de correr** | Completa | Ninguna | Parcial |
| **Mejor para** | Procesos con forma conocida y ramas explícitas | Pedidos cuyo subconjunto de especialistas varía | Ancho o profundidad que dependen del input |

En el caso comparable que armé en los tres estilos, el grafo usó 1 llamada al modelo (solo el agente elegido), el colaborativo al menos 1 más una por especialista más la síntesis, y el dinámico entre 5 y 30 según ancho y profundidad.

## Los tres se componen

No son excluyentes. Por debajo comparten la misma maquinaria de nodos y `ctx.run_node`:

- un agente LLM puede ser un nodo dentro de un grafo,
- un grafo puede ser un nodo dentro de otro,
- un workflow dinámico puede orquestar funciones, agentes, herramientas y otros workflows.

La regla práctica: **elegir el patrón por parte del problema, no por aplicación.** Así se evita volver al prompt gigante.

## Cómo elegir

1. ¿Alcanza una plantilla prearmada (secuencial, paralelo, lazo)? Usarla y parar. Según el informe, esas plantillas figuran como deprecadas en las versiones revisadas, que prefieren `Workflow`.
2. ¿Se puede dibujar el flujo antes de que llegue el input? **Grafo.**
3. ¿Hay un equipo conocido y el pedido elige el subconjunto? **Colaborativo.** Si el usuario debe conversar con el especialista: `task`. Si va en paralelo y sin conversación: `single_turn`. Si es un asistente abierto: `chat`.
4. ¿La forma del trabajo depende del input? **Dinámico.**

## Anti-patrones que vale la pena evitar

- Un prompt gigante que promete todo.
- Que un LLM decida lo que una regla ya decide: un `if` cuesta cero llamadas.
- Un router sin ruta por defecto sobre una entrada no acotada: la rama termina en silencio.
- Un ciclo condicional sin condición de salida garantizada: el framework no lo acota.
- Funciones síncronas bloqueantes dentro de un fan-out: se serializan y anulan el paralelismo.
- Efectos colaterales en el cuerpo de un orquestador dinámico: el cuerpo se re-ejecuta al reanudar.
- Capturar excepciones de forma amplia: enmascara reintentos y pausas humanas.
- Datos grandes en el estado de sesión: no es un almacén de datos.

## Qué es opinión y qué no

- El informe en el que me baso revisó el código de **ADK 2.3.0** y comprobó solo algunos casos en una versión posterior. Los detalles de la API pueden haber cambiado.
- Diez experimentos deterministas, sin llamadas a un modelo, verifican los mecanismos del grafo y de la orquestación dinámica. Los modos de colaboración se observaron en pocas corridas con Gemini 2.5 Flash, y esas conductas dependen del modelo.
- No verifiqué la reanudación tras un fallo de proceso ni el comportamiento con servicios de sesión persistentes. Los experimentos usan sesión en memoria.
- Los tiempos y conteos de llamadas son mediciones puntuales para mostrar órdenes de magnitud, no una referencia de rendimiento.
- La documentación oficial se leyó mediante resúmenes automáticos y se contrastó con el código y con los experimentos. Varias páginas relacionadas no se consultaron.

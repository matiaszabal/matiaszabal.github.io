---
layout: post
title: "Agentic AI Engineer vs. Architect: dos centros de gravedad, no dos cajas"
date: 2026-06-26 09:05:00 -0300
description: "Los roles de Engineer y Architect en sistemas agénticos se superponen. Sirven mejor como dos centros de gravedad que como dos cajas separadas."
thumbnail: /assets/img/agentic-ai-engineer-vs-architect-dos-centros-de-gravedad/thumb.jpg
---

Cuando se habla de roles en IA agéntica aparecen dos títulos: **Agentic AI Engineer** y **Agentic AI Architect**. Se los suele dibujar como dos cajas con una frontera nítida. En la práctica esa frontera no existe. Prefiero pensarlos como **dos centros de gravedad**: cada rol tiene un lugar hacia el que tira su atención, y hay una zona grande en el medio que comparten.

Esto es un marco de trabajo que uso para ordenar el curso, no una taxonomía de la industria ni un resultado medido.

## La diferencia de fondo: la pregunta que cada uno hace primero

- El **Engineer** pregunta: *¿cómo lo implemento y cómo hago que funcione de forma confiable?*
- El **Architect** pregunta: *¿debería existir así, y con qué límites?*

Las dos son necesarias. Cambia el orden en que se hacen y a qué le pone atención cada uno primero.

## Las cinco áreas del Engineer

1. **Frameworks y MCP.** Elegir y usar el framework de agentes, conectar herramientas por protocolo, resolver la integración concreta.
2. **Esquemas de herramientas.** Definir con precisión qué recibe y qué devuelve cada herramienta. Un esquema ambiguo produce llamadas ambiguas.
3. **Guardrails determinísticos y estado.** Controles en código que no dependen de que el modelo se porte bien, y manejo explícito del estado de la ejecución.
4. **Evals y operación de red teaming.** Armar los casos de prueba, correrlos y mantenerlos vivos.
5. **Optimización de ejecución y cómputo.** Latencia, paralelismo, costo por ejecución.

## Las cinco áreas del Architect

1. **Topología multiagente.** Cuántos agentes, quién delega en quién, dónde conviene un agente único y dónde no.
2. **Seguridad, gobernanza y límites de confianza.** Qué puede hacer cada componente, qué se audita, dónde termina la autonomía.
3. **Ingeniería de contexto y memoria.** Qué información ve el agente en cada paso y qué se conserva entre sesiones.
4. **Descomposición de procesos de negocio.** Qué parte de un proceso es para un agente, cuál para un flujo fijo y cuál para una persona.
5. **Ciclo de vida, infraestructura y FinOps.** Despliegue, versionado, observabilidad y control de costos a escala.

## Dónde se tocan: la zona gris compartida

Hay temas donde no tiene sentido discutir de quién son:

- selección de modelos,
- evaluación,
- red teaming,
- CI/CD,
- LLMOps y AgentOps.

Acá los dos roles trabajan sobre lo mismo desde ángulos distintos. El Architect define qué se evalúa y con qué criterio de aceptación. El Engineer construye y mantiene el arnés que lo evalúa. Si uno de los dos falta, la evaluación o no mide lo correcto o no corre.

## Comparación rápida

| | Engineer | Architect |
|---|---|---|
| **Pregunta** | ¿Cómo lo implemento? | ¿Debería existir así y con qué límites? |
| **Horizonte temporal** | Esta entrega, este sprint | Cómo envejece el sistema y qué cambia con él |
| **Artefacto típico** | Código, esquemas, pruebas, pipelines | Diagramas, decisiones de diseño, políticas, criterios |
| **Falla si...** | Funciona en la demo y se rompe con datos reales | Está bien pensado y nadie puede construirlo ni operarlo |

La última fila es la que más me interesa. Las dos fallas son simétricas: un sistema sin criterio de diseño y un diseño sin implementación viable cuestan igual de caro.

## Por qué «centros de gravedad» y no «cajas»

Un ejemplo concreto: la seguridad de una herramienta que escribe en un sistema externo. El Architect decide que esa escritura necesita un límite de confianza y una aprobación humana por encima de cierto monto. El Engineer decide cómo se implementa esa aprobación, dónde guarda el estado mientras espera y cómo se prueba que el límite no se puede saltear. Ninguna de las dos mitades sirve sola.

Por eso, para formación, no me sirve repartir los temas en dos listas cerradas. Me sirve que cada persona sepa hacia dónde tira su atención natural y que reconozca cuándo está entrando en el territorio del otro. Un Engineer que ignora el límite de confianza construye algo que funciona y es inseguro. Un Architect que ignora el costo de ejecución diseña algo elegante que no se puede pagar.

## Qué es opinión y qué no

- Las cinco más cinco áreas son mi agrupación de trabajo para ordenar contenidos, no un estándar de la industria.
- La zona gris compartida depende de cada organización: en equipos chicos, una sola persona cubre los dos centros.
- No hay datos medidos detrás de este marco. Es una herramienta para pensar el diseño de un programa de formación y de un equipo.

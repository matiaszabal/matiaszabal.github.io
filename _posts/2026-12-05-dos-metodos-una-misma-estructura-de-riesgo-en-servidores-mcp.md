---
layout: post
title: "Dos métodos, una misma estructura de riesgo en servidores MCP"
date: 2026-12-05 05:30:00 -0300
description: "Cuando una taxonomía derivada del lenguaje de políticas y otra derivada de auditar repositorios coinciden en el centro y divergen en los bordes."
thumbnail: /assets/img/dos-metodos-una-misma-estructura-de-riesgo-en-servidores-mcp/thumb.jpg
---

En mi trabajo sobre seguridad de MCP hay dos taxonomías de riesgo construidas **por métodos opuestos y de forma independiente**. Compararlas sirve más por lo que no coincide que por lo que coincide.

## Los dos métodos

- **Deductivo.** Una taxonomía de clases de vulnerabilidad derivada por reducción semántica sobre un lenguaje de políticas de autorización (Cedar): cada clase es una forma en que la semántica del lenguaje permite que una solicitud adversarial obtenga permiso. Su corpus es el lenguaje.
- **Inductivo.** Una taxonomía de tres capas más un eje ortogonal, derivada de la auditoría manual de **89 repositorios públicos de servidores MCP**, con cada hallazgo graduado por nivel de evidencia: lectura de código, ejecutado con el destino simulado, o prueba de concepto ejecutada completa. Su corpus es código desplegado.

Ninguna sirvió de insumo a la otra. Si dos métodos con supuestos y corpus distintos llegan a la misma estructura, eso es un argumento a favor de que la estructura sea real. Es **triangulación**, no una prueba.

## Dónde coinciden

| Taxonomía de políticas | Capa de la taxonomía empírica | Idea común |
|---|---|---|
| Exceso de alcance entre roles; abuso de delegación | Capa 1: exposición del plano de control | Una superficie de acción más amplia que la que el rol o la tarea justifican, por ejemplo mapear toda una API a herramientas sin reducir por mínimo privilegio |
| Falsificación de atributos; manipulación de roles; indirección por herramienta ejecutora | Capa 2: delegación de ejecución y confianza | La identidad y el alcance efectivos no están anclados en una fuente verificable externa a quien llama |

## Dónde divergen (lo más informativo)

- **Sobre-bloqueo.** El método deductivo necesita una clase para el exceso de restricción: sin ella, una política que deniega todo obtendría una robustez casi perfecta y la métrica premiaría la degeneración. La auditoría de repositorios solo mide sub-restricción, así que no tiene motivo para producir esa clase.
- **Señalización de riesgo.** La Capa 3 de la taxonomía empírica pregunta si el servidor **le avisa** al cliente cuán riesgosa es una herramienta, mediante las anotaciones nativas del protocolo, como `destructiveHint`. En los repositorios auditados esa señalización se usa de forma sistemática en una minoría, alrededor de 10 de 89. Un motor de políticas *decide*, no *señaliza*: no hay primitiva en el lenguaje para advertir sobre una acción que la política igualmente autorizará. Ninguna derivación sobre ese lenguaje podría generar esta clase.

## Un dato que sorprende

La arquitectura que la formalización presupone, con delegación que falla cerrada ante un punto de decisión externo, aparece en **1 de los 89 repositorios**. El modo de falla dominante en el SoK es otro: una decisión de autorización que nunca se tomó.

## Qué es opinión y qué no

- La coincidencia es de lectura cuidadosa mía entre mis propios dos trabajos. No es una validación externa.
- La convergencia se concentra en el centro y las divergencias en los bordes: esto acota la triangulación. No sostiene que ninguna de las dos taxonomías sea completa.
- El corpus del método deductivo es sintético; el del inductivo es de 89 repositorios y no es representativo de todo el ecosistema.
- Las cifras (89 repositorios, alrededor de 10 con señalización, 1 con delegación fail-closed) las tomo de mi tesis sin repetir el análisis para este post.

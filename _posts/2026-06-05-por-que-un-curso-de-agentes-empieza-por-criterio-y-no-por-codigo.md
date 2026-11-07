---
layout: post
title: "Por qué un curso de agentes debería empezar por criterio y no por código"
date: 2026-06-05 10:15:00 -0300
description: "Antes de escribir la primera herramienta hay preguntas de arquitectura que el código no responde: qué debería existir, con qué límites y a qué costo."
thumbnail: /assets/img/por-que-un-curso-de-agentes-empieza-por-criterio-y-no-por-codigo/thumb.jpg
---

Cuando armo un curso sobre sistemas agénticos, la tentación es empezar por lo que más se ve: un agente que llama a una herramienta y devuelve una respuesta. Es lo que mejor luce en una demo. Yo lo hago al revés, y este post explica por qué.

La idea de fondo es que dos preguntas se parecen y no son la misma:

- **«¿Cómo lo implemento?»** es la pregunta de quien construye el agente.
- **«¿Debería existir así, y con qué límites?»** es la pregunta de quien diseña el sistema.

La segunda no se puede responder bien sin haber invertido tiempo en perspectiva estratégica, en el estado del arte y en criterio de evaluación. Por eso ese es el contenido del principio. Esto es un argumento de diseño de curso, no un resultado medido.

## 1. Hay que dimensionar el cambio antes de construir dentro de él

Un sistema donde el agente decide, actúa y a veces delega en otros agentes no es infraestructura que simplemente llama a un modelo. Es un salto comparable al de los monolitos a los microservicios, o al de los datacenters propios a la nube.

Mi lectura es que en esos dos saltos las organizaciones que primero escribieron código y recién después se preguntaron qué implicaba a nivel de arquitectura, seguridad y costo, pagaron ese orden con reescrituras caras. Con los agentes la pregunta de dimensionamiento es: **¿qué cambia cuando el componente que orquesta un proceso de negocio ya no es determinista?** Va antes de cualquier decisión de implementación: topología, límites de confianza, dónde vive la autonomía y dónde no.

Eso no se resuelve con una slide. Hace falta un mapa mental completo de qué componentes forman un sistema agéntico real (modelo, herramientas, memoria, orquestación, evaluación y gobernanza) antes de profundizar en cualquiera. Quien ve un `ParallelAgent` sin ese mapa aprende una sintaxis. Quien ya lo tiene entiende por qué ese patrón existe y cuándo conviene elegirlo sobre otro.

## 2. El estado del arte se mueve más rápido que las políticas

Una política de arquitectura como «qué modelos están aprobados» o «qué nivel de autonomía se permite por caso de uso» se firma sobre una foto. Si esa foto tiene seis meses, la política nace desactualizada. Cambian las capacidades, cambia el costo por token y cambia lo que se considera seguro por defecto, a una cadencia que ninguna otra capa de infraestructura tuvo antes.

Seguir el estado del arte no es curiosidad. Es lo que mantiene vigente una política de selección de modelos más de un trimestre.

Incluye mirar el costado incómodo: laboratorios que admiten exceso de agencia en sus propios lanzamientos, y casos documentados donde un sistema agéntico cruzó un límite que su propia traza de razonamiento muestra que había identificado. Esa evidencia es el insumo para definir la gobernanza y los límites de seguridad antes de que alguien escriba el primer control sobre una herramienta. Sin haber visto cómo falla un sistema real, la política que se escribe después es genérica y no informada.

## 3. Un benchmark se lee con escepticismo metodológico

Tomar el puntaje de un laboratorio como una medición objetiva es un error de criterio caro. Hay *benchmark gaming* medido por evaluadores independientes, contaminación de los datos de entrenamiento con los propios sets de evaluación, y una brecha bien documentada entre un puntaje en un leaderboard y el comportamiento confiable en una tarea de negocio.

Por eso la lectura de un benchmark no se puede delegar en quien lo va a consumir en producción. Decidir qué modelos están aprobados por nivel de riesgo depende de saber qué mide un benchmark, qué no mide y qué tan reproducible es. Eso se enseña y se practica. No se asume.

## 4. Las capacidades avanzan más rápido que lo que debería contenerlas

La asimetría que más importa tener clara antes de diseñar: **las capacidades agénticas avanzan más rápido que la seguridad, la gobernanza, la práctica de puesta en producción y la medición del retorno que deberían contenerlas.**

Un modelo con más autonomía para usar herramientas puede salir en semanas. Un marco de gobernanza maduro, con límites de confianza definidos y auditoría de trazabilidad, tarda años. Esa brecha no se cierra sola, y es el espacio de trabajo de quien diseña el sistema.

Con el retorno conviene ser explícito: «funciona» y «tiene sentido de negocio» son preguntas distintas. Un agente puede resolver una tarea y aun así no justificar su costo en tokens, en latencia o en el riesgo que introduce. Calcular ese retorno con criterio, y no con el entusiasmo de que funcionó en la demo, es una competencia estratégica que va antes de cualquier línea de código.

## 5. Por qué antes y no en paralelo

Se puede argumentar que estos temas pueden ir intercalados mientras se aprende a implementar. Mi respuesta es que la segunda pregunta, cuando se responde tarde, **no corrige el diseño, lo parchea**. Un sistema multiagente diseñado primero e interrogado después sobre sus límites de confianza termina con controles pegados por afuera y no integrados en la arquitectura.

Instalar primero la perspectiva estratégica permite que, cuando llega el momento de construir, cada decisión (qué modelo, qué patrón de orquestación, qué nivel de autonomía) ya se tome con el criterio correcto y no haya que revisarla después.

Esa es la apuesta: dos bloques de inversión en criterio no compiten con la profundidad técnica que viene después. Son la condición para que esa profundidad se construya sobre una arquitectura bien pensada desde el principio.

## Qué es opinión y qué no

- Todo lo anterior es un argumento de diseño pedagógico, sin datos propios medidos.
- La comparación con los saltos históricos (monolitos a microservicios, datacenters a nube) es una analogía, no una estadística.
- Las referencias a *benchmark gaming*, contaminación de datos y exceso de agencia en lanzamientos son hechos que conviene verificar caso por caso, con la fuente primaria, antes de citarlos.

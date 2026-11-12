---
layout: post
title: "La brecha de atestación: lo que un lenguaje de políticas no puede cerrar"
date: 2026-12-06 05:30:00 -0300
description: "Por qué una parte del riesgo de autorización no se arregla escribiendo mejores políticas sino verificando de dónde vienen los atributos sobre los que la política razona."
thumbnail: /assets/img/la-brecha-de-atestacion-lo-que-un-lenguaje-de-politicas-no-puede-cerrar/thumb.jpg
---

Una política de autorización decide a partir de **atributos**: quién es el solicitante, qué rol dice tener, a qué recurso apunta. La política puede ser impecable y aun así fallar, si nadie verifica que esos atributos sean verdaderos. A esa parte del riesgo la llamé **brecha de atestación**.

## La idea

En mi investigación medí la robustez de políticas Cedar con una métrica determinista, R(π), cuyo oráculo es el motor oficial de Cedar. Endurecí una política en tres versiones: de una base que solo permitía, a una con prohibiciones estructurales, a una versión final. La robustez subió de forma monótona, hasta 1,0 sobre mi conjunto de pruebas.

El resultado más interesante es otro: con **solo reglas estructurales** de prohibición hay un techo. Una fracción del peso total del riesgo no se puede cerrar con reglas del lenguaje, porque requiere que el punto que aplica la política (el PEP) **atestigüe** los atributos de contexto mediante infraestructura de identidad externa. Por ejemplo: la política puede decir «solo el rol administrador», pero si el llamador declara su propio rol, la política no tiene cómo desmentirlo.

## Cuánto es el techo

Aquí tengo que ser cuidadoso. Mis documentos dan cifras distintas según la versión de la taxonomía: **44,4 %** de robustez máxima estructural (55,6 % del peso requiere atestación) en el README del repositorio, y **50 %** del peso (tres vectores de un total de veinte puntos de peso) en la tesis. No verifiqué cuál es la vigente, así que cito el orden de magnitud —alrededor de la mitad— y no un número exacto.

## Por qué importa para agentes

Un agente que llama herramientas por MCP actúa con credenciales y roles que alguien le asignó. Si el servidor confía en lo que el agente declara, endurecer la política no alcanza. La enseñanza de diseño es que **el endurecimiento no puede detenerse en el texto de la política**: debe extenderse a la infraestructura que provee los atributos.

Es la manifestación práctica de la frontera entre los supuestos de mundo abierto y mundo cerrado: la política asume que lo que no está en el contexto es falso, y eso solo es seguro si el contexto lo provee alguien confiable.

## Qué es opinión y qué no

- Los resultados provienen de un **corpus sintético** de siete u ocho clases de vulnerabilidad y de políticas Cedar de laboratorio. No muestran qué proporción del riesgo real se explica así.
- El techo depende de cómo definí y ponderé las clases de vulnerabilidad: es una consecuencia de mi taxonomía, no una constante.
- Que la brecha sea una propiedad de todo sistema de control de acceso basado en atributos, y no solo de Cedar, es mi interpretación.
- El valor 1,0 alcanzado indica convergencia sobre mi conjunto de pruebas, no ausencia de fallas.

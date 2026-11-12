---
layout: post
title: "¿Con qué frecuencia aparece el fail-open de Cedar en repositorios reales?"
date: 2026-12-08 05:30:00 -0300
description: "Una auditoría de 78 repositorios para estimar cuánto se repite un patrón de políticas que falla abierto, y por qué corregí mis propias cifras a la baja."
thumbnail: /assets/img/con-que-frecuencia-aparece-el-fail-open-de-cedar-en-repositorios-reales/thumb.jpg
---

Encontré un patrón en políticas Cedar que **falla abierto**: una condición con el operador `in` sobre un valor de texto produce un error de tipos, la prohibición se descarta y un permiso condicional dispara. Después de verlo en dos políticas, la pregunta natural fue: ¿qué tan común es? No nombro los repositorios que lo tienen.

## El método

Una auditoría estratificada por repositorio: 78 repositorios únicos, elegidos con una búsqueda de código sobre el patrón, un archivo aleatorio por repositorio (semilla fija) y excluyendo los dos de la muestra original.

## El conteo crudo

- **14 de 78 repositorios (17,9 %)** con el patrón, con un intervalo de confianza de Wilson del 95 % de 11,0 % a 27,9 %.
- **7 de 78 (9,0 %)** con, además, un permiso incondicionado, es decir, sintácticamente fail-open.

## La corrección

El conteo por expresión regular **no es el resultado**. Revisé archivo por archivo y esa revisión corrigió ambas cifras **a la baja**. De los siete casos que parecían fail-open, tres eran adopciones reales y verificadas de un mismo plugin de gobernanza, y otro era una defensa real y no una falla. No tengo a mano la cifra final corregida y la tesis la desarrolla con más detalle, así que no la reproduzco aquí.

En una confirmación dinámica extendida, cinco repositorios independientes habían instalado esa política a través de los canales de distribución de un asistente de código y devolvían «permitido» ante entradas adversariales, todo comprobado con la misma versión del motor.

## Dos lecciones

1. **Una regex no es una medición.** Un conteo automático sobreestima: hay que leer los casos.
2. **El riesgo se hereda por copia.** Que varios repositorios independientes tengan la misma falla se explica por un artefacto compartido que se distribuyó, no por errores independientes.

## Qué es opinión y qué no

- El patrón se confirmó con una versión del motor y en dos enlaces independientes del mismo; no verifiqué todas las versiones.
- La muestra sale de una búsqueda de código concreta y **no es representativa** de todo el uso de Cedar. El 17,9 % no es una tasa general.
- No sé si los autores de los repositorios afectados fueron notificados.
- Las cifras de este post vienen de mi tesis; no repetí la auditoría para escribirlo.

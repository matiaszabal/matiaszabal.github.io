---
layout: post
title: "Cuando la capa de enforcement falla abierta: dos bugs y cero enforcement"
date: 2026-12-07 05:30:00 -0300
description: "Un caso donde la política era correcta pero la capa que debía aplicarla permitía todo, y qué enseña sobre diseñar para que un error signifique denegar."
thumbnail: /assets/img/cuando-la-capa-de-enforcement-falla-abierta-dos-bugs-y-cero-enforcement/thumb.jpg
---

Escribir una buena política no sirve si la capa que la aplica permite todo cuando algo sale mal. Analicé un caso real de esa clase en un paquete que aplica políticas Cedar antes de que un asistente de código ejecute una herramienta. **No nombro el paquete ni el plugin que lo usa**, porque no confirmé que se haya avisado a sus autores. Lo importante es el patrón.

## Qué encontré

Al leer el código fuente de esa capa de enforcement aparecieron dos errores de integración independientes, que hacen que falle **abierta**, sin importar la política:

1. **Formato de la llamada incorrecto.** La capa pasa la política como texto plano a una función que, en la versión usada del motor, espera un objeto con una estructura. La llamada lanza una excepción, y el bloque que captura el error devuelve «permitido». Falla abierta **por excepción**.
2. **Formato de la respuesta mal interpretado.** La capa espera un resultado cuyo tipo sea «allow» o «deny», pero el motor devuelve otro envoltorio. El resultado no coincide con ninguno de los dos casos y cae en la rama por defecto, que también devuelve «permitido». Falla abierta **por retorno por defecto**.

Además, el comando de evaluación que el plugin invoca no existe en la versión del paquete que fijaba. Conclusión de mi análisis: esa capa produce cero enforcement de Cedar, independientemente de la política.

## El patrón de diseño

En los dos errores, **ante algo inesperado, el sistema autoriza**. La regla opuesta es sencilla de enunciar: en un punto de control, cualquier excepción, respuesta no reconocida o resultado ambiguo debe significar «denegar». Y conviene una prueba que lo compruebe, con una política que **debe** denegar y un control que confirme que el motor puede devolver «deny».

## Qué no sé

- Verifiqué el comportamiento con un script y con la lectura del código de esa versión. No sé si versiones posteriores lo corrigieron.
- No evalué cuántos usuarios dependían de esa capa en producción.

## Qué es opinión y qué no

- El análisis se hizo con una versión concreta; no es una afirmación sobre el estado actual del proyecto.
- Que el principio «ante la duda, denegar» sea lo correcto es un criterio de diseño de seguridad ampliamente aceptado, pero en algunos contextos de disponibilidad hay compromisos que habría que discutir.
- No reproduzco los detalles que permitan explotar el caso.

---
layout: post
title: "Ataques adversariales de evasión: FGSM, PGD, GCG y el espacio discreto de tokens"
date: 2026-11-19 05:30:00 -0300
description: "Cómo se usa la misma maquinaria que entrena un modelo para engañarlo en producción, y por qué el texto complica la técnica que nació en imágenes."
thumbnail: /assets/img/ataques-adversariales-de-evasion-fgsm-pgd-gcg-y-el-espacio-de-tokens/thumb.jpg
---

Un ataque de evasión no entrena nada y no toca un solo peso del modelo. Asume que el modelo ya está entrenado y en producción, congela sus pesos y usa la misma maquinaria de *backpropagation* que sirvió para entrenarlo, pero apuntada al revés. En vez de preguntar «¿cómo ajusto los pesos para acertar más?», pregunta **«¿cómo cambio la entrada para que el modelo se equivoque como yo quiero, sin que un humano note el cambio?»**

Este post explica el mecanismo para entender la amenaza y defenderse. Es un panorama conceptual, no una guía operativa.

## La formalización mínima

Si una función f asigna a una entrada x la salida correcta y, el atacante busca una perturbación mínima δ tal que:

- **Evasión no dirigida:** f(x + δ) ≠ y. Cualquier salida incorrecta sirve.
- **Evasión dirigida:** f(x + δ) = y objetivo. El atacante elige la salida que quiere forzar.

La perturbación está acotada por un presupuesto ε que garantiza que x + δ siga pareciendo, a un humano, igual o equivalente a x. Ese presupuesto es la variable de diseño central: cuanto más chico, más imperceptible; cuanto más grande, más fácil evadir pero más riesgo de que alguien note algo raro.

## Según lo que sabe el atacante

### White-box: tiene los planos

Con acceso a pesos, arquitectura y gradientes (realista con modelos de pesos abiertos que se pueden correr localmente), puede calcular la perturbación óptima:

- **FGSM** (*Fast Gradient Sign Method*; Goodfellow y colaboradores, 2014): un solo paso en la dirección del signo del gradiente de la pérdida **respecto de la entrada**, no de los pesos. Es rápido, pero produce perturbaciones más gruesas y más fáciles de filtrar.
- **PGD** (*Projected Gradient Descent*): la versión iterativa. Da varios pasos chicos y, después de cada uno, proyecta la entrada de vuelta al radio ε. Es más costoso y más robusto: es el estándar de hecho para evaluar robustez adversarial en la literatura.
- **C&W** (Carlini y Wagner): en vez de fijar ε de antemano, busca directamente la perturbación de norma mínima con alta tasa de éxito. Se suele usar como ataque de referencia para romper una defensa que se declara robusta.

### Black-box: solo ve entradas y salidas

Es el caso realista contra la mayoría de las APIs comerciales de LLMs:

- **Basados en consultas:** estimar el gradiente con diferencias finitas, consultando el modelo con variaciones chicas de la entrada.
- **Transferibilidad:** entrenar un modelo sustituto con las salidas del objetivo, construir el ejemplo adversarial en white-box contra el sustituto y transferirlo. Funciona porque las perturbaciones tienden a transferir, con éxito parcial, entre modelos de arquitectura o entrenamiento parecidos. Es un hecho empírico, no una garantía.

## El problema específico del texto: el espacio es discreto

La técnica nació en visión por computadora (el ejemplo clásico es una señal de Stop con ruido imperceptible, clasificada como límite de velocidad). En texto aparece una restricción que no existe en imágenes: **no se puede «sumar δ» a la entrada**, porque no existe un token «entre» dos tokens del vocabulario.

**GCG** (*Greedy Coordinate Gradient*) es la respuesta a esa restricción. Usa el gradiente del modelo para guiar una **búsqueda discreta**: en cada paso evalúa qué sustitución de un token en un sufijo del prompt reduce más la pérdida hacia la respuesta buscada, y avanza de forma voraz. El resultado suele ser un sufijo de aspecto arbitrario, a menudo sin sentido para un humano, que hace que el modelo cumpla algo que sus políticas deberían rechazar.

GCG es un caso de frontera entre dos categorías. Por *método* es un ataque adversarial puro (optimización guiada por gradiente sobre la geometría de la función, no manipulación semántica). Por *objetivo* es un jailbreak (saltear el alineamiento). La distinción entre categorías es por mecanismo y objetivo, y no garantiza que cada ataque real caiga limpio en una sola casilla.

También existen manifestaciones de texto que no necesitan gradiente:

- **Caracteres Unicode invisibles o de ancho cero** entre los tokens de una palabra prohibida: rompen la tokenización que espera un filtro sin cambiar lo que lee una persona.
- **Homoglifos**: caracteres visualmente idénticos de otro alfabeto (una «a» cirílica por una latina). El ojo no distingue la diferencia, pero un filtro por coincidencia de texto sí.

## Mitigaciones y su límite

| Estrategia | Cómo funciona | Límite |
|---|---|---|
| **Entrenamiento adversarial** | Reentrenar con ejemplos adversariales bien etiquetados | Efectivo pero costoso; solo cubre las perturbaciones representadas, no un método nuevo |
| **Sanitización y *denoising* de entradas** | Normalizar Unicode, detectar sufijos de baja probabilidad | Es otro clasificador más, atacable con suficiente iteración |
| **Ocultar el gradiente** | Dificultar el cálculo al atacante white-box (por ejemplo, ocultar logits) | No da seguridad completa: la transferibilidad sigue funcionando |
| **Robustez certificada** | Métodos como *randomized smoothing*, que garantizan formalmente que la predicción no cambia dentro de un radio ε | Única con garantía matemática, pero cara y poco adoptada hoy en LLMs de producción a escala |

El patrón que se repite: casi todas las defensas son, en el fondo, otro clasificador con el mismo problema de fondo.

## Cómo se distingue de otras amenazas

- **Envenenamiento (*poisoning*)** corrompe el modelo durante el entrenamiento. La evasión actúa solo en inferencia, sin tocar pesos.
- **Inversión de modelo** busca reconstruir información memorizada del corpus de entrenamiento. La evasión busca forzar una salida concreta manipulando la entrada, sin importar qué memorizó el modelo.

## Preguntas para pensar

- GCG produce sufijos que un humano lee como texto sin sentido. Si un sistema filtrara cualquier entrada de baja probabilidad lingüística, ¿cerraría esa vía? ¿Qué le pasaría al mismo filtro frente a jailbreaks semánticos clásicos, como el juego de roles?
- ¿Por qué la robustez certificada escapa a la crítica de «otro clasificador más», y por qué no es todavía el estándar en producción?

## Qué es opinión y qué no

- Resumo un documento de estudio del curso, que sigue el catálogo de amenazas MAESTRO. No volví a leer los papers originales de FGSM, PGD, C&W ni GCG para este post. Conviene citarlos desde la fuente primaria antes de reutilizar los detalles.
- Omití a propósito los detalles operativos de construcción de ataques. El objetivo es entender la amenaza para diseñar defensas.
- La afirmación de que la transferibilidad funciona «con éxito parcial» es un hecho empírico observado, sin garantía formal.
- Que la robustez certificada esté poco adoptada en LLMs de producción es mi lectura del estado de la práctica, y puede haber cambiado.

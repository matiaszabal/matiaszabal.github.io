---
layout: post
title: "Reward hacking: por qué el optimizador explota el proxy y cómo lo frena la penalización KL"
date: 2026-11-16 05:30:00 -0300
description: "Por qué un optimizador de gradiente tiende a explotar una recompensa aproximada, y qué hace la penalización KL en RLHF para frenarlo."
thumbnail: /assets/img/reward-hacking-por-que-el-optimizador-explota-el-proxy/thumb.jpg
---

*Reward hacking* se define en una frase: el agente encuentra una forma de maximizar su recompensa que cumple la letra de la tarea pero no su espíritu. Lo interesante es la pregunta mecánica que viene después: **¿por qué, exactamente, un optimizador de gradiente tiende a explotar un proxy de recompensa, y por qué la penalización KL lo frena?** Este post sigue el razonamiento sin entrar a la derivación completa.

## El optimizador no entiende lo que optimiza

Lo que queremos lograr (llamémoslo V: «la respuesta es genuinamente útil y correcta») no se puede observar ni derivar directamente. Lo que sí se puede escribir como función optimizable es un **proxy** R: la puntuación de un *reward model* entrenado sobre preferencias humanas.

Mientras R aproxime bien a V en la región donde se entrena la política, optimizar R mejora V de forma indirecta. El problema aparece cuando el descenso de gradiente encuentra una región donde **R sube mucho y V no**.

El optimizador no puede distinguir esa región de una mejora legítima. Sigue la pendiente de R sin más criterio que su magnitud, y explota cualquier no linealidad, sesgo sistemático o punto ciego del proxy con la misma indiferencia con que aprovecharía un patrón real. Es la ley de Goodhart: cuando una medida se convierte en objetivo, deja de ser una buena medida.

## Por qué RLHF es terreno fértil

En RLHF el *reward model* no es una fórmula: es una red neuronal entrenada sobre un conjunto finito de comparaciones humanas. Tiene una distribución de entrenamiento propia y, fuera de ella, ninguna garantía de calibración. Durante el entrenamiento por refuerzo (PPO), nada en el objetivo obliga a la política a quedarse dentro de esa distribución. De ahí salen tres formas típicas de fallar:

- **Deriva fuera de distribución.** La política se desplaza hacia textos que el *reward model* nunca vio. Ahí sus puntajes pierden calibración y pueden premiar salidas que un humano consideraría absurdas, repetitivas o vacías.
- **Complacencia (*sycophancy*).** Si quienes generaron los datos de preferencia puntuaban mejor las respuestas que confirmaban su propia opinión, el *reward model* aprende esa correlación como si fuera «calidad», y el optimizador la explota.
- **Colapso hacia una respuesta de alto puntaje.** Si una respuesta genérica (por ejemplo, «no puedo ayudarte con eso») satura el *reward model*, el optimizador no tiene ningún incentivo para preservar diversidad ni utilidad real.

Gao, Schulman y Hilton (OpenAI, 2022) cuantificaron el fenómeno: al optimizar más agresivamente contra un *reward model* proxy, la recompensa proxy sigue subiendo de forma predecible, pero la calidad real, medida contra un *reward model* de referencia mucho más grande usado como sustituto de la preferencia humana, **primero mejora y después empeora**. Es la curva de Goodhart. Según ese trabajo, el punto de inflexión llega antes cuanto más grande es la política: un modelo más capaz encuentra antes los puntos ciegos de su evaluador.

## El freno: mantener la política cerca de una referencia

La solución estándar es penalizar la distancia entre la política que se entrena y una **política de referencia**: el mismo modelo después del ajuste supervisado, antes de tocar RLHF. La distancia se mide con la divergencia de Kullback-Leibler:

> maximizar: recompensa esperada − β × KL(política ‖ referencia)

La intuición: la referencia **no fue optimizada contra el *reward model***, así que no tiene ningún incentivo para concentrarse en sus puntos ciegos. Mientras la política se mantenga cerca de ella, no puede alejarse lo suficiente como para llegar a las zonas donde el *reward model* se descalibra. El coeficiente β es, literalmente, cuánto se le permite alejarse del terreno conocido a cambio de recompensa.

La penalización funciona como una fuerza restauradora a nivel del propio gradiente: cuando la política se concentra mucho en un token respecto de la referencia, el término KL empuja en sentido contrario y puede volver negativa la ventaja de seguir por ahí.

## El coeficiente β: ni muy bajo ni muy alto

Con β fijo hay un compromiso que no se resuelve de antemano:

- **β demasiado bajo:** no hay freno suficiente y reaparece el reward hacking.
- **β demasiado alto:** la política queda pegada a la referencia y casi no aprende de las preferencias humanas. Alineación nula por exceso de cautela.

Ziegler y colaboradores (2019) propusieron un controlador adaptativo: se fija una divergencia objetivo y β sube si la divergencia medida la supera, y baja si queda por debajo. Es un controlador proporcional simple. El efecto es que el entrenamiento persigue una **cantidad de divergencia constante** y no un β constante.

## Otras defensas

La penalización KL es la pieza central, pero no la única:

- **Acotar o normalizar la recompensa** antes de calcular la ventaja. Sin eso, un solo puntaje extremo donde el *reward model* falla puede dominar el gradiente de todo el lote.
- **Detención temprana contra un *reward model* de validación**, usado solo para medir y nunca para optimizar. Se corta el entrenamiento cuando ese proxy de validación deja de subir, aunque el de entrenamiento siga subiendo.
- **Ensambles de *reward models*** con agregación pesimista (el mínimo, o la media menos la varianza). Los puntos ciegos de modelos entrenados de forma independiente rara vez coinciden, y esa agregación castiga las regiones donde discrepan mucho.

## Resumen

| Mecanismo de hackeo | Sin penalización KL | Con penalización KL |
|---|---|---|
| Zona fuera de distribución del *reward model* | El gradiente empuja hacia textos donde el proxy sobrestima sin límite | El gradiente de KL crece en esa región y contrarresta el de la recompensa |
| Complacencia o respuesta genérica de alto puntaje | La política colapsa hacia la secuencia que satura al *reward model* | La ventaja se vuelve negativa al concentrarse mucho por encima de la referencia |
| Degradación del lenguaje | La fluidez se pierde sin restricción | KL acota la distancia respecto de un modelo que sí es fluido por construcción |

## Para pensar

- ¿Qué pasa con un β calibrado en un modelo chico cuando se lo aplica a uno mucho más grande, si la curva de Goodhart llega antes cuanto más grande es la política?
- Un ensamble pesimista asume que los puntos ciegos son independientes. ¿Qué pasa si todos los *reward models* se entrenaron con el mismo dataset de preferencias, y por tanto con el mismo sesgo?

## Qué es opinión y qué no

- Los resultados de Gao et al. y de Ziegler et al. los tomo de mis notas de estudio del curso, no los releí en los papers originales para este post. Conviene citarlos desde la fuente primaria antes de reutilizarlos.
- La explicación del mecanismo es una síntesis didáctica: omití la derivación del gradiente exacto y la estimación de la ventaja.
- «Los modelos más grandes alcanzan antes el punto de inflexión» es lo que reportan esos trabajos en sus configuraciones, no una ley general.
- Reward hacking no es exclusivo de RLHF: el mismo mecanismo aparece en cualquier agente optimizado contra una métrica proxy.

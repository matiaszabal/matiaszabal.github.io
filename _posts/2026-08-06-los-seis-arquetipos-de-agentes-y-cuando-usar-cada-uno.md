---
layout: post
title: "Los seis arquetipos de agentes y cuándo usar cada uno"
date: 2026-08-06 10:05:00 -0300
description: "Reflex, ReAct, Planner-Executor, Query Decomposition, Reflection y Deep Research, comparados con las mismas tres preguntas y un árbol para elegir."
thumbnail: /assets/img/los-seis-arquetipos-de-agentes-y-cuando-usar-cada-uno/thumb.jpg
---

Cuando alguien dice «necesitamos un agente», casi nunca queda claro qué necesita. Yo organizo el trabajo con seis arquetipos y tres preguntas. Los nombres son una abreviatura de las respuestas a esas preguntas.

## Las tres preguntas

Orquestar un agente es decidir tres cosas:

1. **¿Qué se ejecuta después?** Es el control de ejecución. En un extremo el código fija la secuencia y el modelo completa huecos. En el otro, el modelo decide en cada vuelta qué herramienta llamar y si ya terminó.
2. **¿Con qué contexto?** Un paso puede ver todo lo anterior, un artefacto explícito como un plan, un resumen o solo su propia entrada. Esto determina cuánto cuesta cada llamada y cuánto ruido se acumula.
3. **¿Cuándo se detiene?** La señal de cierre puede ser una afirmación del modelo, una verificación determinista o un presupuesto agotado. Tienen confiabilidad muy distinta.

## Un espectro de control

Si se ordenan los seis según quién decide el flujo, aparece un espectro. Es un ordenamiento didáctico, no una medición.

- **Reflex**: el flujo está resuelto en el diseño.
- **Planner-Executor** y **Query Decomposition**: el modelo decide una vez (el plan o la partición) y después el código ejecuta.
- **Reflection**: el código fija el lazo generar, evaluar, corregir; el modelo decide el veredicto y la corrección.
- **ReAct** y **Deep Research**: el modelo decide todo el tiempo, y en Deep Research también cuántas rondas y qué investigar.

Moverse hacia la derecha compra adaptabilidad y cuesta previsibilidad, latencia y dinero. La regla práctica: empezar por la izquierda y moverse solo cuando la tarea lo exija.

## Los seis, uno por uno

### 1. Reflex

Percepción, decisión, acción, en una sola pasada. Conviene con volumen alto, ambigüedad baja y acciones baratas o reversibles. Su lugar natural es el primer nivel: un router que resuelve lo fácil y deja pasar lo difícil.

**Fallas típicas:** clasificación errónea silenciosa (nadie revisa), un mensaje con dos pedidos que se reduce a uno, reglas que envejecen y deriva de alcance cuando se le agrega memoria o consultas sin decidirlo.

**Se descarta** si hay que buscar datos, si hay varios pasos o si un error es caro y nadie lo detecta.

### 2. ReAct

Razonar, actuar, observar, repetir. Conviene cuando no se conoce el camino y cada paso depende del anterior. Es tan flexible que se vuelve la opción por defecto, y de ahí vienen sus riesgos.

**Fallas típicas:** loops (repite la acción porque su contexto no le dice que ya falló), deriva del objetivo, observaciones enormes que ahogan el contexto, herramientas mal descritas y composición de errores (un primer paso malo condiciona todo lo siguiente).

**Se descarta** si el camino se conoce (un plan es más barato y auditable), si hay que aprobar pasos antes de ejecutarlos o si la reproducibilidad es un requisito duro.

### 3. Planner-Executor

Planificar primero, ejecutar después. El plan es un artefacto explícito: se puede revisar antes de que pase nada. Conviene si el camino es largo y conocido, si hay pasos irreversibles (enviar un correo, modificar una base) o si un tercero, como compliance, necesita aprobar antes.

**Fallas típicas:** rigidez (se ejecuta bien un plan equivocado), planes que asumen datos que recién aparecen en un paso posterior, dependencias mal declaradas y replanificación sin tope.

**Se descarta** en tareas exploratorias y en tareas de dos o tres pasos, donde planificar cuesta más que hacer.

### 4. Query Decomposition

Partir la pregunta, resolver las partes, sintetizar. Se parece a Planner-Executor, pero las partes son preguntas de información y no acciones sobre el mundo. Conviene con preguntas multi-salto o comparativas, sobre todo en sistemas de recuperación.

**Fallas típicas:** una descomposición que omite un salto necesario, sub-preguntas que se superponen, propagación de errores en la variante secuencial y una respuesta inventada para una sub-pregunta sin evidencia que la síntesis mezcla con las correctas.

**Se descarta** si una sola fuente alcanza o si las sub-preguntas no se pueden anticipar antes de buscar.

### 5. Reflection

Generar, criticar, corregir. Acá importa un resultado de la literatura: Huang y colaboradores mostraron en 2023 que los modelos tienen dificultades para autocorregir su razonamiento sin feedback externo, y que a veces empeoran. Un lazo de reflexión sin señal externa es una apuesta. Con evidencia real (pruebas que pasan o fallan, reglas que se cumplen, citas que se pueden contrastar) es una herramienta sólida.

**Fallas típicas:** el crítico complaciente, el crítico excesivo que degrada un borrador bueno, la oscilación (corregir un problema reintroduce otro) y rúbricas vagas que producen críticas vagas.

**Se justifica** cuando un error cuesta más que las rondas extra y existe algo verificable. Una optimización habitual es usar un modelo más chico como crítico.

### 6. Deep Research

Rondas de investigación hasta cubrir el tema. Sirve para preguntas abiertas cuyo resultado es un informe que alguien va a leer y cuyo valor justifica el costo, como una debida diligencia o una revisión de literatura.

**Fallas típicas:** caro, lento y no determinista; cobertura ilusoria si el evaluador se conforma antes de tiempo; fuentes de baja calidad mezcladas sin que se note; y citas que no respaldan lo afirmado. Por eso conviene verificar los informes por muestreo.

**Advertencia:** es el arquetipo que más se elige de más. Antes de justificarlo, probar con uno más simple.

## Los arquetipos rara vez aparecen solos

Hay dos formas de combinarlos:

- **Escalamiento.** Un Reflex como router de primer nivel resuelve lo conocido. Lo ambiguo pasa a un ReAct. Si la acción resultante tiene riesgo alto, pasa por un lazo de Reflection antes de ejecutarse. Cada nivel filtra lo que el siguiente no necesita ver.
- **Anidamiento.** Deep Research se puede leer como una composición: un plan al estilo Planner-Executor, sub-preguntas en paralelo como en Query Decomposition, investigadores que funcionan como ReAct y una crítica de cobertura que es una Reflection sobre la pregunta «¿qué falta?».

La consecuencia de diseño: ante un sistema complejo, descomponerlo en estos bloques y responder para cada uno quién decide, con qué contexto y cuándo se detiene.

## Cómo elegir: cinco preguntas, de lo simple a lo complejo

1. ¿Alcanza una sola pasada de percepción a acción? **Reflex.**
2. ¿Es un problema de información que se parte en sub-preguntas conocidas de antemano? **Query Decomposition.**
3. ¿Se conocen los pasos y conviene aprobarlos antes de ejecutar? **Planner-Executor.**
4. Si ninguna aplica: ¿es una pregunta abierta que justifica un costo y una latencia muy altos? **Deep Research.** Si no, **ReAct.**
5. Transversal: ¿un error es costoso y hay un criterio verificable? Agregar **Reflection** sobre el arquetipo elegido.

El orden importa: se empieza por lo más simple y se sube solo cuando hace falta.

## Qué es opinión y qué no

- El espectro de control es un ordenamiento didáctico, no una medición: una implementación concreta puede correrse hacia cualquier lado.
- Las categorías no son una taxonomía cerrada ni excluyente. Son herramientas para decidir y para comunicarse con un equipo.
- Las fallas listadas son las que se observan con más frecuencia al diseñar estos sistemas, sin un estudio propio detrás. La excepción es la autocorrección sin feedback externo, que tiene respaldo en la literatura citada.
- Todo control en manos del modelo debería llevar un tope impuesto desde afuera (rondas, pasos, presupuesto).

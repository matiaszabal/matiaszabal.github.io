---
layout: post
title: "Aprender sin tocar pesos: few-shot dinámico, ExpeL y Reflexion"
date: 2026-09-25 10:10:00 -0300
description: "Tres formas de que un agente mejore con la experiencia sin reentrenar el modelo: recuperar ejemplos, guardar lecciones o destilar reglas."
thumbnail: /assets/img/aprender-sin-tocar-pesos-few-shot-dinamico-expel-y-reflexion/thumb.jpg
---

Un agente puede mejorar con la experiencia sin que nadie reentrene el modelo. Lo que cambia no son los pesos: cambia **lo que se le da al modelo** en cada turno. Hay tres técnicas no paramétricas que enseño en el curso y que se distinguen por una sola cosa: **cuánto se transforma la experiencia antes de guardarla**.

> **Few-shot dinámico recupera ejemplos, Reflexion recupera lecciones, ExpeL recupera reglas.**

## No son componentes nuevos, son políticas

Si se mira la arquitectura de memoria de un agente (camino de escritura, camino de lectura y un sustrato gobernado), estas técnicas no agregan cajas. Son políticas sobre los mismos caminos: cambian *qué entra* al paso de extracción, *cuándo* corre y *en qué forma* se guarda lo que sale. Este mapeo es lectura mía, no figura en la presentación de origen.

| Técnica | Qué se guarda | Cuándo se escribe | Qué tipo de memoria |
|---|---|---|---|
| Few-shot fijo | Nada (ejemplos escritos a mano) | Nunca | Solo en las instrucciones |
| Few-shot dinámico | Episodios: contexto, acción, resultado, feedback | Se guardan sin transformar | Episódica |
| Reflexion | Auto-crítica del fallo | Tras un fallo | Episódica, con contenido de lección |
| ExpeL | Reglas con votos | En lote, sobre muchas experiencias | Procedimental |

## 1. Few-shot dinámico: recuperar ejemplos

Es el patrón más simple y el más extendido en herramientas. Tiene tres piezas:

1. **Almacén de ejemplos**: pares entrada → salida deseada, con el *embedding* de la entrada.
2. **Selector**: embebe la consulta y trae los k más cercanos (k de 3 a 4 es típico).
3. **Inyección**: los ejemplos entran al prompt, de preferencia como mensajes de usuario y asistente.

Variantes: similitud pura, con diversidad (para no traer k casi duplicados) y diversa por etiqueta. Hay selectores listos en LangChain y servicios gestionados.

**¿Cuánto ayuda?** La ganancia es consistente pero a veces modesta, y depende de la tarea. Un experimento publicado por LangChain en 2024 con *tool-calling* mostró que un modelo pasaba de 16 % (sin ejemplos) a 52 % con 3 ejemplos semánticamente parecidos. Dos matices:

- En ese experimento el banco total era de 13 ejemplos, y el dinámico apenas igualaba a poner los 13. La ventaja de seleccionar aparece cuando el banco es demasiado grande para entrar en el prompt.
- Un cambio global positivo no excluye categorías donde empeora. Conviene medir por tipo de tarea, no solo en total.

**En mi demo** (tareas sintéticas con convenciones inventadas): sin ejemplos acertó 6 de 18 al primer intento, con ejemplos fijos 12 de 18 y con dinámicos 18 de 18. El fijo estaba armado para fallar en un caso (no tenía ningún ejemplo de clientes Premium). Con un fijo que tenga un ejemplo de cada tipo, empata. La demo muestra el **mecanismo**, no que la técnica rinda en general.

## 2. Reflexion: recuperar lecciones

Reflexion se diferencia del few-shot en una cosa: **cuando el agente falla, reflexiona sobre por qué y reintenta, y esa reflexión queda guardada para tareas futuras.**

El ciclo de mi demo:

1. El agente intenta y falla.
2. Un **verificador** externo corrige. No dice «mal»: devuelve su número y el número correcto.
3. El agente escribe una reflexión («usé la tasa compensatoria directamente; el punitorio es 150 % de esa tasa»).
4. Reintenta con la reflexión a la vista.
5. Al terminar la tarea, la lección pasa a la memoria de largo plazo.
6. Se prueba con tareas nuevas.

Un detalle importante: reintentar con el número correcto a la vista es fácil. Por eso lo que importa medir no es la tasa de tareas resueltas en entrenamiento, sino si en una tarea **nueva** el agente acierta **al primer intento** gracias a lo aprendido.

La memoria de la tarea (el buffer de corto plazo) desaparece al terminar. Si la lección no se guarda en otro lado, todo el aprendizaje se pierde.

## 3. ExpeL: recuperar reglas

ExpeL da un paso más: en lugar de guardar lecciones sueltas atadas a un caso, **junta la experiencia de varias tareas y la destila en reglas generales con votos**.

Tres fases en mi demo:

- **Experiencia.** El agente resuelve tareas; falla, reflexiona y reintenta. Las tareas que acierta a la primera no se destilan: no hay nada que aprender de ellas.
- **Destilación.** Cada experiencia se prepara para un destilador (con la diferencia y el cociente entre lo respondido y lo correcto). Un LLM **propone** operaciones sobre el banco de reglas (agregar, editar, acordar, eliminar) y el **código las aplica**. El LLM nunca edita el banco directamente. Cada experiencia que respalda una regla suma un voto.
- **Prueba.** Solo las reglas confirmadas (en mi demo, con al menos 2 votos) se inyectan en el prompt. Se prueba con tareas nuevas y con **controles**: tareas donde la regla no aplica, para comprobar que no se sobre-aplica.

Las reglas tienen ámbito («al exterior», «Premium»). Un voto es una experiencia que respalda la regla, no una opinión ni una garantía de verdad. El umbral de 2 votos es una decisión de diseño de la demo.

## Reflexion o ExpeL

Ambas persisten y recuperan por parecido. La diferencia: Reflexion guarda reflexiones sueltas ligadas a casos concretos; ExpeL las **generaliza**, las destila en reglas y las vota. En la arquitectura, ExpeL cae en el camino de escritura asíncrono más el ciclo de vida de la memoria (consolidar), porque agregar, editar y eliminar reglas es, en el fondo, un refinamiento.

## Lo que la arquitectura no dibuja

- **Una señal de resultado.** Reflexion necesita saber que falló, y ExpeL necesita comparar éxitos y fracasos. De dónde sale esa evaluación (pruebas, un juez, feedback humano) hay que agregarlo como componente. Es la parte difícil.
- **Un disparador distinto por método.** Reflexion escribe tras un fallo y ExpeL en lote. Son políticas de *cuándo*, no cajas nuevas.
- **Crecimiento sin límite.** Si el almacén de episodios o reflexiones no pasa por el ciclo de vida de la memoria (consolidar, expirar, olvidar), se vuelve un buffer sin límite.

## Dónde entra el fine-tuning

Actúa en otro lugar: **dentro de la caja del LLM**. Cambia los pesos, mientras que todo lo anterior cambia lo que se le da al modelo. Se conecta con esta arquitectura por los datos: el almacén de episodios (fracasos y éxitos con su resultado) es materia prima para un dataset de entrenamiento.

## ¿Quién decide qué es «correcto»?

No hay un evaluador único. Lo que muestran las fuentes que revisé:

- **Curación humana** de los ejemplos, o correcciones humanas sobre trazas que llenan un dataset.
- Donde la verdad es computable (cálculos, SQL, esquemas, pruebas), el verificador es una regla en código. Esta es una inferencia mía.
- Para medir si la técnica mejora, **evaluación offline** sobre un conjunto reservado, comparando condiciones (sin ejemplos, fijos, dinámicos). Cuando la salida no se evalúa con un programa, un LLM como juez alineado con correcciones humanas.

## Qué es opinión y qué no

- Todas las demos usan tareas sintéticas con convenciones inventadas para el curso, y cada una corresponde a **una sola corrida**. Muestran mecanismos, no tasas de acierto generalizables.
- En la demo de ExpeL, el verificador revela el número correcto, una señal muy rica. Con uno que solo dijera «mal», rendiría peor. La ayuda numérica la calcula el código y hace el patrón más visible que en un caso real.
- Sobre el uso real del few-shot dinámico: hay oferta de producto de proveedores grandes y evidencia de investigación, pero no encontré casos de producción con nombre y números. Puedo decir que es una técnica soportada y razonable, no qué tan extendida está.
- La investigación fue una búsqueda corta, no una revisión sistemática. De varios papers solo vi el resumen.
- El mapeo de estas técnicas sobre la arquitectura de memoria es interpretación propia.

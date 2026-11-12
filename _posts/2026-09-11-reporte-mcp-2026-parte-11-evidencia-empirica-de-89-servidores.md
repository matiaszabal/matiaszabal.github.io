---
layout: post
title: "Reporte MCP 2026 - Parte 11: evidencia empírica de 89 servidores"
date: 2026-09-11 09:00:00 -0300
description: "Qué muestra una auditoría manual de 89 servidores MCP públicos: la falla dominante no es un bug sino una decisión de autorización que nunca se tomó. Taxonomía de tres capas, el caso del sandbox que no lo era y el catálogo de mitigaciones."
thumbnail: /assets/img/reporte-mcp-2026-parte-11-evidencia-empirica-de-89-servidores/thumb.jpg
tags: [mcp, seguridad, auditoria, autorizacion, reporte-mcp-2026]
---

*Undécimo artículo de la serie **Reporte MCP 2026** ([índice en la Parte 1](/posts/2026/reporte-mcp-2026-parte-1-panorama-y-adopcion/)). Las referencias del tipo «§5.2» remiten a las secciones del reporte.*

## 5.9 Evidencia empírica: qué muestran 89 servidores MCP públicos auditados a mano

Las subsecciones anteriores describen lo que la arquitectura empresarial debería poner alrededor de un servidor MCP, y la Parte 10 lo ordena contra un esquema de clasificación de industria. Falta la pregunta empírica que ninguna de las dos responde: **qué hacen efectivamente los servidores MCP publicados, cuando nadie les exige un Gateway, un PDP externo ni una capa de inspección de contenido.** Un trabajo reciente del autor de este reporte aporta evidencia directa sobre ese punto (Zabaljáuregui, 2026).

### Qué es el estudio, y con qué grano de sal leerlo

Se trata de una auditoría manual de 89 repositorios públicos distintos de servidores MCP (91 turnos de auditoría a lo largo de 15 rondas estratificadas por dominio de aplicación; dos repositorios fueron auditados dos veces, y el trabajo reporta esa discrepancia de forma explícita en lugar de corregirla en silencio). Antes de citar sus cifras corresponde señalar tres limitaciones que el propio trabajo declara, porque cambian cómo deben leerse:

- **Es una muestra por conveniencia, no un censo.** Los repositorios se eligieron dentro de cada dominio a partir de resultados de búsqueda, repositorios oficiales de proveedores y directorios del ecosistema, no mediante un crawl sistemático de un registro. El trabajo declara explícitamente que no reclama representatividad estadística del ecosistema MCP.
- **La verificación fue de un solo revisor.** No hubo una segunda pasada independiente ni se reporta acuerdo inter-observador. El trabajo señala además que buena parte de la ejecución mecánica (lectura de repositorios candidatos, triage del escáner, construcción de pruebas de concepto) la realizó un asistente de investigación basado en IA bajo dirección del autor, con revisión y aprobación humana de cada hallazgo contra el código subyacente.
- **Su escala es dos órdenes de magnitud menor** que la de los estudios automatizados contra los que se posiciona (entre ellos un estudio de escala de registro sobre 67.057 servidores y otro sobre 1.899), a cambio de una profundidad por repositorio que esos no tienen.

Un rasgo metodológico que sí conviene adoptar como buena práctica, y que conecta con el criterio de «fecha de verificación explícita» que este reporte viene aplicando a sus fuentes: cada hallazgo está graduado por **nivel de evidencia** en tres niveles:

1. Solo lectura de código.
2. Ejecutado con el efecto final mockeado.
3. Completamente ejecutado contra una reconstrucción aislada.

La distinción evita que una hipótesis de lectura de código pese retóricamente lo mismo que un exploit corrido.

### El hallazgo central: la falla dominante no es un bug

El trabajo reporta que menos del 10 % de los repositorios (aproximadamente 8 de 89) contiene un error de programación explotable dentro del alcance del estudio: inyección de comandos o de sub-lenguajes, SSRF por un default de librería no sobrescrito, o un sandbox no sólido. Es importante trasladar la cifra con el calificador que el trabajo le pone encima: se presenta explícitamente como una **cota inferior** sobre bugs detectados, no como una estimación de prevalencia, porque la tasa de falsos negativos del escáner usado para el triage no fue medida (su tasa de falsos positivos sí: alrededor del 90 % de los aciertos del escáner resultaron serlo). El argumento no depende de la precisión del número: un piso tan bajo ya alcanza para sostener la tesis.

Y esa tesis es la que cierra el arco de toda la sección 5: **la falla dominante es una decisión de autorización que nunca se tomó, no un error de programación.** La mayoría de los servidores con problemas serios de gobernanza no tiene ningún defecto de código: simplemente expone el plano de control completo de la API que envuelve como un conjunto de herramientas invocables, bajo una única credencial compartida, sin ninguna señal a nivel de protocolo que distinga una lectura de una escritura irreversible.

Los ejemplos que el trabajo da son deliberadamente aburridos desde el punto de vista del código: un servidor de domótica cuya superficie de control entera es una sola herramienta genérica; un servidor de gestión de secretos que mapea 1:1 las 24 operaciones administrativas de su bóveda de respaldo sobre herramientas MCP. Hacen exactamente lo que su código dice; nadie decidió que hacía falta un límite.

### La taxonomía de tres capas

El trabajo organiza esas decisiones no tomadas en tres capas, más un eje ortogonal:

| Capa | Pregunta que responde | Falla característica |
|---|---|---|
| 1. Exposición del plano de control | ¿Qué parte de la superficie de la API subyacente queda expuesta como herramienta invocable? | Mapeo 1:1 de la API completa (plano de datos y plano de control) sobre tools MCP, sin reducción por mínimo privilegio. |
| 2. Delegación de ejecución y confianza | ¿Bajo qué identidad, y con qué confirmación, se ejecuta realmente una herramienta? | Delegación ciega de autoridad (una única credencial compartida y estática, sin acotamiento por invocación) combinada con la ausencia de una compuerta humana ante mutaciones de alto impacto. |
| 3. Señalización de riesgo a nivel de protocolo | ¿El servidor le dice al cliente MCP qué tan riesgosa es una herramienta dada? | Omisión de las annotations nativas de riesgo (`destructiveHint` o equivalente), dejando al LLM como único punto de auto-restricción. |
| Ortogonal: integridad de implementación | Cuando sí se intenta poner un límite, ¿está bien construido? | Un bug en el mecanismo de contención mismo: no ausencia de diseño, sino un diseño que no entrega la garantía que dice entregar. |

Dos cifras de la capa 3 conectan directamente con lo que §3.8 (Parte 5) describía de forma cualitativa: de los 89 repositorios, solo unos 10 (aproximadamente el 11 %) usan las annotations nativas de riesgo de MCP de forma sistemática, y no como un caso aislado. El mecanismo declarativo que §3.8 caracterizó como «hints, no garantías» resulta además, en los hechos, mayormente sin usar.

### El caso que confirma empíricamente la tesis de §5.2

La dimensión nueva más relevante para este reporte es la que el trabajo llama **«intención de contención sin una primitiva técnica válida»**: código que declara explícitamente la intención de aislar algo, eligiendo un mecanismo que estructuralmente no puede proveer esa garantía.

El caso ilustrativo, que el propio trabajo describe como el único hallazgo de nivel 3 (completamente ejecutado) de todo el corpus, es un servidor MCP público de registros de salud que carga el expediente clínico completo de un paciente en memoria y expone una herramienta de evaluación de código para análisis ad-hoc sobre ese expediente, usando el módulo `vm` de Node.js como «sandbox». La documentación del propio Node.js dice, textualmente, que «el módulo `vm` no es un mecanismo de seguridad; no lo use para ejecutar código no confiable». `vm.createContext` aísla los objetos creados dentro del sandbox, pero no los que el código anfitrión le pasa como parámetros: en este caso `console`, una referencia a `lodash` y, críticamente, `Buffer`, todos construidos en el *realm* del proceso anfitrión.

El trabajo reconstruyó esa construcción exacta en un proceso local aislado, con un objeto sintético de relleno en lugar de datos reales de paciente y sin tocar nunca el despliegue del repositorio auditado, y obtuvo desde el «sandbox» una referencia viva al objeto `process` del anfitrión, partiendo de `Buffer.constructor`. El escape es sincrónico y se completa en microsegundos, muy por debajo del presupuesto de ejecución de 2,5 segundos que el propio servidor impone. La herramienta de evaluación no lleva ninguna annotation de riesgo.

Conviene marcar explícitamente por qué este caso importa para este reporte, y en qué dirección va la confirmación. La sección 5.2 (Parte 8) argumentó, desde la especificación, que Roots nunca fue un mecanismo de seguridad y que el límite efectivo siempre vivió en la capa de sandboxing del sistema operativo (permisos de archivos, contenedores, microVMs), no en el protocolo. El hallazgo de §5.9 es la instancia empírica exacta de esa misma tesis, un nivel más abajo: no ya una primitiva del protocolo que se confunde con una frontera de seguridad, sino una primitiva del lenguaje de implementación que se confunde con una, con un exploit reproducible que lo demuestra.

Las dos son la misma clase de error (un componente etiquetado y razonado como frontera de seguridad que estructuralmente no puede serlo) y se refuerzan mutuamente: §5.2 lo deriva del texto normativo, §5.9 lo exhibe corriendo. Es también el punto que §5.8 (Parte 10) identificó como el menos cómodo de mapear: el propio trabajo señala que ninguna de las diez categorías del OWASP MCP Top 10 nombra esta falla, y ofrece la dimensión como refinamiento candidato de MCP05.

### El mapeo del trabajo contra el OWASP MCP Top 10

El trabajo publica su propia correspondencia con el marco de la Parte 10, lo que permite cruzar ambas subsecciones sin inventar el puente:

- La **capa 1** (exposición del plano de control) mapea a MCP02 (Privilege Escalation via Scope Creep).
- La **capa 2** (delegación de ejecución y confianza) mapea a MCP05 (Command Injection & Execution) y MCP07 (Insufficient Authentication & Authorization).
- La **capa 3** (señalización de riesgo a nivel de protocolo) mapea parcialmente a MCP06 (Prompt Injection via Contextual Payloads), sin categoría dedicada para la omisión de annotations de riesgo.
- El **eje ortogonal** de integridad de implementación mapea a MCP05, aplicado a la corrección de una frontera antes que a su ausencia.
- La **dimensión nueva** de contención sin primitiva válida no mapea a ninguna categoría: es la celda deliberadamente vacía ya mencionada.

### El catálogo de mitigaciones: qué se ve cuando la gobernanza sí está

Frente al inventario de lo que falta, el trabajo cataloga **diez patrones de mitigación** observados en código desplegado real, cuatro de ellos recurriendo de forma independiente en bases de código no relacionadas entre sí. Hay una observación agregada que conviene no perder: ningún repositorio del corpus combina más de tres o cuatro de los diez, y ninguno de los patrones es por sí solo suficiente. Los diez, abreviados:

1. **Delegación dinámica de identidad:** se reenvía el token del propio usuario, no una credencial compartida.
2. **Credenciales que nunca cruzan la frontera del protocolo:** el invocador recibe solo un alias opaco.
3. **Decisión de política delegada externamente y *fail-closed*.**
4. **Compuerta de confirmación derivada automáticamente de la anotación de riesgo,** en lugar de opt-in.
5. **Limitación de radio de explosión persistida del lado del servidor:** presupuestos, circuit breakers, límites de tasa que un agente comprometido no puede desactivar por parámetro.
6. **Verificación delegada al motor real:** preguntarle al backend si una consulta es de solo lectura, en vez de reimplementar un parser con expresiones regulares.
7. **Seguro por defecto con relajación explícita.**
8. **Anotación honesta en la herramienta más peligrosa.**
9. **Sanitización del contenido entrante no confiable,** marcado como dato y no como instrucción.
10. **Pinning completo contra SSRF:** bloqueo de rangos más fijación de la conexión a la IP ya validada, no solo su resolución.

Tres de esos patrones merecen una nota por su relación directa con las subsecciones anteriores:

- **El patrón de política externa *fail-closed* es, en los hechos, un PDP/PEP construido de forma independiente.** El trabajo lo encontró en un servidor de pagos que consulta un webhook de política externa antes de ejecutar una transferencia de alto valor y deniega por defecto ante timeout o respuesta no reconocida. Es la arquitectura que §5.5 describe con OPA/Rego, llegada por convergencia y no por prescripción: alguien que resolvía un problema concreto de pagos reinventó la separación entre punto de decisión y punto de aplicación. Es, probablemente, el mejor argumento disponible a favor del patrón de §5.5, más fuerte que cualquier recomendación, porque nadie se lo recomendó a quien lo escribió.
- **El patrón de sanitización de contenido entrante es la contraparte artesanal de Model Armor (§5.6).** Un único repositorio del corpus, un servidor cliente de Telegram, sanitiza el contenido de mensajes y nombres de chat entrantes y lo anota explícitamente como «datos de audiencia de usuario, no instrucciones». Uno, sobre 89. Es una medición indirecta pero elocuente de por qué §5.3 concluye que esta responsabilidad terminó desplazada a la capa de Gateway: casi nadie la implementa del lado del servidor.
- **La verificación delegada al motor real** es un patrón que este reporte no había descrito y que vale la pena registrar como complemento de §5.6: para saber si una consulta SQL es de solo lectura, preguntarle al motor de base de datos en lugar de reimplementar un analizador con expresiones regulares. Es la misma lógica que hace preferible validar contra un JSON Schema antes que con validación ad-hoc.

### Una advertencia sobre la severidad

El estudio sostiene, con tres casos independientes, que la severidad real no es una propiedad del código del servidor. Depende de:

- la **reversibilidad** de la operación en la plataforma de destino (un «delete» que es un borrado suave frente a uno irreversible);
- si el servidor es **auto-alojado y auditable** o alojado por un proveedor y opaco;
- qué **proceso** ejecuta efectivamente una operación de red dada (el servidor MCP, o la infraestructura del proveedor a la que se hace proxy).

Ninguna de esas tres dimensiones es visible desde el análisis estático de un repositorio, y ninguna de las dos primeras es visible siquiera desde el Gateway. Es una limitación que corresponde reconocer respecto del optimismo implícito del pipeline de §5.1–§5.6: **el Gateway gobierna el tráfico, no las consecuencias.**

### Un último matiz metodológico

Al cruzar su catálogo de patrones positivos contra el índice de CVEs mantenido por la comunidad OWASP, el trabajo encontró dos CVEs no relacionados contra un mismo proyecto que había sido citado como ejemplo de buena práctica en otra de sus herramientas. La conclusión que extrae, y que este reporte suscribe, es que la calidad de gobernanza y la corrección a nivel de código son **ejes separados**: un proyecto puede razonar bien sobre autorización y tener bugs, o no tener bugs y no haber tomado nunca una decisión de autorización.

---

**Anterior:** [Parte 10: OWASP MCP-Taxonomy](/posts/2026/reporte-mcp-2026-parte-10-owasp-mcp-taxonomy/) · **Siguiente:** [Parte 12: problemas abiertos, conclusión y referencias](/posts/2026/reporte-mcp-2026-parte-12-problemas-abiertos-conclusion-y-referencias/)

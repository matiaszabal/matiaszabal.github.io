---
layout: post
title: "Reporte MCP 2026 - Parte 7: MCP, A2A y la capa vertical"
date: 2026-09-07 09:00:00 -0300
description: "MCP como capa vertical y A2A como capa horizontal: por qué el panorama de tres protocolos ya es de dos, cómo se combinan en producción y por qué gobernanza compartida no es convergencia técnica."
thumbnail: /assets/img/reporte-mcp-2026-parte-7-mcp-a2a-y-la-capa-vertical/thumb.jpg
tags: [mcp, a2a, protocolos, arquitectura, reporte-mcp-2026]
---

*Séptimo artículo de la serie **Reporte MCP 2026** ([índice en la Parte 1](/posts/2026/reporte-mcp-2026-parte-1-panorama-y-adopcion/)). Las referencias del tipo «§5.7» remiten a las secciones del reporte.*

## 4. MCP como capa vertical en una arquitectura de (al menos) dos capas

### 4.1 MCP vs. A2A vs. «ACP»: un panorama que convergió más rápido de lo que la literatura divulgativa asume

La forma más común de presentar el panorama de protocolos agénticos durante la primera mitad de 2026 fue como una arquitectura de tres capas complementarias:

- **MCP** como capa vertical (agente↔herramienta/dato).
- **A2A** como capa horizontal (agente↔agente, con descubrimiento vía Agent Cards, delegación de tareas y orquestación multi-agente).
- **ACP** como una alternativa REST de menor fricción para quien no quisiera adoptar el SDK completo de MCP (Zylos Research, 2026a).

Esa caracterización de las dos primeras capas sigue siendo válida y es, en efecto, el resumen más preciso disponible hoy: «MCP se ocupa de las conexiones desde aplicaciones de IA hacia herramientas, fuentes de datos y servicios; A2A se ocupa de la comunicación entre agentes operados de forma independiente, incluyendo descubrimiento de capacidades, delegación y el intercambio de resultados de tareas» (quasa.io, 2026). El ejemplo canónico que ilustra la división de trabajo: un agente coordinador usa MCP para leer registros aprobados de un sistema de negocio, y luego usa A2A para delegar un análisis especializado a un agente operado de forma independiente.

Donde el panorama de tres capas ya no resiste un chequeo actualizado es en el tercer elemento. «ACP» no designa un protocolo único, sino que ha sido, en momentos distintos, el nombre de al menos dos iniciativas independientes y hoy discontinuadas como proyectos propios:

- El **Agent Communication Protocol** de IBM Research (proyecto BeeAI, marzo de 2025), que se fusionó formalmente con A2A en agosto de 2025 bajo la gobernanza de LF AI & Data (LF AI & Data, 2025).
- El **Agent Connect Protocol** de AGNTCY (la iniciativa incubada por Cisco Outshift y donada a la Linux Foundation también en 2025), cuya invocación, según crónicas técnicas recientes aunque no confirmado por una fuente institucional de igual peso que la anterior, se habría redirigido hacia A2A a partir de abril de 2026 (Basar, 2026).

En ninguno de los dos casos «ACP» sobrevive como una tercera alternativa arquitectónica comparable a MCP o A2A; sobrevive, en el mejor de los casos, como una API REST de compatibilidad hacia atrás dentro de proyectos que ya delegaron su función de coordinación multi-agente a A2A. Otros protocolos que también usan o usaron la sigla ACP (el Agent Client Protocol de Zed, de agosto de 2025, activo pero acotado a integración editor↔agente, y el Agentic Commerce Protocol de OpenAI y Stripe, de septiembre de 2025, acotado a comercio) ocupan nichos verticales específicos y no compiten por el rol de capa horizontal general (Basar, 2026).

La implicancia para cualquier lectura del ecosistema hecha con una antigüedad de más de un par de meses: tratar «MCP + A2A + ACP» como tres opciones estructuralmente equivalentes ya es, a mediados de 2026, una simplificación desactualizada. El panorama vigente es más bien **MCP (vertical) + A2A (horizontal, ahora bajo la misma gobernanza que MCP desde agosto de 2026)** como el par dominante, con protocolos de nicho alrededor.

### 4.2 Las primitivas en la práctica: Tools, Resources y descubrimiento dinámico de capacidades

Más allá de la capa de transporte, el valor arquitectónico de MCP para un agente individual descansa en una separación de responsabilidades bastante estable a lo largo de las revisiones de especificación:

- **Resources**, identificados por URIs (`file://`, o esquemas definidos por cada servidor), sirven para inyectar contexto (lectura de código, esquemas de bases de datos, documentación, logs) sin efectos secundarios.
- **Tools** se reservan para acciones que sí modifican el entorno (escribir un archivo, ejecutar un script, enviar un correo), con sus entradas y salidas validadas contra los esquemas (`inputSchema` / `outputSchema`) que el propio servidor declara. La revisión 2026-07-28 flexibilizó esos esquemas para admitir cualquier palabra clave de JSON Schema 2020-12, en lugar de un subconjunto restringido (Model Context Protocol Specification, 2026).

El descubrimiento de estas capacidades es dinámico: en la inicialización de una conexión (o, bajo el modelo stateless de la revisión vigente, en cualquier momento vía `tools/list`, `resources/list` y `prompts/list`), el cliente consulta qué puede hacer el servidor, y el agente incorpora esas capacidades sin necesidad de recompilación ni redespliegue de código propio. Es la propiedad que suele describirse como «integración sin código»: conectar un nuevo servidor MCP (un conector a una base de datos, un linter) hace que el agente absorba automáticamente los esquemas JSON-RPC disponibles.

Un detalle de producción añadido en la revisión más reciente, y fácil de pasar por alto: se recomienda ahora que los servidores devuelvan las listas de tools en un **orden determinístico**, específicamente para mejorar la tasa de aciertos de caché de prompts del lado del cliente. Es una optimización que solo tiene sentido una vez que MCP se usa a la escala de tráfico que reportan las cifras de la sección 2.1 (Parte 1).

### 4.3 Adopción combinada MCP + A2A en despliegues de referencia

El ejemplo mejor documentado de una arquitectura de producción que combina ambos protocolos de forma explícita es **Salesforce Agentforce**, donde MCP cumple una doble función:

- *Hacia adentro,* el motor de razonamiento Atlas puede invocar servidores MCP externos como fuente de acciones (GitHub, Jira, APIs propias).
- *Hacia afuera,* flujos de trabajo de Agentforce se exponen como tools MCP a través del catálogo de API de MuleSoft, para que agentes externos (incluido Claude) puedan invocarlos.

A2A, por su parte, se usa específicamente para la delegación entre plataformas: comunicación de agentes de Agentforce con agentes construidos sobre el tooling de Vertex de Google o el Agent Framework de Microsoft (ChatForest, 2026).

La misma fuente introduce una advertencia operacional relevante, el **«problema de la costura»** (*seam problem*): las fallas en los puntos de handoff entre agentes no escalan linealmente con la cantidad de agentes involucrados. «Tres agentes no producen tres veces la superficie de depuración; las interacciones entre agentes producen algo cercano a modos de falla de orden N²» (ChatForest, 2026). Es una observación que conecta directamente con el déficit de observabilidad discutido en la sección 6.3 (Parte 12).

Google ADK (Agent Development Kit) y ServiceNow se citan con frecuencia junto a Agentforce como implementadores del mismo patrón combinado MCP+A2A (ambos ofrecen soporte nativo a los dos protocolos como parte de su tooling de agentes). Pero este reporte no encontró, al momento de su redacción, documentación técnica de tercero de profundidad comparable a la disponible para Agentforce que describa el detalle arquitectónico de esas dos implementaciones; se señala la limitación en lugar de sobre-extender la evidencia.

### 4.4 ¿Convergencia técnica o coexistencia institucional? El trabajo conjunto MCP/A2A, sin confirmar

Es importante no confundir dos fenómenos que suelen mencionarse juntos: la **convergencia de gobernanza** (MCP y A2A conviven hoy bajo el paraguas de la misma fundación) y una eventual **convergencia técnica** (una especificación conjunta que defina, por ejemplo, cómo una invocación de tool de MCP puede disparar una delegación de A2A, o viceversa).

Una investigación de marzo de 2026 mencionaba un «esfuerzo conjunto de especificación MCP/A2A reportado para el tercer trimestre de 2026», sin que existiera un borrador oficial en ese momento (Zylos Research, 2026b). Una nota independiente sobre la incorporación formal de A2A a la AAIF, del 17 de agosto de 2026, es explícita al respecto: el movimiento fue «principalmente organizativo» y «la próxima evidencia significativa de una alineación más profunda sería técnica (como guías de integración conjuntas, tests de conformidad o herramientas interoperables) y esas adiciones no formaron parte del cambio de alojamiento» (quasa.io, 2026).

Al momento de redactar este reporte no se identificó ningún borrador de especificación conjunta publicado. La lectura más defendible con la evidencia disponible es que la convergencia institucional es un hecho consumado, mientras que la convergencia técnica sigue siendo, en el mejor de los casos, una intención declarada sin cronograma público verificable.

(La sección 5.7, en la Parte 9 de esta serie, retoma esta distinción al analizar cuánto de la infraestructura de seguridad construida para MCP se reutiliza, a nivel de implementación, en despliegues de A2A: una convergencia de tooling del lado de quien despliega, distinta de la convergencia técnica entre especificaciones que esta sección no encontró.)

---

**Anterior:** [Parte 6: descubrimiento dinámico en la práctica](/posts/2026/reporte-mcp-2026-parte-6-descubrimiento-dinamico-en-la-practica/) · **Siguiente:** [Parte 8: gateways, sandboxing y prompt injection](/posts/2026/reporte-mcp-2026-parte-8-gateways-sandboxing-y-prompt-injection/)

---
layout: post
title: "Reporte MCP 2026 - Parte 1: panorama y adopción"
date: 2026-09-01 09:00:00 -0300
description: "El Model Context Protocol en 2026: resumen del reporte, cómo pasó de conector de herramientas a sustrato de interoperabilidad y qué dicen (y qué no) las cifras de adopción."
thumbnail: /assets/img/reporte-mcp-2026-parte-1-panorama-y-adopcion/thumb.jpg
tags: [mcp, agentes, protocolos, reporte-mcp-2026]
---

*Este es el primer artículo de la serie **Reporte MCP 2026**, que divide en doce partes el reporte «El Model Context Protocol en 2026: de conector de herramientas a sustrato de interoperabilidad en arquitecturas agénticas». Las referencias del tipo «sección 3.3» o «§5.1» remiten a las secciones del reporte completo; el índice de la serie está al final de este artículo.*

## Resumen (TL;DR)

### Evolución del protocolo (revisión 2026-07-28)

- **Transición a stateless.** Se eliminó la sesión a nivel de protocolo y el handshake de inicialización. Cada petición JSON-RPC es autónoma y declara versión y capacidades dentro de la estructura de metadatos `_meta`, lo que facilita el balanceo de carga sin *sticky sessions*.
- **Reemplazo de HTTP+SSE.** Streamable HTTP pasó a ser el estándar definitivo sobre un único endpoint; HTTP+SSE quedó formalmente deprecado.
- **Patrón Multi Round-Trip Requests (MRTR).** Reemplaza las peticiones anidadas servidor-a-cliente sobre conexiones bidireccionales persistentes. Las solicitudes de contexto adicional devuelven un `InputRequiredResult` con un estado opaco (`requestState`) firmado criptográficamente, lo que traslada la persistencia de estado al cliente.
- **Deprecación de primitivas fundacionales.** Sampling, Roots y Logging quedaron deprecados, con una ventana de transición de 12 meses. La orquestación y el razonamiento intermedio se delegan a la capa de aplicación o de modelo, y el aislamiento de archivos pasa a depender del sandboxing del sistema operativo.
- **Modularización de Tasks.** La gestión de operaciones asíncronas de larga duración salió del núcleo para convertirse en la extensión formal `io.modelcontextprotocol/tasks`, basada en polling explícito (`tasks/get`) y actualización (`tasks/update`).

### Usos agénticos y arquitectura integrada

- **Separación de capas (MCP + A2A).** MCP se consolida como la capa vertical (conexión agente-herramientas/datos). Para la capa horizontal (coordinación, negociación y delegación entre agentes independientes), el estándar convergente es Agent2Agent (A2A) de Google. Ambos están alojados en la Agentic AI Foundation (AAIF), bajo la Linux Foundation.
- **Inyección dinámica de capacidades.** El descubrimiento vía `tools/list` y `resources/list` permite que el agente absorba nuevos métodos sin recompilación. Para optimizar el tráfico a gran escala, las listas de herramientas se ordenan de forma determinística y así maximizan la tasa de aciertos del *prompt caching* del cliente.
- **MCP Gateways en producción.** La arquitectura empresarial abandonó la conexión directa punto a punto en favor de gateways intermediarios. Estos aplican políticas de RBAC, filtrado de prompt injection indirecto, auditoría JSON-RPC y un patrón de triple compuerta (*triple-gate*) ante la infraestructura crítica.
- **Desafíos abiertos en redes agénticas.**
  - *Identidad multi-salto:* OAuth 2.1 con Resource Indicators resuelve la delegación directa cliente-servidor, pero falla en cadenas de delegación recursiva (*confused deputy* entre múltiples agentes).
  - *Observabilidad y «seam problem»:* la integración multi-agente presenta fallas superlineales en los puntos de transferencia (*handoffs*), y la falta de un estándar de traza obligatorio en MCP dificulta la depuración del estado del agente.

## 1. Introducción

En noviembre de 2024, Anthropic publicó el Model Context Protocol (MCP) como una especificación abierta para estandarizar la forma en que los modelos de lenguaje acceden a herramientas y fuentes de datos externas. Menos de dos años después, MCP dejó de discutirse como una propuesta entre varias y pasó a ocupar el lugar de infraestructura dada por sentada. En diciembre de 2025 Anthropic reportaba más de 10.000 servidores públicos activos y 97 millones de descargas mensuales combinadas de sus SDKs de Python y TypeScript (Model Context Protocol Blog, 2025). Ese mismo mes el protocolo fue donado a una fundación neutral, la Agentic AI Foundation (AAIF), alojada por la Linux Foundation, junto con goose (Block) y AGENTS.md (OpenAI), con Amazon, Google, Microsoft y OpenAI entre sus miembros Platinum (Linux Foundation, 2025).

Conviene, sin embargo, tratar las cifras de adopción con cautela metodológica. Los relevamientos independientes muestran conteos de servidores que oscilan entre 9.652 y casi 29.000 según el snapshot y la fuente (registro oficial frente a repositorios de GitHub con el tema `mcp-server`). Las encuestas empresariales recientes sitúan la adopción en producción bastante más abajo de lo que sugiere el entusiasmo del ecosistema: 41 % combinado entre producción limitada y amplia, según una encuesta de Stacklok de 2026 que además retiró explícitamente una cifra previa del 78 % por no estar sustentada (digitalapplied.com, 2026). La ausencia de un registro canónico único es en sí misma un dato relevante sobre el estado de madurez del protocolo, y este reporte trata cada cifra citada como una estimación situada en el tiempo, no como un hecho estable.

Ese primer capítulo de la historia de MCP, su consolidación como estándar de facto, está relativamente cerrado. El objeto de este reporte es distinto: preguntar qué rol cumple MCP hoy, una vez asumida esa consolidación, dentro de arquitecturas agénticas que ya no son un único modelo llamando herramientas, sino redes de múltiples agentes que se coordinan entre sí, delegan tareas y operan sobre infraestructura empresarial con requisitos de seguridad, auditoría y gobernanza.

En ese contexto, MCP se asentó específicamente como la capa vertical del stack, la que conecta un agente individual con sus herramientas y datos, mientras que Agent2Agent (A2A), de Google, cubre la capa horizontal de coordinación entre agentes independientes. Un hallazgo central del reporte, que actualiza el consenso divulgativo de comienzos de 2026, es que el panorama de protocolos convergió más rápido de lo previsto. Lo que hasta hace pocos meses se describía como un ecosistema de tres protocolos (MCP, A2A y «ACP») es hoy, en la práctica, un ecosistema de dos, con distintas iniciativas que alguna vez reclamaron el nombre «ACP» absorbidas, archivadas o redirigidas hacia A2A (sección 4.1).

Al mismo tiempo, el protocolo siguió evolucionando técnicamente a un ritmo que desactualiza rápido cualquier descripción de su funcionamiento interno. La revisión de especificación del 28 de julio de 2026 eliminó las sesiones y el handshake de inicialización en favor de un modelo completamente stateless, introdujo el patrón Multi Round-Trip Requests (MRTR) para reemplazar los requests servidor→cliente que antes exigían una conexión bidireccional persistente, y deprecó formalmente tres de sus primitivas fundacionales (Sampling, Roots y Logging) con una ventana de doce meses antes de su remoción.

El reporte documenta esa evolución técnica (sección 3), la posición de MCP en el stack de protocolos agénticos (sección 4), las prácticas de seguridad y gobernanza operacional que se construyeron alrededor de él en producción (sección 5) y los problemas que siguen genuinamente abiertos (identidad, descubrimiento a escala de Internet, autorización granular y observabilidad, sección 6), antes de cerrar con una síntesis de hacia dónde se movió la conversación (sección 7).

## 2. De prototipo a estándar de facto: la trayectoria de adopción (nov. 2024 – 2026)

### 2.1 Cronología y cifras de adopción

MCP se lanzó el 25 de noviembre de 2024. Su trayectoria de adopción, reconstruida a partir de fuentes primarias y relevamientos independientes, es la siguiente:

- **Noviembre de 2024:** lanzamiento inicial (stdio y HTTP+SSE como transportes).
- **Marzo de 2025 (spec 2025-03-26):** introducción de Streamable HTTP, que reemplaza a HTTP+SSE.
- **Diciembre de 2025:** Anthropic reporta más de 10.000 servidores públicos activos y 97 millones de descargas mensuales combinadas de los SDKs de Python y TypeScript, al cumplirse un año del proyecto (Model Context Protocol Blog, 2025). El mismo mes, MCP es donado a la Agentic AI Foundation.
- **Abril de 2026:** primer MCP Dev Summit, en Nueva York.
- **Mayo de 2026:** un snapshot independiente sobre la API del registro oficial cuenta 9.652 entradas vigentes (28.959 si se incluyen versiones históricas); una búsqueda sobre repositorios de GitHub con el tema `mcp-server` arroja 15.926 resultados (digitalapplied.com, 2026).
- **Julio de 2026:** revisión de especificación 2026-07-28, la más profunda desde el lanzamiento (sección 3).
- **Agosto de 2026:** A2A se incorpora como proyecto alojado por la AAIF (17 de agosto; quasa.io, 2026).

Sobre adopción en producción, a diferencia de la disponibilidad de servidores o descargas de SDK, una encuesta de Stacklok de 2026 sobre organizaciones de software encontró que un 29 % tenía despliegues de MCP en «producción limitada» y un 12 % en «producción amplia» (41 % combinado). Es una cifra bastante menor que la que circuló informalmente (78 %) y que el propio artículo que la reportaba retiró por no estar sustentada en una fuente identificable (digitalapplied.com, 2026).

El cuadro que emerge es el de un protocolo con una capa de disponibilidad (servidores publicados, SDKs descargados) que maduró muy rápido, y una capa de adopción productiva real que, si bien creciente, todavía es minoritaria y depende fuertemente de cómo cada organización define «producción».

### 2.2 Gobernanza: la Agentic AI Foundation bajo la Linux Foundation

El 9 de diciembre de 2025, la Linux Foundation anunció la formación de la Agentic AI Foundation (AAIF), con Anthropic (MCP), Block (goose) y OpenAI (AGENTS.md) como contribuyentes fundadores. Amazon Web Services, Anthropic, Block, Bloomberg, Cloudflare, Google, Microsoft y OpenAI son miembros Platinum; Adyen, Cisco, Docker, IBM, Oracle, Salesforce, SAP, Shopify y otros figuran como miembros Gold (Linux Foundation, 2025).

Según el propio blog de MCP, el cambio de gobernanza fue deliberadamente conservador: la estructura de mantenedores y el proceso de propuestas de especificación (SEP) se mantuvieron intactos, y la Linux Foundation provee infraestructura y supervisión neutral «sin dictar la dirección técnica de MCP» (Model Context Protocol Blog, 2025). El objetivo explícito fue reducir el temor al *vendor lock-in* que frenaba la adopción empresarial, siguiendo el mismo modelo de tutela neutral que sostiene a Kubernetes, PyTorch o Node.js.

Este movimiento de convergencia institucional no quedó limitado a MCP:

- Cisco, a través de su incubadora Outshift, donó su proyecto AGNTCY (que incluía una especificación propia llamada Agent Connect Protocol) a la Linux Foundation en 2025 (Linux Foundation, 2025; The Next Platform, 2025).
- Por separado, el Agent Communication Protocol de IBM Research (el proyecto BeeAI) se fusionó formalmente con A2A en agosto de 2025 bajo la gobernanza de LF AI & Data (LF AI & Data, 2025).
- Más recientemente, A2A se incorporó como proyecto alojado por la propia AAIF el 17 de agosto de 2026, un movimiento que la cobertura especializada describe como «principalmente organizativo», sin que se haya anunciado todavía ninguna alineación técnica más profunda entre las especificaciones de MCP y A2A (quasa.io, 2026).

Volveremos sobre esta distinción, gobernanza compartida frente a convergencia técnica, en la sección 4.4 (Parte 7 de la serie), porque es fácil, y engañoso, confundir una como evidencia de la otra.

---

## Índice de la serie

1. **Parte 1: panorama y adopción** (este artículo)
2. [Parte 2: del protocolo con sesión al protocolo stateless](/posts/2026/reporte-mcp-2026-parte-2-del-protocolo-con-sesion-al-protocolo-stateless/)
3. [Parte 3: autorización OAuth y agentes sin humano](/posts/2026/reporte-mcp-2026-parte-3-autorizacion-oauth-y-agentes-sin-humano/)
4. [Parte 4: MRTR y la extensión Tasks](/posts/2026/reporte-mcp-2026-parte-4-mrtr-y-la-extension-tasks/)
5. [Parte 5: semántica del protocolo y señales de riesgo](/posts/2026/reporte-mcp-2026-parte-5-semantica-del-protocolo-y-senales-de-riesgo/)
6. [Parte 6: descubrimiento dinámico en la práctica](/posts/2026/reporte-mcp-2026-parte-6-descubrimiento-dinamico-en-la-practica/)
7. [Parte 7: MCP, A2A y la capa vertical](/posts/2026/reporte-mcp-2026-parte-7-mcp-a2a-y-la-capa-vertical/)
8. [Parte 8: gateways, sandboxing y prompt injection](/posts/2026/reporte-mcp-2026-parte-8-gateways-sandboxing-y-prompt-injection/)
9. [Parte 9: defensa en profundidad con OPA, Pydantic y Model Armor](/posts/2026/reporte-mcp-2026-parte-9-defensa-en-profundidad-opa-pydantic-y-model-armor/)
10. [Parte 10: OWASP MCP-Taxonomy](/posts/2026/reporte-mcp-2026-parte-10-owasp-mcp-taxonomy/)
11. [Parte 11: evidencia empírica de 89 servidores](/posts/2026/reporte-mcp-2026-parte-11-evidencia-empirica-de-89-servidores/)
12. [Parte 12: problemas abiertos, conclusión y referencias](/posts/2026/reporte-mcp-2026-parte-12-problemas-abiertos-conclusion-y-referencias/)

**Siguiente:** [Parte 2: del protocolo con sesión al protocolo stateless](/posts/2026/reporte-mcp-2026-parte-2-del-protocolo-con-sesion-al-protocolo-stateless/)

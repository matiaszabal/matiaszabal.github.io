---
layout: post
title: "Reporte MCP 2026 - Parte 2: del protocolo con sesión al protocolo stateless"
date: 2026-09-02 09:00:00 -0300
description: "El transporte de MCP pasó de HTTP+SSE a Streamable HTTP y, con la revisión 2026-07-28, a un modelo sin sesiones ni handshake. Qué cambió y qué malentendidos circulan."
thumbnail: /assets/img/reporte-mcp-2026-parte-2-del-protocolo-con-sesion-al-protocolo-stateless/thumb.jpg
tags: [mcp, transporte, streamable-http, reporte-mcp-2026]
---

*Segundo artículo de la serie **Reporte MCP 2026** ([Parte 1](/posts/2026/reporte-mcp-2026-parte-1-panorama-y-adopcion/) incluye el índice completo). Las referencias del tipo «§3.3» remiten a las secciones del reporte.*

## 3. Evolución técnica: de protocolo con sesión a protocolo stateless

### 3.1 Transporte: de HTTP+SSE a Streamable HTTP, y de ahí a un modelo sin sesiones

El transporte HTTP original de MCP, denominado explícitamente HTTP+SSE Transport, acoplaba dos endpoints HTTP independientes: un canal `GET /sse`, unidireccional y de larga duración, por el que el cliente escuchaba eventos del servidor, y un endpoint `POST /messages?sessionId=...` separado, por el que enviaba cada request JSON-RPC. Ese diseño exigía *sticky sessions* en cualquier balanceador de carga (el `sessionId` ataba ambas conexiones entre sí, y el estado de la conversación vivía pegado a una conexión SSE específica) y arrastraba dos problemas operacionales adicionales:

- Si el stream SSE se cortaba a mitad de una operación larga, el estado de esa llamada JSON-RPC en curso se perdía sin mecanismo de recuperación integrado.
- Mantener conexiones SSE abiertas de forma permanente resultaba costoso en infraestructura serverless o de auto-escalado, donde cada instancia activa tiene un costo.

La especificación 2025-03-26 introdujo Streamable HTTP como reemplazo: un único endpoint HTTP donde cada respuesta puede, opcionalmente, resolverse mediante un stream, pero sin exigir que el cliente mantenga una conexión persistente abierta para recibir mensajes del servidor.

Streamable HTTP resolvió el problema de las *sticky sessions*, pero mantuvo un concepto de sesión (identificada por un header `Mcp-Session-Id`) y un handshake de inicialización (`initialize` / `notifications/initialized`) que debía completarse antes de cualquier otra operación. La revisión 2026-07-28 fue un paso más allá y eliminó ambos por completo (SEP-2567, SEP-2575): ya no hay sesiones a nivel de protocolo, ya no hay handshake, y cada request lleva su propia versión de protocolo y capacidades declaradas del cliente en un campo `_meta` (`io.modelcontextprotocol/protocolVersion`, `io.modelcontextprotocol/clientCapabilities`). Para negociar versión antes de cualquier otra llamada se añadió un nuevo RPC, `server/discover`, que un servidor debe implementar obligatoriamente. La motivación declarada es operacional: un protocolo sin estado a nivel de conexión permite que cualquier request aterrice en cualquier instancia de un servidor detrás de un balanceador de carga, sin necesidad de almacenamiento compartido entre instancias (Model Context Protocol Blog, 2026).

Como consecuencia de este mismo cambio, HTTP+SSE, ya deprecado desde 2025-03-26, fue formalmente reclasificado como *Deprecated* bajo una nueva política de ciclo de vida de funcionalidades que la propia revisión introdujo (SEP-2596: ventana mínima de doce meses antes de la remoción, anotaciones `@deprecated` y un proceso de dos SEPs, una para deprecar y otra para remover; Model Context Protocol Specification, 2026). También se eliminó la posibilidad de reanudar un stream interrumpido mediante `Last-Event-ID`: una respuesta cortada a mitad de camino ahora se resuelve reemitiendo la request completa con un nuevo `id`, no reanudando la anterior.

### Una advertencia sobre el material educativo

Vale una advertencia práctica, motivada por un chequeo puntual hecho para este reporte: buena parte del material educativo disponible públicamente sobre MCP, incluyendo cursos de referencia como el MCP Course de Hugging Face, todavía describe el ciclo de vida de la interacción en cuatro fases (inicialización con intercambio de versión y capacidades → discovery → ejecución → terminación) como si fuera el estado vigente del protocolo (Hugging Face, s.f.-a). Esa descripción fue exacta durante la vigencia de 2025-03-26 y 2025-11-25, pero dejó de serlo con 2026-07-28: ya no existe una fase de inicialización que negociar ni una sesión que terminar, porque no hay sesión que abrir en primer lugar.

Un segundo chequeo sobre otra página del mismo curso, la unidad dedicada a clientes MCP, encuentra un caso todavía más desactualizado. Esa página afirma sin matices que «el tipo de transporte es stdio o sse» (Hugging Face, s.f.-b), sin mencionar Streamable HTTP (vigente desde 2025-03-26) ni, por supuesto, el modelo stateless de 2026-07-28. Describe, en rigor, el transporte tal como existía al lanzamiento de noviembre de 2024, una revisión de especificación entera por detrás de la que reemplazó a SSE.

El caso ilustra un punto metodológico más amplio, relevante para cualquier trabajo de referencia sobre MCP: la vida media de la documentación técnica de este protocolo parece ser sensiblemente más corta que el ciclo de publicación típico de un curso o material didáctico. Eso exige tratar toda fuente secundaria sobre MCP con una **fecha de verificación explícita**, no solo una fecha de publicación.

### Dos confusiones frecuentes sobre «Streamable HTTP» (y una corrección necesaria)

Vale la pena aclarar dos malentendidos habituales sobre el transporte HTTP de MCP, ambos presentes en material divulgativo sobre el protocolo.

**WebSocket no es, y nunca fue, un transporte oficial de MCP.** Es cierto que WebSocket (RFC 6455) y Streamable HTTP resuelven el problema del streaming bajo paradigmas de red distintos: WebSocket abre un socket TCP bidireccional de larga duración tras un handshake de actualización (`Upgrade: websocket`), con *full-duplex* simétrico entre cliente y servidor; Streamable HTTP, en cambio, es un patrón construido sobre HTTP estándar de tipo request/response, sin necesidad de mantener un socket persistente fuera del ciclo de vida de cada request.

Pero de esa distinción técnica real no se sigue que WebSocket sea «el transporte clásico» de MCP para conexiones locales o peer-to-peer. La especificación oficial, en todas sus revisiones hasta la vigente 2026-07-28, solo define dos transportes estándar, stdio y Streamable HTTP, con HTTP+SSE como su predecesor ya deprecado. Sí existió una propuesta formal para incorporar WebSocket al protocolo: la SEP-1287, «WebSocket transport for MCP», abierta el 2 de agosto de 2025 y cerrada sin fusionarse el 3 de diciembre de 2025 (GitHub — Model Context Protocol, 2025). Hoy WebSocket solo aparece como propuesta de nivel SDK o comunidad (por ejemplo, un issue abierto en el repositorio `modelcontextprotocol/go-sdk`), nunca como parte del protocolo core.

La renuncia a un socket bidireccional persistente no es un descuido de diseño. Es la misma decisión arquitectónica que ya motivó el abandono de HTTP+SSE y, más tarde, la eliminación de sesiones en 2026-07-28: favorecer un transporte stateless, compatible con balanceadores de carga simples y con infraestructura serverless, por sobre uno que exige afinidad de conexión.

**Streamable HTTP tampoco es simplemente sinónimo de «SSE»**, ni, a la inversa, el combo de dos endpoints separados (uno GET para el stream, otro POST para los requests, con `202 Accepted` inmediato) que a veces se describe. Bajo la especificación vigente, Streamable HTTP usa un único endpoint HTTP para todo el intercambio. El flujo real:

1. El cliente envía cada request JSON-RPC mediante `POST` a ese único endpoint.
2. El servidor responde de una de dos formas: un `application/json` directo con la respuesta completa, o bien una actualización a `text/event-stream`, un stream de Server-Sent Events acotado exclusivamente a esa request (progreso, resultado final), que el servidor cierra al terminar.
3. Un `202 Accepted` sin cuerpo solo aparece cuando el POST transporta una notificación o una respuesta del cliente que no espera contestación; nunca como acuse de recibo de un request que se resolverá después, en un stream aparte.

Ese último patrón (el POST devuelve 202 de inmediato y la respuesta real llega más tarde por un stream SSE abierto por separado vía GET) sí existió, pero corresponde al transporte HTTP+SSE original (pre-2025-03-26), ya deprecado; no es como opera Streamable HTTP hoy.

La revisión 2026-07-28 fue, además, un paso más allá de lo ya descrito: no solo eliminó sesiones y handshake, sino el método GET del todo. El endpoint MCP pasó a aceptar únicamente POST, y un servidor conforme a esta revisión responde `405 Method Not Allowed` ante un GET o un DELETE. En las revisiones anteriores (2025-03-26, 2025-06-18), un GET al mismo endpoint era válido pero opcional, reservado para que el servidor iniciara notificaciones fuera del ciclo de una respuesta POST.

### Cómo encaja con las pausas

Esto se conecta con el patrón MRTR de la sección 3.3 (Parte 4), porque explica cómo Streamable HTTP soporta pausas (por ejemplo, esperar confirmación humana vía *elicitation*) sin volver a depender de una conexión persistente. Cuando una operación necesita esa pausa, el servidor no mantiene el stream SSE abierto a la espera de una respuesta humana: lo cierra devolviendo un `InputRequiredResult` dentro de esa misma respuesta a la request original, y es el cliente quien reintenta más tarde con un nuevo request JSON-RPC (nuevo `id`, `input_responses` con la respuesta del usuario).

La combinación de ambos mecanismos (un único endpoint que alterna entre JSON directo y SSE acotado a cada request, más MRTR para las pausas) es lo que permite que Streamable HTTP sea, a la vez, capaz de streaming y completamente stateless a nivel de conexión.

---

**Anterior:** [Parte 1: panorama y adopción](/posts/2026/reporte-mcp-2026-parte-1-panorama-y-adopcion/) · **Siguiente:** [Parte 3: autorización OAuth y agentes sin humano](/posts/2026/reporte-mcp-2026-parte-3-autorizacion-oauth-y-agentes-sin-humano/)

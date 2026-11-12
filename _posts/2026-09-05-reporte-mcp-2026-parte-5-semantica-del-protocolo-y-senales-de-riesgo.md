---
layout: post
title: "Reporte MCP 2026 - Parte 5: semántica del protocolo y señales de riesgo"
date: 2026-09-05 09:00:00 -0300
description: "Primitivas del servidor (resources, tools, prompts), descubrimiento en dos niveles, modelo de errores y la diferencia entre annotations declarativas y elicitation en tiempo real."
thumbnail: /assets/img/reporte-mcp-2026-parte-5-semantica-del-protocolo-y-senales-de-riesgo/thumb.jpg
tags: [mcp, semantica, annotations, elicitation, reporte-mcp-2026]
---

*Quinto artículo de la serie **Reporte MCP 2026** ([índice en la Parte 1](/posts/2026/reporte-mcp-2026-parte-1-panorama-y-adopcion/)). Las referencias del tipo «§3.3» remiten a las secciones del reporte.*

## 3.5 Semántica del protocolo: primitivas, mensajes y modelo de interacción

A nivel puramente semántico, independientemente de si el transporte es un conducto stdio, un socket o un flujo HTTP, MCP opera como un protocolo de comunicación síncrona/asíncrona basado en JSON-RPC 2.0. Su semántica define la interacción entre tres entidades conceptuales: el **Host** (entorno de ejecución), el **Cliente** (orquestador del protocolo) y el **Servidor** (proveedor de contexto y capacidad).

La semántica del protocolo se articula en torno a tres primitivas nucleares del lado del servidor, un esquema de negociación de capacidades y un patrón de gestión de estado diferido.

### Negociación de capacidades y ciclo de vida

En la especificación actual, la semántica de la sesión es completamente stateless.

- **Descubrimiento semántico (`server/discover`).** Antes de cualquier interacción, el cliente puede consultar la versión de protocolo soportada y el conjunto de capacidades del servidor.
- **Metadatos por mensaje (`_meta`).** Cada mensaje JSON-RPC incluye metadatos explícitos (`io.modelcontextprotocol/protocolVersion` y `clientCapabilities`), lo que elimina la necesidad de un handshake con estado previo (ver también §3.1).

### Descubrimiento de servidores: nivel de red y nivel semántico

Conviene distinguir dos niveles de «descubrimiento» que suelen mencionarse como si fueran uno solo: el descubrimiento de red/endpoint (cómo el Host localiza e instancia la conexión con un servidor) y el descubrimiento semántico de capacidades (cómo el cliente, una vez conectado, inspecciona lo que ese servidor sabe hacer). El primero es responsabilidad del Host, no del protocolo MCP en sí, que no define ningún mecanismo propio de *service discovery* de red:

- **Configuración local (transporte stdio).** El Host lee un archivo de manifiesto (por ejemplo, `mcp_config.json`, siguiendo la convención popularizada por clientes de escritorio) que declara los binarios o comandos a ejecutar (`npx -y @modelcontextprotocol/server-postgres`, por caso); el Host levanta el subproceso y establece la comunicación por entrada/salida estándar.
- **Catálogos y MCP Gateways (transporte HTTP).** En entornos distribuidos o empresariales, el Host se conecta a un Gateway o registro central (el mismo patrón *hub-and-spoke* descrito en §5.1) que expone los endpoints HTTP/Streamable de los servidores autorizados, típicamente protegidos por los mecanismos de autorización de §3.2.
- **Integración con A2A para redes de agentes.** A escala de red entre dominios distintos, un agente usa A2A para localizar a otro agente mediante *Agent Cards* (§6.1), que declaran endpoint, capacidades y esquema de autenticación. Una vez localizado el agente objetivo a nivel horizontal, la invocación interna a sus herramientas y datos vuelve a ser, de forma vertical, una llamada MCP.

El segundo nivel, el descubrimiento semántico, es el que efectivamente define el protocolo:

```text
[Cliente MCP] --- (1) server/discover ------------------->  [Servidor MCP]
[Cliente MCP] <-- (2) versión de protocolo + metadatos ----  [Servidor MCP]

[Cliente MCP] --- (3) tools/list ------------------------->  [Servidor MCP]
[Cliente MCP] <-- (4) lista de tools + JSON Schema --------  [Servidor MCP]

[Cliente MCP] --- (5) resources/list --------------------->  [Servidor MCP]
[Cliente MCP] <-- (6) URIs y tipos MIME -------------------  [Servidor MCP]
```

Una vez recibidas estas listas, el cliente las traduce al formato de invocación nativo del LLM que orquesta (el mecanismo de «integración sin código» de la sección 4.2, Parte 7, donde también se cubre la recomendación de ordenar las listas de forma determinística para maximizar aciertos de *prompt caching*). Si se agrega o modifica un servidor en la configuración del Host, el agente dispone de las nuevas capacidades en la siguiente petición, sin recompilación ni redespliegue de código propio.

### Las primitivas del servidor

La semántica distingue estrictamente entre lectura pura de datos y acciones con efectos secundarios:

- **Resources (recursos).** *Semántica:* acceso de solo lectura (lectura pasiva). *Mecanismo:* identificados por URIs (`resources/read`, `resources/list`); la respuesta retorna contenido textual o binario (base64) junto con un tipo MIME. *Uso:* inyección de contexto al LLM (código fuente, logs, esquemas de base de datos) sin alterar el entorno.
- **Tools (herramientas).** *Semántica:* invocación de funciones con efectos secundarios (*side effects*). Conviene precisar algo que el texto fuente daba por sentado: el protocolo no garantiza ni exige que las tools sean deterministas, y buena parte de las herramientas del mundo real (una consulta a una API externa, la ejecución de código) no lo son. Es una distinción relevante para razonar sobre la seguridad de los reintentos bajo MRTR (§3.3). *Mecanismo:* se descubren vía `tools/list` y se ejecutan vía `tools/call`. *Validación:* tanto los parámetros de entrada (`inputSchema`) como la estructura de respuesta (`outputSchema`) se validan contra JSON Schema.
- **Prompts (plantillas).** *Semántica:* recetas o flujos de trabajo predefinidos por el servidor (`prompts/get`, `prompts/list`). *Mecanismo:* parametrizan mensajes estructurados para guiar la interacción del modelo con las herramientas del servidor.

### Patrón semántico interactivo: MRTR

Cuando una llamada a una herramienta o recurso requiere información adicional o autorización en tiempo de ejecución, el servidor no puede pausar la conexión esperando un callback: no hay conexión persistente que pausar, bajo el modelo stateless de §3.1. La semántica de ejecución resuelve esto mediante MRTR (descrito en detalle en §3.3, Parte 4):

```text
[Cliente] --- (1) tools/call --->                                  [Servidor]
[Cliente] <-- (2) InputRequiredResult (requestState) ---           [Servidor]
          |
          | (resuelve la elicitation)
          |
[Cliente] --- (3) tools/call (inputResponses + requestState) --->  [Servidor]
[Cliente] <-- (4) resultado final ---                              [Servidor]
```

- **`InputRequiredResult`:** el servidor responde con `resultType: "input_required"`, suspendiendo semánticamente la tarea sin mantener ninguna conexión abierta a la espera.
- **`requestState`:** un payload opaco para el cliente que el servidor debe proteger criptográficamente (HMAC o AEAD) cuando su contenido influye en decisiones de autorización o en lógica de negocio. La protección no es una exigencia incondicional del protocolo, sino una obligación condicionada a la sensibilidad de lo que ese estado representa (Model Context Protocol Specification, 2026).
- **Reintento desacoplado:** el cliente resuelve la petición pendiente (por ejemplo, pidiéndole datos al usuario vía elicitation) y vuelve a emitir la llamada original con un nuevo `id` de JSON-RPC, adjuntando la respuesta y el `requestState` recibido, lo que le permite al servidor reanudar el flujo sin haber guardado estado propio en memoria entre ambas llamadas.

### Errores y modelo de excepción

MCP mapea sus fallos de protocolo sobre los códigos de error estándar de JSON-RPC 2.0: `-32700` (Parse error), `-32600` (Invalid Request), `-32601` (Method not found), `-32602` (Invalid params) y `-32603` (Internal error). Desde la revisión 2026-07-28 reserva el rango `-32020` a `-32099` para códigos específicos de la especificación (por ejemplo, `-32021` para `MissingRequiredClientCapability` o `-32022` para `UnsupportedProtocolVersion`), mientras que `-32000` a `-32019` queda como espacio de implementación libre, heredado de convenciones previas de los distintos SDKs (Model Context Protocol Specification, 2026).

A esto se añade una capa de errores de dominio de aplicación dentro del propio objeto `result`, típicamente `isError: true` en el payload de una herramienta, lo que le permite al agente distinguir entre una falla de transporte o de protocolo y una falla lógica en la ejecución de la herramienta misma.

## 3.8 ¿Puede un servidor avisar que una invocación es peligrosa? Annotations declarativas vs. elicitation en tiempo real

MCP ofrece dos mecanismos distintos para señalar riesgo, en dos momentos distintos del ciclo de vida de una llamada, con niveles de garantía muy diferentes entre sí.

### Antes de invocar: estático y declarativo

Cada tool puede traer un objeto `annotations` en la respuesta de `tools/list` (verificado contra `mcp.types.ToolAnnotations` en el SDK oficial, `mcp==2.2.0`) con cuatro campos:

- `readOnlyHint`: la tool no modifica el entorno.
- `destructiveHint`: puede realizar cambios destructivos; solo tiene sentido si `readOnlyHint` es falso.
- `idempotentHint`: invocarla repetidamente con los mismos argumentos no tiene efecto adicional.
- `openWorldHint`: interactúa con un dominio abierto de entidades externas, como una búsqueda web, en vez de uno cerrado.

La especificación es explícita sobre el límite de esto: son *hints*, no garantías, autodeclarados por el propio servidor, y advierte textualmente que los clientes nunca deberían tomar decisiones de uso de una tool basándose en annotations recibidas de un servidor no confiable (Model Context Protocol Specification, 2026). Un servidor puede declarar `destructiveHint: false` en una tool que en los hechos borra datos, y el protocolo no tiene forma de verificarlo.

### Durante la invocación: en tiempo de ejecución

Acá el mecanismo con garantías reales es el patrón MRTR descrito en §3.3 y §3.5: el servidor puede empezar a procesar una llamada y, en lugar de completarla directamente, devolver un `InputRequiredResult` pidiendo confirmación humana antes de seguir (el ejemplo de `delete_production_table` de §3.3). A diferencia de las annotations, esto sí es parte del protocolo en un sentido operativo: la llamada no termina hasta que alguien resuelve la elicitation.

No se identificó, revisando el SDK oficial, un tercer mecanismo de «advertencia» genérico (una notificación de riesgo que el servidor pueda emitir sin pausar la ejecución, por fuera de annotations y elicitation). No existe en la versión de la especificación cubierta por este reporte.

### La consecuencia práctica

El protocolo provee la herramienta para preguntar (elicitation) y para etiquetar (annotations), pero ninguna garantía de que un servidor hostil o mal implementado las use de buena fe. La garantía efectiva de «esto es peligroso, frenar» termina viviendo, en despliegues de producción, en la capa externa al protocolo (un Gateway con OPA evaluando la llamada antes de que llegue al servidor, o Model Armor inspeccionando el resultado, secciones 5.5 y 5.6, Parte 9), no en la buena voluntad del servidor de avisar.

---

**Anterior:** [Parte 4: MRTR y la extensión Tasks](/posts/2026/reporte-mcp-2026-parte-4-mrtr-y-la-extension-tasks/) · **Siguiente:** [Parte 6: descubrimiento dinámico en la práctica](/posts/2026/reporte-mcp-2026-parte-6-descubrimiento-dinamico-en-la-practica/)
